#!/usr/bin/env python3
"""Regression test for the two safety properties of generate.py.

    python3 generator/test_guard.py

1. A repo carrying `.bian-graduated` is never written to, NOT EVEN with --force.
   Graduated repos hold hand-authored domain code behind a real GitHub origin;
   a re-stamp would destroy it.  The 7 graduated BIAN services are the live
   instance of this, and this test is the one that fails if the guard regresses.
2. --dry-run writes nothing at all.

Everything happens in a temporary directory.  This test never touches
islamic-banking-services or bian-services.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
DOMAIN = "isb-mudarabah-savings-account"
SENTINEL = "hand-authored domain code — the generator must never overwrite this\n"


def run(out: Path, *extra: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-I", str(HERE / "generate.py"),
         "--only", DOMAIN, "--out", str(out), "--no-git", *extra],
        capture_output=True, text=True)


def main() -> int:
    failures = []
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        repo = out / DOMAIN
        (repo / "api").mkdir(parents=True)
        (repo / ".bian-graduated").write_text("graduated 2026-01-01\n")
        (repo / "api" / "openapi.yaml").write_text(SENTINEL)
        before = sorted(p.relative_to(repo).as_posix() for p in repo.rglob("*"))

        for extra in ((), ("--force",)):
            res = run(out, *extra)
            label = "--force" if extra else "plain"
            if (repo / "api" / "openapi.yaml").read_text() != SENTINEL:
                failures.append(f"GUARD BROKEN ({label}): the generator "
                                f"overwrote a .bian-graduated repo's file")
            after = sorted(p.relative_to(repo).as_posix() for p in repo.rglob("*"))
            if after != before:
                failures.append(f"GUARD BROKEN ({label}): files added to a "
                                f"graduated repo: {set(after) - set(before)}")
            if "GRADUATED, refusing to touch" not in res.stdout:
                failures.append(f"GUARD SILENT ({label}): the generator did not "
                                f"say it was refusing. stdout tail: "
                                f"{res.stdout[-200:]!r}")

    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        res = run(out, "--dry-run")
        written = [p for p in out.rglob("*")]
        if written:
            failures.append(f"--dry-run WROTE {len(written)} paths, e.g. "
                            f"{written[0]}")
        if "+ " not in res.stdout:
            failures.append("--dry-run printed no per-file plan")

    for f in failures:
        print("FAIL:", f)
    print(f"guard test: {'PASS' if not failures else str(len(failures)) + ' FAILURES'}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
