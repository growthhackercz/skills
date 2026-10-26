"""atomic_state.py — zámek a atomický zápis skupiny souborů.

Řeší audit:
  P1-10  souběžné Strategist crony mění stejný stav bez zámku
  P1-13  scorecard se zapisuje jako tři samostatné soubory bez commitu,
         takže pád zanechá jen část

Zásady:
  1. Jeden zámek na logický stav, držený po celou dobu čtení i zápisu.
  2. Skupina souborů se zapíše do temp, zvaliduje a přejmenuje — buď všechno,
     nebo nic. Přejmenování v rámci jednoho svazku je atomické.
  3. Stejné `callId` podruhé neudělá `-2`, ale řízenou no-op nebo revizi.

Tento soubor je runtime-local součást skillu; upravuj jej společně s jeho callery a testy.
"""

import ctypes
import fcntl
import json
import os
import shutil
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path

SCHEMA_VERSION = "1.0"
AT_FDCWD = -100
RENAME_EXCHANGE = 2


def _fsync_dir(path):
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _exchange_dirs(left, right):
    """Atomically exchange two existing directories or fail before mutation."""
    libc = ctypes.CDLL(None, use_errno=True)
    renameat2 = getattr(libc, "renameat2", None)
    if renameat2 is None:
        raise OSError("atomická revize adresáře není na tomto systému dostupná")
    renameat2.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
    renameat2.restype = ctypes.c_int
    if renameat2(AT_FDCWD, os.fsencode(left), AT_FDCWD, os.fsencode(right), RENAME_EXCHANGE) != 0:
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error), str(left), str(right))

# Poznámka: dřív tu byla konstanta STALE_LOCK_SECONDS, podle které se
# „osiřelý" soubor zámku mazal. Byla to chyba (viz komentář v `locked`) —
# mazání zámku ho ruší, ne uklízí. Osiřelost řeší jádro samo.


@contextmanager
def locked(path, timeout=60):
    """Výhradní zámek nad logickým stavem.

    `path` je cesta ke stavu (soubor nebo složka); zámek vzniká jako
    `<path>.lock`. Drží se po celou dobu bloku, takže dva souběžné crony
    se nemohou dohodnout, že ani jeden ještě nezapsal.
    """
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    # Skrytý název: složku scorecardů čte Analytik a stray soubor by ho mohl
    # zmást. Tečka na začátku ho drží mimo běžné globy.
    lockfile = p.with_name("." + p.name + ".lock")

    # Soubor zámku se NIKDY nemaže.
    #
    # Dřív se mazal, když byl starší než STALE_LOCK_SECONDS. To zámek rozbíjelo:
    # `flock` drží zámek na inode, ne na jménu. Když běh legitimně trval déle
    # než 15 minut (velké CRM), jiný proces mu soubor odmazal, vyrobil si nový
    # a dostal na něm vlastní zámek. Oba pak běžely současně a přesně tomu měl
    # zámek zabránit.
    #
    # Osiřelý zámek žádný úklid nepotřebuje: když proces spadne, jádro
    # deskriptor zavře a `flock` uvolní samo. Zbylý prázdný soubor nevadí.
    fh = open(lockfile, "a+")
    deadline = time.time() + timeout
    while True:
        try:
            fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            break
        except BlockingIOError:
            if time.time() > deadline:
                fh.close()
                raise TimeoutError(
                    f"zámek {lockfile} drží jiný běh déle než {timeout} s — "
                    "pravděpodobně běží další cron; tento běh se ukončuje bez zápisu")
            time.sleep(0.25)
    try:
        fh.seek(0)
        fh.truncate()
        fh.write(f"{os.getpid()} {time.strftime('%Y-%m-%dT%H:%M:%S%z')}\n")
        fh.flush()
        yield
    finally:
        fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
        fh.close()


def write_bundle(out_dir, files, manifest=None, validate=None, overwrite=False):
    """Zapíše skupinu souborů atomicky — buď všechny, nebo žádný.

    `files`   {relativní_jméno: obsah(str|bytes)}
    `manifest` volitelný dict → zapíše se jako `_manifest.json`
    `validate` volitelná funkce(dict_cest) → vyhodí výjimku při nevalidním obsahu
    `overwrite` False = existující bundle se NEPŘEPÍŠE (idempotence)

    Vrací (zapsáno: bool, důvod: str|None).
    """
    out = Path(out_dir)
    out.parent.mkdir(parents=True, exist_ok=True)

    if out.exists() and not overwrite:
        return False, "bundle už existuje (idempotence) — beze změny"

    staging_root = out.parent.parent / f".{out.parent.name}-bundle-staging"
    staging_root.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix=f".{out.name}-", dir=str(staging_root)))
    try:
        written = {}
        for rel, content in files.items():
            target = tmp / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            if isinstance(content, bytes):
                target.write_bytes(content)
            else:
                target.write_text(str(content), encoding="utf-8")
            written[rel] = target

        if manifest is not None:
            m = dict(manifest)
            m.setdefault("schemaVersion", SCHEMA_VERSION)
            m.setdefault("writtenAt", time.strftime("%Y-%m-%dT%H:%M:%S%z"))
            m["files"] = sorted(files.keys())
            (tmp / "_manifest.json").write_text(
                json.dumps(m, ensure_ascii=False, indent=2), encoding="utf-8")

        # Validace běží nad TEMP obsahem — nevalidní bundle se nikdy nezveřejní.
        if validate is not None:
            validate(written)

        # fsync všech souborů včetně manifestu a staging adresáře.
        for t in (path for path in tmp.rglob("*") if path.is_file()):
            with open(t, "r+b") as f:
                os.fsync(f.fileno())
        _fsync_dir(tmp)

        exchanged = out.exists()
        if exchanged:
            _exchange_dirs(out, tmp)
        else:
            os.replace(tmp, out)
        try:
            _fsync_dir(out.parent)
            _fsync_dir(staging_root)
        except Exception:
            if exchanged and out.exists() and tmp.exists():
                _exchange_dirs(out, tmp)
                _fsync_dir(out.parent)
                _fsync_dir(staging_root)
            raise
        if tmp.exists():
            shutil.rmtree(tmp, ignore_errors=True)
        return True, None
    except Exception:
        shutil.rmtree(tmp, ignore_errors=True)
        raise


def write_json_atomic(path, data):
    """Jeden JSON soubor atomicky (temp → fsync → rename)."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=p.name + ".", dir=str(p.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, p)
    except Exception:
        Path(tmp).unlink(missing_ok=True)
        raise
