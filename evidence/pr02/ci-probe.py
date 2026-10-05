import os
import shutil
import yaml
import subprocess
from pathlib import Path

def run(args, **kwargs):
    subprocess.run(args, check=True, **kwargs)

workflow = yaml.safe_load(Path('/source/.gitverse/workflows/pr02.yml').read_text())['jobs']['practice']
print('BEFORE BOOTSTRAP: expected absence of Node in the pinned ROS image', flush=True)
missing = subprocess.run(['bash', '-c', 'node --version'])
assert missing.returncode == 127
print('PASS: reproduced missing node, exit 127', flush=True)
run(['bash', '--noprofile', '--norc', '-eo', 'pipefail', '-c', workflow['steps'][0]['run']])
workspace = Path('/tmp/checkout-workspace')
workspace.mkdir()
runtime = Path('/tmp/checkout-runtime')
runtime.mkdir()
run(['git', 'config', '--global', 'url.file:///source/.git.insteadOf', 'https://gitverse.ru/virusapex/ros2-student'])
run(['git', 'config', '--global', 'safe.directory', '/source'])
run(['git', 'config', '--global', 'protocol.file.allow', 'always'])
sha = subprocess.check_output(['git', '-C', '/source', 'rev-parse', 'HEAD'], text=True).strip()
env = dict(os.environ, GITHUB_WORKSPACE=str(workspace), RUNNER_TEMP=str(runtime),
           GITHUB_REPOSITORY='virusapex/ros2-student', GITHUB_REF='refs/heads/pr02',
           GITHUB_SHA=sha, GITHUB_SERVER_URL='https://gitverse.ru',
           GITHUB_STATE=str(runtime/'state'), GITHUB_OUTPUT=str(runtime/'output'),
           INPUT_TOKEN='local-ci-placeholder-not-a-secret')
env['INPUT_FETCH-DEPTH'] = '0'
env['INPUT_PERSIST-CREDENTIALS'] = 'true'
(runtime/'state').touch()
(runtime/'output').touch()
print('CHECKOUT MAIN: actual GitVerse actions/checkout@v4 dist/index.js, local Git transport', flush=True)
run(['node', '/action/dist/index.js'], env=env)
assert subprocess.check_output(['git', '-C', str(workspace), 'rev-parse', 'HEAD'], text=True).strip() == sha
assert subprocess.check_output(['git', '-C', str(workspace), 'rev-parse', '--is-shallow-repository'], text=True).strip() == 'false'
key = 'http.https://gitverse.ru/.extraheader'
assert subprocess.run(['git', '-C', str(workspace), 'config', '--local', '--get', key], stdout=subprocess.DEVNULL).returncode == 0
print('PASS: checkout HEAD matches source, full history, test auth header configured', flush=True)
print('CANDIDATE EVIDENCE: overlay only evidence/pr02 and AI_USAGE.md before evidence commit', flush=True)
shutil.copytree('/source/evidence/pr02', workspace/'evidence/pr02', dirs_exist_ok=True)
shutil.copyfile('/source/AI_USAGE.md', workspace/'AI_USAGE.md')
step_env = dict(os.environ, **workflow['env'])
for step in workflow['steps'][2:]:
    print('WORKFLOW RUN: '+step['name'], flush=True)
    run(['bash', '--noprofile', '--norc', '-eo', 'pipefail', '-c', step['run']], cwd=workspace, env=step_env)
print('PASS: all workflow shell steps including build, installed launch, package tests and evidence checker', flush=True)
lines = (runtime/'state').read_text().splitlines()
i=0
while i < len(lines):
    name, marker = lines[i].split('<<', 1)
    i += 1
    values=[]
    while lines[i] != marker:
        values.append(lines[i]); i += 1
    env['STATE_'+name] = '\n'.join(values)
    i += 1
print('CHECKOUT POST: saved main state, same Node runtime', flush=True)
run(['node', '/action/dist/index.js'], env=env)
assert subprocess.run(['git', '-C', str(workspace), 'config', '--local', '--get', key], stdout=subprocess.DEVNULL).returncode == 1
print('PASS: post executed and removed test auth header', flush=True)
