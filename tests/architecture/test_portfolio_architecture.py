from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CHECKER_PATH = ROOT / "scripts" / "check_portfolio_architecture.py"


def load_checker() -> ModuleType:
    spec = importlib.util.spec_from_file_location("check_portfolio_architecture", CHECKER_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def source_contract() -> dict[str, object]:
    return {
        "source_layout": {
            "python_rules_applicable": True,
            "allowed_non_python_files": [],
            "metadata_names": [],
            "python_source_roots": ["src"],
        },
        "limits": {
            "max_immediate_runtime_entries": 10,
            "max_python_module_lines": 2,
        },
    }


def test_portfolio_architecture_contract() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/check_portfolio_architecture.py"],
        check=False,
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_hidden_source_metadata_does_not_require_exception(
    tmp_path: Path, monkeypatch: Any
) -> None:
    checker = load_checker()
    source = tmp_path / "src"
    source.mkdir()
    (source / "app.py").write_text("pass\n", encoding="utf-8")
    (source / ".gitignore").write_text("*.pyc\n", encoding="utf-8")
    monkeypatch.setattr(checker, "ROOT", tmp_path)

    errors: list[str] = []
    checker.validate_source(source_contract(), {}, errors)

    assert errors == []


def test_visible_source_entry_type_gate_still_requires_exception(
    tmp_path: Path, monkeypatch: Any
) -> None:
    checker = load_checker()
    source = tmp_path / "src"
    source.mkdir()
    (source / "app.py").write_text("pass\n", encoding="utf-8")
    (source / "notes.txt").write_text("not runtime metadata\n", encoding="utf-8")
    monkeypatch.setattr(checker, "ROOT", tmp_path)

    errors: list[str] = []
    checker.validate_source(source_contract(), {}, errors)

    assert errors == ["source_entry_type violation at src/notes.txt: 1; no documented exception"]


def test_hidden_directories_are_not_scanned_for_python_modules(
    tmp_path: Path, monkeypatch: Any
) -> None:
    checker = load_checker()
    source = tmp_path / "src"
    hidden = source / ".generated"
    hidden.mkdir(parents=True)
    (source / "app.py").write_text("pass\n", encoding="utf-8")
    (hidden / "oversized.py").write_text("pass\npass\npass\n", encoding="utf-8")
    monkeypatch.setattr(checker, "ROOT", tmp_path)

    errors: list[str] = []
    checker.validate_source(source_contract(), {}, errors)

    assert errors == []


def test_visible_python_module_line_gate_still_requires_exception(
    tmp_path: Path, monkeypatch: Any
) -> None:
    checker = load_checker()
    source = tmp_path / "src"
    source.mkdir()
    (source / "oversized.py").write_text("pass\npass\npass\n", encoding="utf-8")
    monkeypatch.setattr(checker, "ROOT", tmp_path)

    errors: list[str] = []
    checker.validate_source(source_contract(), {}, errors)

    assert errors == [
        "python_module_max_lines violation at src/oversized.py: 3; no documented exception"
    ]


def test_unreadable_python_module_fails_closed_without_crashing(
    tmp_path: Path, monkeypatch: Any
) -> None:
    checker = load_checker()
    source = tmp_path / "src"
    source.mkdir()
    blocked = source / "blocked.py"
    blocked.write_text("pass\n", encoding="utf-8")
    monkeypatch.setattr(checker, "ROOT", tmp_path)
    original_read_text = Path.read_text

    def read_text_or_raise(self: Path, *args: Any, **kwargs: Any) -> str:
        if self == blocked:
            raise PermissionError("denied")
        return original_read_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", read_text_or_raise)

    errors: list[str] = []
    checker.validate_source(source_contract(), {}, errors)

    assert len(errors) == 1
    assert "Python module cannot be read: src/blocked.py" in errors[0]
