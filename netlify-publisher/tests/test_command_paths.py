#!/usr/bin/env python3
"""Command-level regressions for deploy/promote/rollback/ensure/SSR.

The real publisher CLI is executed in a subprocess. A local fake `netlify`
binary supplies deterministic JSON; no network, credentials or live site are
used. These tests intentionally exercise argparse, command dispatch, locks and
state-file writes rather than calling validators in isolation.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "netlify_publish.py"
RESULTS: list[tuple[bool, str]] = []


FAKE_NETLIFY = r'''#!/usr/bin/env python3
import json
import fcntl
import os
import subprocess
import sys
import time
from pathlib import Path

args = sys.argv[1:]
fake_path = Path(__file__)
log = fake_path.with_suffix(".log")
with log.open("a", encoding="utf-8") as handle:
    handle.write(json.dumps(args) + "\n")
try:
    config = json.loads(fake_path.with_suffix(".config.json").read_text(encoding="utf-8"))
except Exception:
    config = {}

mode = config.get("mode", "")
deploy_id = config.get("deploy_id", "draft-1")
site_id = config.get("site_id", "site-a")
registry_path = fake_path.with_suffix(".sites.json")
registry_lock_path = fake_path.with_suffix(".sites.lock")

def read_registry():
    try:
        value = json.loads(registry_path.read_text(encoding="utf-8"))
        return value if isinstance(value, list) else []
    except Exception:
        return []

def data():
    try:
        index = args.index("--data")
        return json.loads(args[index + 1])
    except Exception:
        return {}

if args and args[0] == "sites:list":
    if mode == "ensure-race":
        with registry_lock_path.open("a+") as lock_handle:
            fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX)
            sites = read_registry()
            fcntl.flock(lock_handle.fileno(), fcntl.LOCK_UN)
        # Bez publisher locku rozšíří okno mezi lookup a create tak, aby oba
        # procesy spolehlivě viděly missing a druhý založil fallback.
        if not sites:
            time.sleep(0.2)
        print(json.dumps(sites))
    elif mode == "ensure-existing-missing-id":
        print(json.dumps([{"name": "demo", "url": "https://demo.netlify.app"}]))
    else:
        print("[]")
elif args and args[0] == "sites:create":
    name = args[args.index("--name") + 1] if "--name" in args else "generated"
    if mode == "ensure-race":
        with registry_lock_path.open("a+") as lock_handle:
            fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX)
            sites = read_registry()
            if any(site.get("name") == name for site in sites):
                print("site name already taken", file=sys.stderr)
                sys.exit(1)
            created = {
                "id": f"id-{name}",
                "name": name,
                "url": f"https://{name}.netlify.app",
            }
            sites.append(created)
            registry_path.write_text(json.dumps(sites), encoding="utf-8")
            fcntl.flock(lock_handle.fileno(), fcntl.LOCK_UN)
        print(json.dumps(created))
    elif mode == "ensure-create-missing-id":
        print(json.dumps({"name": name, "url": f"https://{name}.netlify.app"}))
    else:
        print(json.dumps({"id": site_id, "name": name, "url": f"https://{name}.netlify.app"}))
elif args and args[0] == "deploy":
    # Netlify CLI parent potřebuje PAT pro upload. U SSR ale config-file env
    # precedence musí build/plugin child procesu předat prázdnou hodnotu.
    # Fake zaznamená simulovaný child stav, aniž by spouštěl projektový kód.
    if "--dir" not in args:
        # Skutečný child process přes PATH: simuluje Netlify Build auto-install
        # pluginu i local-plugin instalaci s yarn.lock; ani jedna cesta v CLI
        # 26 ještě nepoužívá [build.environment].
        subprocess.run(["npm", "cc-token-probe"], check=True)
        subprocess.run(["yarn", "cc-token-probe"], check=True)
        config_text = (Path.cwd() / "netlify.toml").read_text(encoding="utf-8")
        masked = 'NETLIFY_AUTH_TOKEN = ""' in config_text
        fake_path.with_suffix(".build-env").write_text(
            "EMPTY" if masked else "VISIBLE",
            encoding="utf-8",
        )
    else:
        deploy_root = Path(args[args.index("--dir") + 1])
        files = {}
        directories = {".": oct(deploy_root.stat().st_mode & 0o777)}
        for entry in sorted(deploy_root.rglob("*")):
            relative = entry.relative_to(deploy_root).as_posix()
            if entry.is_dir():
                directories[relative] = oct(entry.stat().st_mode & 0o777)
            elif entry.is_file():
                info = entry.stat()
                files[relative] = {
                    "size": info.st_size,
                    "inode": info.st_ino,
                    "mode": oct(info.st_mode & 0o777),
                }
        fake_path.with_suffix(".deploy-tree.json").write_text(json.dumps({
            "root": str(deploy_root),
            "files": files,
            "directories": directories,
        }), encoding="utf-8")
    state = "building" if mode == "deploy-building" else "ready"
    payload = {
        "state": state,
        "id": deploy_id,
        "deploy_ssl_url": "https://draft--site-a.netlify.app",
    }
    if mode != "deploy-followup":
        payload["site_id"] = site_id
    print(json.dumps(payload))
elif args[:2] == ["api", "getSite"]:
    target = config.get("published_deploy_id", deploy_id)
    print(json.dumps({
        "id": site_id,
        "name": "site-a",
        "ssl_url": "https://site-a.netlify.app",
        "published_deploy": {"id": target},
    }))
elif args[:2] == ["api", "listSiteDeploys"]:
    print(json.dumps([{
        "id": deploy_id,
        "site_id": site_id,
        "state": "ready",
        "context": "deploy-preview",
        "published_at": None,
        "deploy_ssl_url": "https://draft--site-a.netlify.app",
    }]))
elif args[:2] == ["api", "restoreSiteDeploy"]:
    requested = data().get("deploy_id", deploy_id)
    state = "ready" if mode == "restore-ready" else "current"
    print(json.dumps({
        "id": requested,
        "site_id": site_id,
        "state": state,
        "ssl_url": "https://site-a.netlify.app",
    }))
else:
    print(json.dumps({"error": "unsupported fake command", "args": args}))
    sys.exit(2)
'''


def record(condition: bool, description: str) -> None:
    RESULTS.append((bool(condition), description))


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def static_project(documents: Path, slug: str) -> Path:
    project = documents / "sites" / slug
    project.mkdir(parents=True)
    (project / "index.html").write_text("<!doctype html>", encoding="utf-8")
    return project


def ssr_project(documents: Path, slug: str) -> Path:
    project = documents / "sites" / slug
    (project / ".next").mkdir(parents=True)
    write_json(
        project / "package.json",
        {
            "name": slug,
            "version": "1.0.0",
            "scripts": {"build": "next build"},
            "dependencies": {"next": "15.0.0", "react": "19.0.0"},
        },
    )
    return project


def svelte_ssr_project(documents: Path, slug: str) -> Path:
    project = documents / "sites" / slug
    (project / "build").mkdir(parents=True)
    write_json(
        project / "package.json",
        {
            "name": slug,
            "version": "1.0.0",
            "scripts": {"build": "vite build"},
            "dependencies": {"@sveltejs/kit": "2.0.0"},
        },
    )
    return project


def invoke(
    env: dict[str, str],
    *args: str,
    mode: str = "",
    deploy_id: str = "draft-1",
) -> tuple[subprocess.CompletedProcess[str], dict]:
    command_env = dict(env)
    fake = Path(command_env["NETLIFY_CLI"])
    fake.with_suffix(".config.json").write_text(
        json.dumps({"mode": mode, "deploy_id": deploy_id, "site_id": "site-a"}),
        encoding="utf-8",
    )
    completed = subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        env=command_env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
        check=False,
    )
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError:
        payload = {}
    return completed, payload


def log_commands(path: Path) -> list[list[str]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def reset_log(path: Path) -> None:
    path.unlink(missing_ok=True)


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        documents = root / "documents"
        documents.mkdir()
        fake = root / "netlify-fake"
        fake.write_text(FAKE_NETLIFY, encoding="utf-8")
        fake.chmod(0o755)
        fake_bin = root / "fake-bin"
        fake_bin.mkdir()
        fake_npm = fake_bin / "npm"
        fake_npm.write_text(
            "#!/usr/bin/env python3\n"
            "import os\n"
            "from pathlib import Path\n"
            "Path(__file__).with_suffix('.child-env').write_text("
            "'VISIBLE' if os.environ.get('NETLIFY_AUTH_TOKEN') else 'EMPTY', encoding='utf-8')\n",
            encoding="utf-8",
        )
        fake_npm.chmod(0o755)
        fake_yarn = fake_bin / "yarn"
        fake_yarn.write_text(
            "#!/usr/bin/env python3\n"
            "import os\n"
            "from pathlib import Path\n"
            "Path(__file__).with_suffix('.child-env').write_text("
            "'VISIBLE' if os.environ.get('NETLIFY_AUTH_TOKEN') else 'EMPTY', encoding='utf-8')\n",
            encoding="utf-8",
        )
        fake_yarn.chmod(0o755)
        log = fake.with_suffix(".log")
        env = {
            **os.environ,
            "PATH": f"{fake_bin}{os.pathsep}{os.environ.get('PATH', '')}",
            "DOCUMENTS_PATH": str(documents),
            "NETLIFY_CLI": str(fake),
            "NETLIFY_AUTH_TOKEN": "local-test-token",
            "NETLIFY_PUBLISH_SKIP_URL_CHECK": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
        }

        # ensure-site: lookup may be automatic, creation never is.
        completed, payload = invoke(env, "ensure-site", "--slug", "demo", "--json")
        commands = log_commands(log)
        record(completed.returncode == 65 and "--confirm-create" in payload.get("error", ""),
               "ensure-site create branch fails without --confirm-create")
        record(not any(command and command[0] == "sites:create" for command in commands),
               "ensure-site without confirmation never calls sites:create")

        reset_log(log)
        completed, payload = invoke(
            env, "ensure-site", "--slug", "demo", "--dry-run", "--json"
        )
        commands = log_commands(log)
        record(completed.returncode == 0 and payload.get("wouldCreate") is True,
               "ensure-site --dry-run returns a create plan")
        record(not any(command and command[0] == "sites:create" for command in commands),
               "ensure-site --dry-run performs no create")

        reset_log(log)
        completed, payload = invoke(
            env, "ensure-site", "--slug", "demo", "--confirm-create", "--json"
        )
        record(completed.returncode == 0 and payload.get("siteId") == "site-a",
               "ensure-site confirmed create returns exact site ID")
        record(
            payload.get("skillVersion") == "1.3.4" and payload.get("artifactVersion") == 1,
            "every persisted CLI JSON result carries the release artifact contract",
        )

        completed, payload = invoke(
            env,
            "ensure-site", "--slug", "demo", "--confirm-create", "--json",
            mode="ensure-create-missing-id",
        )
        record(completed.returncode == 65 and "site ID" in payload.get("error", ""),
               "ensure-site refuses create success without site ID")

        completed, payload = invoke(
            env, "ensure-site", "--slug", "demo", "--json",
            mode="ensure-existing-missing-id",
        )
        record(completed.returncode == 65 and "site ID" in payload.get("error", ""),
               "ensure-site refuses existing-site success without site ID")

        completed, payload = invoke(
            env,
            "create-site", "--name", "demo", "--confirm-create", "--json",
            mode="ensure-create-missing-id",
        )
        record(completed.returncode == 65 and "site ID" in payload.get("error", ""),
               "create-site command refuses remote success without site ID")

        # Dva potvrzené chat runy stejného slugu musí skončit u jediného site,
        # ne u primary + fallback názvu. Test používá dva skutečné procesy.
        fake.with_suffix(".sites.json").unlink(missing_ok=True)
        fake.with_suffix(".sites.lock").unlink(missing_ok=True)
        fake.with_suffix(".config.json").write_text(
            json.dumps({"mode": "ensure-race", "site_id": "site-a"}),
            encoding="utf-8",
        )
        race_command = [
            sys.executable,
            str(SCRIPT),
            "ensure-site",
            "--slug",
            "race-project",
            "--confirm-create",
            "--json",
        ]
        first = subprocess.Popen(
            race_command, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        second = subprocess.Popen(
            race_command, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        first_out, first_err = first.communicate(timeout=30)
        second_out, second_err = second.communicate(timeout=30)
        race_payloads = []
        for raw in (first_out, second_out):
            try:
                race_payloads.append(json.loads(raw))
            except json.JSONDecodeError:
                race_payloads.append({})
        registry = read_json(fake.with_suffix(".sites.json"))
        record(
            first.returncode == 0 and second.returncode == 0,
            "concurrent ensure-site calls both finish successfully",
        )
        record(
            [site.get("name") for site in registry] == ["race-project"],
            "concurrent ensure-site creates exactly one deterministic site",
        )
        record(
            sorted(payload.get("created") for payload in race_payloads) == [False, True]
            and all(payload.get("siteId") == "id-race-project" for payload in race_payloads),
            "second ensure-site reuses the first run's exact site ID",
        )

        # Direct deploy: ready + exact binding/follow-up before local write.
        deploy_project = static_project(documents, "deploy-ok")
        assets = deploy_project / "assets"
        assets.mkdir()
        asset = assets / "app.js"
        asset.write_text("console.log('safe')", encoding="utf-8")
        origin_asset_inode = asset.stat().st_ino
        write_json(deploy_project / ".web-builder.json", {"internal": True})
        write_json(deploy_project / ".netlify-state.json", {
            "siteId": "site-a",
            "stateVersion": 2,
            "skillVersion": "1.3.4",
        })
        reset_log(log)
        completed, payload = invoke(
            env,
            "deploy", str(deploy_project), "--site-id", "site-a", "--draft", "--json",
            mode="deploy-followup",
            deploy_id="direct-1",
        )
        state = read_json(deploy_project / ".netlify-state.json")
        record(completed.returncode == 0 and payload.get("deployId") == "direct-1",
               "deploy command accepts ready result after authoritative site-scoped follow-up")
        record(
            state.get("siteId") == "site-a"
            and state.get("draftDeployId") == "direct-1"
            and state.get("skillVersion") == "1.3.4"
            and state.get("stateVersion") == 2,
            "deploy writes the validated pair and release state contract",
        )
        first_static_deploy = next(
            command for command in log_commands(log)
            if command and command[0] == "deploy" and "--dir" in command
        )
        record("--no-build" in first_static_deploy and "--context" not in first_static_deploy,
               "prebuilt static upload uses the valid Netlify 26 --no-build argument set")
        observed_tree = read_json(fake.with_suffix(".deploy-tree.json"))
        observed_files = observed_tree.get("files", {})
        staged_root = Path(observed_tree.get("root", "/missing"))
        record(
            set(observed_files) == {"index.html", "assets/app.js"},
            "static CLI receives only the verified public manifest, never CC metadata",
        )
        record(
            payload.get("scan", {}).get("isFinalPublicManifest") is True
            and payload.get("scan", {}).get("isFinalDeployManifest") is True,
            "function-free static summary identifies its exact final manifest",
        )
        record(
            Path(first_static_deploy[first_static_deploy.index("--dir") + 1]) != deploy_project,
            "static deploy passes a private staging tree instead of the project root",
        )
        record(
            observed_files.get("assets/app.js", {}).get("inode") != origin_asset_inode,
            "static staging copies bytes to a new inode instead of hard-linking source files",
        )
        record(
            all(item.get("mode") == "0o600" for item in observed_files.values())
            and all(mode == "0o700" for mode in observed_tree.get("directories", {}).values()),
            "static staging is private (directories 0700, files 0600)",
        )
        record(not staged_root.exists(), "static staging is removed after a successful deploy")

        # A state file written by the first deploy must remain private on every
        # later deploy too; exclusion cannot be a first-run-only property.
        completed, payload = invoke(
            env,
            "deploy", str(deploy_project), "--site-id", "site-a", "--draft", "--json",
            deploy_id="direct-2",
        )
        second_tree = read_json(fake.with_suffix(".deploy-tree.json"))
        record(
            completed.returncode == 0
            and set(second_tree.get("files", {})) == {"index.html", "assets/app.js"},
            "second static deploy still excludes generated state and Web Builder metadata",
        )

        function_project = static_project(documents, "deploy-functions")
        function_dir = function_project / "netlify" / "functions"
        function_dir.mkdir(parents=True)
        (function_dir / "api.mjs").write_text(
            "export default async () => new Response('ok')", encoding="utf-8"
        )
        reset_log(log)
        completed, function_payload = invoke(
            env,
            "deploy", str(function_project), "--site-id", "site-a", "--draft", "--json",
            deploy_id="function-1",
        )
        function_command = next(
            command for command in log_commands(log)
            if command and command[0] == "deploy" and "--functions" in command
        )
        record(
            completed.returncode == 0
            and function_payload.get("scan", {}).get("isFinalPublicManifest") is True
            and function_payload.get("scan", {}).get("isFinalDeployManifest") is False
            and function_payload.get("scan", {}).get("functionFiles") == 1,
            "static functions are reported as source preflight, not a final server bundle",
        )
        record(
            function_command[function_command.index("--functions") + 1] == str(function_dir),
            "Netlify receives the validated project-bound functions directory separately",
        )

        bad_deploy = static_project(documents, "deploy-bad")
        original_state = {"siteId": "site-a", "marker": "unchanged", "stateVersion": 2}
        write_json(bad_deploy / ".netlify-state.json", original_state)
        completed, payload = invoke(
            env,
            "deploy", str(bad_deploy), "--site-id", "site-a", "--draft", "--json",
            mode="deploy-building",
            deploy_id="bad-1",
        )
        record(completed.returncode == 65 and "ready" in payload.get("error", ""),
               "deploy command rejects non-terminal direct state")
        record(read_json(bad_deploy / ".netlify-state.json") == original_state,
               "failed direct validation happens before local state write")

        direct_prod = static_project(documents, "direct-prod")
        write_json(direct_prod / ".netlify-state.json", {
            "siteId": "site-a",
            "promotedDeployId": "stale-promote",
            "rolledBackDeployId": "stale-rollback",
        })
        completed, payload = invoke(
            env,
            "deploy", str(direct_prod), "--site-id", "site-a",
            "--confirm-publish", "yes", "--json",
            deploy_id="production-1",
        )
        state = read_json(direct_prod / ".netlify-state.json")
        record(completed.returncode == 0 and state.get("prodDeployId") == "production-1",
               "direct production deploy persists the exact validated deploy")
        record(state.get("promotedDeployId") is None and state.get("rolledBackDeployId") is None,
               "direct production deploy clears stale operation checkpoint IDs")

        # Promote: exact approved draft and restore state `current`.
        promote_project = static_project(documents, "promote-ok")
        write_json(promote_project / ".netlify-state.json", {
            "siteId": "site-a",
            "draftDeployId": "draft-1",
            "draftUrl": "https://draft--site-a.netlify.app",
            "rolledBackDeployId": "stale-rollback",
        })
        completed, payload = invoke(
            env,
            "promote", "--site-id", "site-a", "--path", str(promote_project),
            "--deploy-id", "draft-1", "--confirm-publish", "yes", "--json",
            deploy_id="draft-1",
        )
        state = read_json(promote_project / ".netlify-state.json")
        record(completed.returncode == 0 and payload.get("state") == "current",
               "promote command validates restore state current")
        record(state.get("draftDeployId") is None and state.get("prodDeployId") == "draft-1",
               "promote updates local state only after validated restore")
        record(state.get("rolledBackDeployId") is None,
               "promote clears a stale rollback checkpoint ID")

        promote_bad = static_project(documents, "promote-bad")
        pending = {
            "siteId": "site-a",
            "draftDeployId": "draft-2",
            "draftUrl": "https://draft--site-a.netlify.app",
            "stateVersion": 2,
        }
        write_json(promote_bad / ".netlify-state.json", pending)
        completed, payload = invoke(
            env,
            "promote", "--site-id", "site-a", "--path", str(promote_bad),
            "--deploy-id", "draft-2", "--confirm-publish", "yes", "--json",
            mode="restore-ready",
            deploy_id="draft-2",
        )
        record(completed.returncode == 65 and "current" in payload.get("error", ""),
               "promote command rejects deploy-style ready restore response")
        record(read_json(promote_bad / ".netlify-state.json") == pending,
               "failed promote restore leaves pending state intact")

        # Rollback: path binding, project+site lock and state update.
        rollback_project = static_project(documents, "rollback-ok")
        write_json(rollback_project / ".netlify-state.json", {"siteId": "site-a"})
        completed, payload = invoke(
            env,
            "rollback", "--site-id", "site-a", "--path", str(rollback_project),
            "--deploy-id", "previous-1", "--confirm-publish", "yes", "--json",
            deploy_id="previous-1",
        )
        state = read_json(rollback_project / ".netlify-state.json")
        site_locks = list((documents / "platform" / "netlify-publisher" / ".site-locks").glob("*.lock"))
        record(completed.returncode == 0 and payload.get("state") == "current",
               "rollback command validates restore state current")
        record(state.get("rolledBackDeployId") == "previous-1" and state.get("prodDeployId") == "previous-1",
               "rollback writes project-bound production state")
        record(bool(site_locks), "rollback uses a persistent per-site lock file")

        rollback_bad = static_project(documents, "rollback-bad")
        write_json(rollback_bad / ".netlify-state.json", {"siteId": "other-site"})
        reset_log(log)
        completed, payload = invoke(
            env,
            "rollback", "--site-id", "site-a", "--path", str(rollback_bad),
            "--deploy-id", "previous-2", "--confirm-publish", "yes", "--json",
            deploy_id="previous-2",
        )
        commands = log_commands(log)
        record(completed.returncode == 65 and "other-site" in payload.get("error", ""),
               "rollback rejects a project bound to another site")
        record(not any(command[:2] == ["api", "restoreSiteDeploy"] for command in commands),
               "rollback binding failure occurs before remote restore")

        rollback_restore_bad = static_project(documents, "rollback-restore-bad")
        rollback_pending = {"siteId": "site-a", "marker": "unchanged", "stateVersion": 2}
        write_json(rollback_restore_bad / ".netlify-state.json", rollback_pending)
        completed, payload = invoke(
            env,
            "rollback", "--site-id", "site-a", "--path", str(rollback_restore_bad),
            "--deploy-id", "previous-3", "--confirm-publish", "yes", "--json",
            mode="restore-ready",
            deploy_id="previous-3",
        )
        record(completed.returncode == 65 and "current" in payload.get("error", ""),
               "rollback command rejects deploy-style ready restore response")
        record(read_json(rollback_restore_bad / ".netlify-state.json") == rollback_pending,
               "failed rollback restore leaves local state unchanged")

        # SSR: scan wording is truthful and every nested/dangling symlink fails
        # before generated config or remote deploy writes.
        ssr = ssr_project(documents, "ssr-ok")
        completed, payload = invoke(
            env,
            "deploy", str(ssr), "--site-id", "site-a", "--draft", "--json",
            deploy_id="ssr-1",
        )
        commands = log_commands(log)
        scan = payload.get("scan", {})
        record(completed.returncode == 0 and payload.get("deployMode") == "ssr-build-token-masked",
               "SSR command keeps Netlify framework build and deploy in one process")
        record(
            scan.get("scope") == "ssr-project-and-build-output-preflight"
            and scan.get("isFinalDeployManifest") is False,
            "SSR output labels source/build preflight as non-final manifest",
        )
        record(any(command and command[0] == "deploy" and "--dir" not in command for command in commands),
               "SSR command does not masquerade as static --dir upload")
        ssr_deploy = next(
            command for command in reversed(commands)
            if command and command[0] == "deploy" and "--dir" not in command
        )
        record("--no-build" not in ssr_deploy and "--config" not in ssr_deploy,
               "SSR uses supported Netlify 26 build-mode arguments")
        record(
            "--context" in ssr_deploy
            and ssr_deploy[ssr_deploy.index("--context") + 1] == "deploy-preview",
            "SSR draft declares the deploy-preview context",
        )
        record(fake.with_suffix(".build-env").read_text(encoding="utf-8") == "EMPTY",
               "SSR framework build and plugin children receive a blank Netlify auth token")
        record(fake_npm.with_suffix(".child-env").read_text(encoding="utf-8") == "EMPTY",
               "Netlify's pre-build npm plugin auto-install receives no deploy token")
        record(fake_yarn.with_suffix(".child-env").read_text(encoding="utf-8") == "EMPTY",
               "Netlify's pre-build yarn local-plugin install receives no deploy token")
        generated_config = (ssr / "netlify.toml").read_text(encoding="utf-8")
        record(
            "[build.environment]" in generated_config
            and 'NETLIFY_AUTH_TOKEN = ""' in generated_config,
            "generated SSR config contains the credential mask",
        )

        ssr_bad = ssr_project(documents, "ssr-symlink")
        nested = ssr_bad / ".next" / "server" / "nested"
        nested.mkdir(parents=True)
        (nested / "dangling").symlink_to(ssr_bad / "missing", target_is_directory=True)
        reset_log(log)
        completed, payload = invoke(
            env,
            "deploy", str(ssr_bad), "--site-id", "site-a", "--draft", "--json",
            deploy_id="ssr-bad",
        )
        record(completed.returncode == 65 and "Symlinky" in payload.get("error", ""),
               "SSR command rejects a nested dangling symlink")
        record(not (ssr_bad / "netlify.toml").exists(),
               "SSR symlink failure happens before local netlify.toml write")
        record(not log_commands(log), "SSR symlink failure happens before Netlify CLI invocation")

        # Existing SSR config is accepted only with the exact base mask and no
        # non-empty context override. All failures happen before CLI execution.
        ssr_unmasked = ssr_project(documents, "ssr-unmasked")
        (ssr_unmasked / "netlify.toml").write_text(
            '[build]\ncommand = "npm run build"\npublish = ".next"\n',
            encoding="utf-8",
        )
        reset_log(log)
        completed, payload = invoke(
            env, "deploy", str(ssr_unmasked), "--site-id", "site-a", "--draft", "--json",
            deploy_id="ssr-unmasked",
        )
        record(
            completed.returncode == 65
            and "build.environment" in payload.get("error", "")
            and "credential" in payload.get("error", ""),
            "existing SSR config without a blank auth mask fails closed",
        )
        record(not log_commands(log), "missing SSR mask fails before Netlify CLI invocation")

        ssr_override = ssr_project(documents, "ssr-context-override")
        (ssr_override / "netlify.toml").write_text(
            '[build]\ncommand = "npm run build"\npublish = ".next"\n\n'
            '[build.environment]\nNETLIFY_AUTH_TOKEN = ""\n\n'
            '[context.production.environment]\nNETLIFY_AUTH_TOKEN = "secret-again"\n',
            encoding="utf-8",
        )
        reset_log(log)
        completed, payload = invoke(
            env, "deploy", str(ssr_override), "--site-id", "site-a", "--draft", "--json",
            deploy_id="ssr-override",
        )
        record(
            completed.returncode == 65 and "neprázdnou" in payload.get("error", ""),
            "non-empty SSR context override cannot reintroduce the credential",
        )
        record(not log_commands(log), "context override fails before Netlify CLI invocation")

        ssr_masked = ssr_project(documents, "ssr-existing-mask")
        (ssr_masked / "netlify.toml").write_text(
            '[build]\ncommand = "npm run build"\npublish = ".next"\n\n'
            '[build.environment]\nNETLIFY_AUTH_TOKEN = ""\n',
            encoding="utf-8",
        )
        reset_log(log)
        completed, payload = invoke(
            env, "deploy", str(ssr_masked), "--site-id", "site-a", "--draft", "--json",
            deploy_id="ssr-existing-mask",
        )
        record(
            completed.returncode == 0
            and payload.get("netlifyConfig", {}).get("created") is False,
            "existing SSR config with the exact blank mask remains usable",
        )

        # Jiné SSR frameworky ani ruční force nesmí spadnout do token-bearing
        # build mode bez stejně ověřeného config/output kontraktu.
        svelte = svelte_ssr_project(documents, "svelte-unsupported")
        reset_log(log)
        completed, payload = invoke(
            env, "deploy", str(svelte), "--site-id", "site-a", "--draft", "--json",
            deploy_id="svelte-must-not-run",
        )
        record(
            completed.returncode == 65
            and "není bezpečně podporovaný" in payload.get("error", ""),
            "unverified SvelteKit SSR fails closed",
        )
        record(not log_commands(log), "unsupported SSR calls no token-bearing Netlify CLI")

        forced_static = static_project(documents, "forced-static-ssr")
        reset_log(log)
        completed, payload = invoke(
            env, "deploy", str(forced_static), "--site-id", "site-a", "--ssr", "--json",
            deploy_id="forced-must-not-run",
        )
        record(
            completed.returncode == 65 and "nesmí přepsat" in payload.get("error", ""),
            "--ssr cannot override a statically detected framework",
        )
        record(not log_commands(log), "forced static SSR calls no Netlify CLI")

        # Project path means the exact project root, not an arbitrary subtree.
        nested_project = static_project(documents, "exact-root")
        nested = nested_project / "subdir"
        nested.mkdir()
        (nested / "index.html").write_text("<!doctype html>", encoding="utf-8")
        completed, payload = invoke(
            env, "deploy", str(nested), "--site-id", "site-a", "--dry-run", "--json"
        )
        record(completed.returncode == 65 and "přesně" in payload.get("error", ""),
               "publisher rejects a nested directory disguised as a project root")

        # Lock directory creation must not follow a pre-existing platform symlink.
        evil_documents = root / "evil-documents"
        outside = root / "outside-lock-target"
        evil_documents.mkdir()
        outside.mkdir()
        evil_project = static_project(evil_documents, "lock-symlink")
        (evil_documents / "platform").symlink_to(outside, target_is_directory=True)
        evil_env = {**env, "DOCUMENTS_PATH": str(evil_documents)}
        reset_log(log)
        completed, payload = invoke(
            evil_env,
            "deploy", str(evil_project), "--site-id", "site-a", "--draft", "--json",
            deploy_id="must-not-run",
        )
        record(completed.returncode == 65 and "symlink" in payload.get("error", "").lower(),
               "lock path rejects a pre-existing platform symlink")
        record(not (outside / "netlify-publisher").exists() and not log_commands(log),
               "rejected lock path writes nothing outside DOCUMENTS_PATH and calls no CLI")

        # Build dry-run validates malformed install metadata through main().
        malformed = documents / "sites" / "malformed-install"
        malformed.mkdir(parents=True)
        write_json(malformed / "package.json", {
            "name": "malformed-install",
            "scripts": {"build": "vite build"},
            "devDependencies": {"vite": "7.0.0"},
            "cliqsales": "not-an-object",
        })
        completed, payload = invoke(
            env, "build", str(malformed), "--dry-run", "--json"
        )
        record(completed.returncode == 65 and "JSON objekt" in payload.get("error", ""),
               "build --dry-run gracefully validates malformed install metadata")

        reset_log(log)
        malformed_sections = documents / "sites" / "malformed-package-sections"
        malformed_sections.mkdir(parents=True)
        write_json(malformed_sections / "package.json", {
            "name": "malformed-package-sections",
            "dependencies": None,
            "scripts": {"build": "vite build"},
        })
        completed, payload = invoke(
            env, "build", str(malformed_sections), "--dry-run", "--json"
        )
        record(
            completed.returncode == 65
            and "dependencies musí být JSON objekt" in payload.get("error", "")
            and "Traceback" not in completed.stderr
            and not log_commands(log),
            "malformed package sections return structured CLI error without traceback or side effect",
        )

    for success, description in RESULTS:
        print(f"{'PASS' if success else 'FAIL'}  {description}")
    failed = sum(1 for success, _ in RESULTS if not success)
    print(f"\n{len(RESULTS) - failed}/{len(RESULTS)} prošlo")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
