"""Local read-only audit probe. No extraction, execution of backup code or API calls."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess
import tarfile
import zipfile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--backup-root', type=Path, required=True)
parser.add_argument('--repo', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
ROOT = args.backup_root
REPO = args.repo
assert subprocess.check_output(['git', '-C', str(REPO), 'remote', 'get-url', 'origin'], text=True).strip().rstrip('/') in ('https://github.com/growthhackercz/skills.git', 'https://github.com/growthhackercz/skills', 'git@github.com:growthhackercz/skills.git'), 'unexpected repository'
BACKUP = ROOT / 'platform/openclaw-disaster-recovery/openclaw-continuity-2026-10-26-v1.tar.gz'
PREFIX = 'openclaw-continuity-2026-10-26-v1/'


def sha_file(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def checked_names(names):
    assert len(names) == len(set(names)), 'duplicate archive entry'
    for name in names:
        path = PurePosixPath(name)
        assert not path.is_absolute() and '..' not in path.parts and '\\' not in name


result = {'scope': 'static-local-backup-not-live-runtime',
          'repo_base_sha': subprocess.check_output(['git', '-C', str(REPO), 'rev-parse', 'HEAD'], text=True).strip()}
with zipfile.ZipFile(ROOT / 'how-to-restore.zip') as restore:
    checked_names(restore.namelist())
    assert restore.testzip() is None, 'restore ZIP CRC failure'
    entry = 'platform/openclaw-disaster-recovery/' + BACKUP.name
    with restore.open(entry) as stream:
        embedded_hash = hashlib.file_digest(stream, 'sha256').hexdigest()
    result['restore_zip'] = {'sha256': sha_file(ROOT / 'how-to-restore.zip'),
                             'regular_entries': sum(not x.is_dir() for x in restore.infolist()),
                             'crc': 'PASS', 'embedded_tar_matches_local': embedded_hash == sha_file(BACKUP)}
    assert result['restore_zip']['embedded_tar_matches_local']

expected = BACKUP.with_name(BACKUP.name + '.sha256').read_text().split()[0]
actual = sha_file(BACKUP)
assert actual == expected, 'TAR checksum mismatch'
with tarfile.open(BACKUP, 'r:gz') as archive:
    members = archive.getmembers()
    checked_names([m.name for m in members])
    assert all(m.isdir() or m.isfile() for m in members), 'non-regular TAR member'
    assert all(m.name == PREFIX.rstrip('/') or m.name.startswith(PREFIX) for m in members)
    manifest = json.load(archive.extractfile(PREFIX + 'MANIFEST.json'))
    listed = {row['path']: row for row in manifest['files']}
    assert len(listed) == len(manifest['files']) == manifest['fileCount']
    files = {m.name[len(PREFIX):]: m for m in members if m.isfile()}
    assert set(files) == set(listed) | {'MANIFEST.json'}, 'manifest coverage mismatch'
    for name, row in listed.items():
        assert files[name].size == row['bytes'], 'manifest size mismatch'
        with archive.extractfile(files[name]) as stream:
            assert hashlib.file_digest(stream, 'sha256').hexdigest() == row['sha256'], 'manifest digest mismatch'
    config = json.load(archive.extractfile(PREFIX + 'config/openclaw.redacted.json'))
    assignments = json.load(archive.extractfile(PREFIX + 'inventory/agent-skill-assignments.json'))
    cc_agents = json.load(archive.extractfile(PREFIX + 'inventory/agents.json'))
    users = json.load(archive.extractfile(PREFIX + 'inventory/user-skills.json'))
    dependencies = json.load(archive.extractfile(PREFIX + 'inventory/dependencies.json'))
    workspaces = sorted({name.split('/')[1] for name in files if name.startswith('workspaces/')})
    defaults = config['agents']['defaults']
    result['continuity_tar'] = {'sha256': actual, 'checksum': 'PASS',
                               'manifest_verified': len(listed), 'regular_files': len(files),
                               'members': len(members), 'nonregular_members': 0,
                               'workspace_count': len(workspaces), 'cc_agent_count': len(cc_agents),
                               'runtime_agent_ids': [a['id'] for a in config['agents']['list']],
                               'user_skills': len(users),
                               'assignment_counts': {row['agent']: len(row['skills']) for row in assignments},
                               'assignment_total': sum(len(row['skills']) for row in assignments)}
    result['runtime_config'] = {'openclaw_version': dependencies['openclawVersion'],
                               'platform': dependencies['platform'],
                               'primary_model': defaults['model']['primary'],
                               'agent_models': {a['id']: a.get('model', {}).get('primary', 'inherit-default') for a in config['agents']['list']},
                               'default_heartbeat': defaults['heartbeat'],
                               'subagents': defaults['subagents'],
                               'memory_search_provider': defaults['memorySearch']['provider'],
                               'memory_wiki_enabled': config['plugins']['entries']['memory-wiki']['enabled'],
                               'compiled_wiki_digest_in_prompt': config['plugins']['entries']['memory-wiki']['config']['context']['includeCompiledDigestPrompt'],
                               'autonomous_skill_workshop': config['skills']['workshop']['autonomous']['enabled'],
                               'workshop_approval_policy': config['skills']['workshop']['approvalPolicy'],
                               'cron_config_keys': sorted(config['cron']),
                               'mcp_server_ids': sorted(config['mcp']['servers']),
                               'cmo_social_publisher_assignments': [s for r in assignments if r['agent'] == 'cmo' for s in r['skills'] if 'cliqsales-social-publisher' in s]}

with zipfile.ZipFile(ROOT / 'cs-skills.zip') as skills:
    names = skills.namelist()
    checked_names(names)
    assert skills.testzip() is None, 'skills ZIP CRC failure'
    base = 'platform/cs-skills/'
    archive_skills = {n[len(base):].split('/')[0] for n in names if n.startswith(base) and n.endswith('/SKILL.md') and n[len(base):].count('/') == 1}
    repo_skills = {p.parent.name for p in REPO.glob('*/SKILL.md')}
    identical, differences = [], {}
    for skill in sorted(archive_skills & repo_skills):
        prefix = base + skill + '/'
        left = {n[len(prefix):]: skills.read(n).replace(b'\r\n', b'\n') for n in names if n.startswith(prefix) and not n.endswith('/')}
        right = {p.relative_to(REPO / skill).as_posix(): p.read_bytes().replace(b'\r\n', b'\n') for p in (REPO / skill).rglob('*') if p.is_file()}
        delta = {'only_archive': sorted(left.keys() - right.keys()), 'only_repo': sorted(right.keys() - left.keys()),
                 'content_changed': sorted(k for k in left.keys() & right.keys() if left[k] != right[k])}
        if any(delta.values()):
            differences[skill] = delta
        else:
            identical.append(skill)
    lib_files = [n for n in names if n.startswith(base + '_lib/') and not n.endswith('/')]
    result['skill_library'] = {'zip_sha256': sha_file(ROOT / 'cs-skills.zip'), 'crc': 'PASS',
                               'archive_skills': len(archive_skills), 'repo_top_level_skills': len(repo_skills),
                               'common': len(archive_skills & repo_skills), 'identical_normalized': len(identical),
                               'only_archive': sorted(archive_skills - repo_skills), 'only_repo_count': len(repo_skills - archive_skills), 'only_repo': sorted(repo_skills - archive_skills),
                               'differences': differences, 'shared_library_files_in_archive': len(lib_files),
                               'repo_shared_library_present': (REPO / '_lib').is_dir()}

out = args.output
out.parent.mkdir(parents=True, exist_ok=True)
assert not out.exists(), 'do not overwrite an existing evidence file'
out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(result, ensure_ascii=False, indent=2))
