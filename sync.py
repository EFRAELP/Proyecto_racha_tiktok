import subprocess
import os

BASE = os.path.dirname(os.path.abspath(__file__))


def _run(cmd):
    result = subprocess.run(
        cmd, capture_output=True, text=True, cwd=BASE
    )
    return result.returncode == 0, (result.stdout + result.stderr).strip()


def git_pull():
    return _run(["git", "pull"])


def git_push(mensaje="sync rachas"):
    _run(["git", "add", "data/"])
    ok_commit, _ = _run(["git", "commit", "-m", mensaje])
    if not ok_commit:
        # Nothing to commit is fine
        pass
    return _run(["git", "push"])
