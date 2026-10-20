"""Compare built wheel/sdist payloads with the single canonical default source."""

import argparse
import tarfile
import zipfile
from pathlib import Path


def verify(artifact: Path, expected: dict[str, bytes]) -> None:
    """Reject absent, duplicate, changed and obsolete-root default payloads."""
    if artifact.suffix == ".whl":
        with zipfile.ZipFile(artifact) as archive:
            names = archive.namelist()
            for name, payload in expected.items():
                if names.count(name) != 1 or archive.read(name) != payload:
                    raise SystemExit(f"Missing, duplicate or altered payload: {artifact}: {name}")
            if any(name.startswith(("prompts/", "rules/")) for name in names):
                raise SystemExit(f"Duplicate root payload: {artifact}")
        return
    with tarfile.open(artifact, "r:gz") as archive:
        members = archive.getmembers()
        if not members:
            raise SystemExit(f"Missing payloads in empty archive: {artifact}")
        prefix = members[0].name.split("/")[0] + "/"
        for name, payload in expected.items():
            matches = [member for member in members if member.name == prefix + name]
            if len(matches) != 1 or not matches[0].isfile():
                raise SystemExit(f"Missing or duplicate payload: {artifact}: {name}")
            with archive.extractfile(matches[0]) as stream:
                if stream.read() != payload:
                    raise SystemExit(f"Altered payload: {artifact}: {name}")
        if any(
            member.name.startswith((prefix + "prompts/", prefix + "rules/")) for member in members
        ):
            raise SystemExit(f"Duplicate root payload: {artifact}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifacts", nargs="+", type=Path)
    args = parser.parse_args()
    canonical = Path(__file__).resolve().parents[1] / "src/utils/assets"
    expected = {
        "src/utils/assets/" + path.relative_to(canonical).as_posix(): path.read_bytes()
        for path in canonical.rglob("*")
        if path.is_file()
    }
    if len(expected) != 9:
        raise SystemExit("Expected exactly nine canonical default payloads")
    for artifact in args.artifacts:
        verify(artifact, expected)
        print(f"{artifact.name}: nine default payloads match canonical bytes")


if __name__ == "__main__":
    main()
