from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def test_cases_cli_does_not_require_llm_or_google_credentials(tmp_path) -> None:
    """The local state inspection CLI must be usable without external clients."""
    env = os.environ.copy()
    env["HOME"] = str(tmp_path)
    env.pop("ANTHROPIC_API_KEY", None)
    repo_root = Path(__file__).resolve().parents[2]

    blocker_dir = tmp_path / "import_blocker"
    blocker_dir.mkdir()
    (blocker_dir / "sitecustomize.py").write_text(
        """
import importlib.abc
import sys

_BLOCKED = ("anthropic", "google", "googleapiclient", "google_auth_oauthlib")


class _Blocker(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname in _BLOCKED or any(fullname.startswith(prefix + ".") for prefix in _BLOCKED):
            raise RuntimeError(f"optional dependency import leaked into local CLI path: {fullname}")
        return None


sys.meta_path.insert(0, _Blocker())
""".lstrip(),
        encoding="utf-8",
    )
    env["PYTHONPATH"] = str(blocker_dir)

    result = subprocess.run(
        [sys.executable, "-m", "src.main", "--run", "cases"],
        cwd=repo_root,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "[]"
    assert "ANTHROPIC_API_KEY" not in result.stderr
