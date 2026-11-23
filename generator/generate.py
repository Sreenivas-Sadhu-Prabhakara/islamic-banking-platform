#!/usr/bin/env python3
"""islamic-banking-platform service generator.

Reads catalog/islamic-service-landscape.json (catalog schema v2) and stamps one
independent git repo per Islamic service domain from templates/service/ plus the
per-domain renderers in render.py.

CATALOG SCHEMA v2 IS WHAT MAKES THE SERVICES DIFFERENT FROM EACH OTHER.  A v1
entry was {name, functionalPattern, assetType} — three fields — so every one of
the 48 generated services was a byte-identical scaffold with
`additionalProperties: true` and a ConcurrentHashMap.  This generator now
VALIDATES each entry against catalog/islamic-service-landscape.schema.json and
REFUSES to stamp a malformed one.  There is no scaffold fallback.

Usage:
    python3 generate.py                     # stamp all missing repos
    python3 generate.py --validate-only     # validate the whole catalog, write nothing
    python3 generate.py --dry-run           # per-repo diff of what WOULD change
    python3 generate.py --force             # re-stamp existing repos
    python3 generate.py --only isb-mudarabah-savings-account
    python3 generate.py --out /tmp/throwaway --no-git

SAFETY.  A repo carrying a `.bian-graduated` marker owns all of its files and is
never touched, not even with --force.  See docs/adr/0004-graduation.md.

Stdlib only — no dependencies. Deterministic: same catalog in, same repos out.
"""

from __future__ import annotations

import argparse
import difflib
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import catalog_validate      # noqa: E402 - sibling module, stdlib only
import render                # noqa: E402
import rules_lang            # noqa: E402
CATALOG = HERE.parent / "catalog" / "islamic-service-landscape.json"
SCHEMA = HERE.parent / "catalog" / "islamic-service-landscape.schema.json"
TEMPLATE = HERE / "templates" / "service"
DEFAULT_OUT = HERE.parent.parent / "islamic-banking-services"

COMMIT_MESSAGE = (
    "Initial commit: generated Islamic banking service domain '{sd}'\n\n"
    "Stamped by islamic-banking-platform/generator (Phase 1 — shallow build).\n\n"
    "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
)

RESTAMP_MESSAGE = (
    "Re-stamp from golden template\n\n"
    "Boilerplate refresh via islamic-banking-platform/generator --force.\n\n"
    "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
)

# BIAN-style control-record naming: functional pattern -> generic artifact noun.
# e.g. Current Account (Fulfill, "Current Account Facility")
#      -> control record "Current Account Facility Fulfillment Arrangement"
PATTERN_NOUN = {
    "Direct": "Strategy",
    "Manage": "Management Plan",
    "Administer": "Administrative Plan",
    "Process": "Procedure",
    "Operate": "Operating Session",
    "Maintain": "Maintenance Agreement",
    "Catalog": "Directory Entry",
    "Develop": "Development Project",
    "Design": "Design",
    "Provide Advice": "Advisory Session",
    "Monitor": "Monitoring State",
    "Track": "Tracking Position",
    "Fulfill": "Fulfillment Arrangement",
    "Transact": "Transaction",
    "Register": "Registration",
    "Allocate": "Allocation",
    "Analyze": "Analysis",
    "Assess": "Assessment",
    "Distribute": "Distribution",
    "Plan": "Plan",
}

# One K8s namespace per BIAN business area.
AREA_NAMESPACE = {
    "Shariah Governance and Compliance": "isb-governance",
    "Deposits and Investment Accounts": "isb-deposits",
    "Islamic Financing": "isb-financing",
    "Treasury Markets and Sukuk": "isb-treasury",
    "Takaful and Shared Operations": "isb-operations",
    "Islamic Account Servicing and Positions": "isb-accounts",
}


def slug(text: str) -> str:
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", text.lower())).strip("-")


def package_segment(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", text.lower())


def build_context(area: str, domain: str, sd: dict) -> dict:
    name = sd["name"]
    pattern = sd["functionalPattern"]
    asset = sd["assetType"]
    sd_slug = slug(name)
    control_record = f"{asset} {PATTERN_NOUN[pattern]}"
    return {
        "__SD_NAME__": name,
        "__SD_SLUG__": sd_slug,
        "__ARTIFACT_ID__": f"isb-{sd_slug}",
        "__PACKAGE__": f"com.bank.islamic.{package_segment(name)}",
        "__BUSINESS_AREA__": area,
        "__BUSINESS_AREA_SLUG__": slug(area),
        "__BUSINESS_DOMAIN__": domain,
        "__BUSINESS_DOMAIN_SLUG__": slug(domain),
        "__FUNCTIONAL_PATTERN__": pattern,
        "__FUNCTIONAL_PATTERN_SLUG__": slug(pattern),
        "__ASSET_TYPE__": asset,
        "__CONTROL_RECORD__": control_record,
        "__CR_SLUG__": slug(control_record),
        "__NAMESPACE__": AREA_NAMESPACE[area],
        "__MODEL_PKG__": f"com.bank.islamic.{package_segment(name)}.model",
        "__API_PKG__": f"com.bank.islamic.{package_segment(name)}.api.generated",
        "__MIGRATION_FILE__": f"V1__{slug(control_record).replace('-', '_')}.sql",
    }


def substitute(text: str, ctx: dict) -> str:
    for key, value in ctx.items():
        text = text.replace(key, value)
    return text


def planned_files(ctx: dict, sd: dict,
                  warnings: list[str] | None = None) -> dict[str, str]:
    """Every file this generator would write for one domain, path -> content.

    ONE function decides the whole output, so --dry-run shows exactly what a
    real run writes and the two can never diverge.
    """
    pkg_path = ctx["__PACKAGE__"].replace(".", "/")
    out: dict[str, str] = {}

    # 1. the shared template: identical for every domain (Helm, CI, Dockerfile,
    #    the contract test). This is the genuinely good part of the estate and
    #    is left alone.
    for src in sorted(TEMPLATE.rglob("*")):
        if not src.is_file():
            continue
        rel = src.relative_to(TEMPLATE).as_posix()
        rel = rel.replace("__JAVA_TEST__", f"src/test/java/{pkg_path}")
        rel = rel.replace("__JAVA__", f"src/main/java/{pkg_path}")
        out[substitute(rel, ctx)] = substitute(src.read_text(), ctx)

    # 2. the per-domain artefacts, derived from the catalog entry
    translations = [rules_lang.translate(r, sd["controlRecord"]["fields"])
                    for r in sd["rules"]]
    main = f"src/main/java/{pkg_path}"
    test = f"src/test/java/{pkg_path}"
    out["api/openapi.yaml"] = render.render_openapi(ctx, sd)
    out["api/events.yaml"] = render.render_events(ctx, sd)
    out[f"src/main/resources/db/migration/{ctx['__MIGRATION_FILE__']}"] = \
        render.render_migration(ctx, sd, translations)
    out[f"{main}/money/Iso4217.java"] = render.render_iso4217(ctx)
    out[f"{main}/rules/ShariahRules.java"] = render.render_rules(ctx, sd, translations)
    out[f"{main}/repo/{render.camel(sd['name'])}Repository.java"] = \
        render.render_repository(ctx, sd)
    out[f"{main}/api/{render.camel(sd['name'])}Controller.java"] = \
        render.render_controller(ctx, sd)
    out[f"{main}/config/SecurityConfig.java"] = render.render_security_config(ctx, sd)
    out[f"{test}/rules/ShariahRulesTest.java"] = \
        render.render_rules_test(ctx, sd, translations)
    out[f"{test}/api/AuthorizationDenyTest.java"] = render.render_deny_test(ctx, sd)
    out[f"{test}/ApplicationTests.java"] = render.render_app_test(ctx, sd)
    out["docs/RULES-GAPS.md"] = render.render_rules_gaps(
        ctx, sd, translations, warnings or [])
    out["docs/SHARIAH-GAPS.md"] = render.render_shariah_gaps(ctx, sd)
    return out


def superseded(ctx: dict) -> list[str]:
    """Files an EARLIER version of this generator wrote and this one replaces.

    A re-stamp that only adds files leaves the Phase-1 scaffold behind, and the
    leftovers are not inert: the old ServiceDomainController maps the same paths
    as the generated controller (two beans, one URL) and the old
    model/ControlRecord collides with the one openapi-generator derives from the
    contract.  So the generator removes exactly these three, and nothing else.
    """
    pkg_path = ctx["__PACKAGE__"].replace(".", "/")
    return [f"src/main/java/{pkg_path}/api/ServiceDomainController.java",
            f"src/main/java/{pkg_path}/model/ControlRecord.java",
            f"src/main/java/{pkg_path}/service/ControlRecordStore.java"]


def stamp(repo_dir: Path, files: dict[str, str], stale: list[str]) -> None:
    for rel in stale:
        path = repo_dir / rel
        if path.exists():
            path.unlink()
            parent = path.parent
            if parent.is_dir() and not any(parent.iterdir()):
                parent.rmdir()
    for rel, content in files.items():
        dest = repo_dir / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content)


def diff_report(repo_dir: Path, files: dict[str, str],
                stale: list[str]) -> list[str]:
    """What --dry-run prints: per-file added / changed / unchanged, with the
    unified diff of the contract and the migration, which are the two files a
    reviewer actually needs to see before a re-stamp."""
    lines, added, changed, same = [], [], [], []
    for rel, content in sorted(files.items()):
        path = repo_dir / rel
        if not path.exists():
            added.append(rel)
            continue
        current = path.read_text()
        if current == content:
            same.append(rel)
            continue
        changed.append(rel)
        if rel.endswith((".yaml", ".sql")) and rel.startswith(("api/", "src/main/resources/")):
            lines += list(difflib.unified_diff(
                current.splitlines(), content.splitlines(),
                fromfile=f"a/{rel}", tofile=f"b/{rel}", lineterm="", n=2))
    orphans = []
    if repo_dir.exists():
        tracked = {p.relative_to(repo_dir).as_posix()
                   for p in repo_dir.rglob("*")
                   if p.is_file() and ".git/" not in p.as_posix()}
        orphans = sorted(tracked - set(files) - set(stale) - {".bian-graduated"})
    removed = [rel for rel in stale if (repo_dir / rel).exists()]
    head = [f"    + {len(added)} new, ~ {len(changed)} changed, "
            f"= {len(same)} unchanged, - {len(removed)} superseded, "
            f"? {len(orphans)} present but not generated"]
    for rel in removed:
        head.append(f"    - {rel}  (superseded Phase-1 file, would be DELETED)")
    for rel in added:
        head.append(f"    + {rel}")
    for rel in changed:
        head.append(f"    ~ {rel}")
    for rel in orphans:
        head.append(f"    ? {rel}  (would be LEFT IN PLACE, not deleted)")
    return head + lines


def git_commit(repo_dir: Path, sd_name: str) -> None:
    def run(*args: str) -> None:
        subprocess.run(["git", *args], cwd=repo_dir, check=True, capture_output=True)

    fresh = not (repo_dir / ".git").exists()
    if fresh:
        run("init", "-q", "-b", "main")
    has_head = not fresh and subprocess.run(
        ["git", "rev-parse", "-q", "--verify", "HEAD"],
        cwd=repo_dir, capture_output=True).returncode == 0
    run("add", "-A")
    status = subprocess.run(["git", "status", "--porcelain"], cwd=repo_dir,
                            check=True, capture_output=True, text=True)
    if status.stdout.strip():
        msg = RESTAMP_MESSAGE if has_head else COMMIT_MESSAGE.format(sd=sd_name)
        run("commit", "-q", "-m", msg)


def iter_service_domains(catalog: dict):
    for area in catalog["businessAreas"]:
        for domain in area["businessDomains"]:
            for sd in domain["serviceDomains"]:
                yield area["name"], domain["name"], sd


def write_registry(out_dir: Path, entries: list[dict]) -> None:
    (out_dir / "registry.json").write_text(json.dumps(
        {"generatedFrom": "islamic-banking-platform/catalog/islamic-service-landscape.json",
         "count": len(entries), "services": entries}, indent=2) + "\n")

    lines = [
        "# Islamic Banking Service Registry",
        "",
        f"**{len(entries)} service domains**, one repo each, stamped by `islamic-banking-platform/generator`.",
        "",
        "| Repo | Service Domain | Business Area | Pattern | Namespace | Gateway path |",
        "|---|---|---|---|---|---|",
    ]
    for e in entries:
        lines.append(
            f"| `{e['repo']}` | {e['serviceDomain']} | {e['businessArea']} "
            f"| {e['functionalPattern']} | `{e['namespace']}` | `/{e['repo']}` |")
    (out_dir / "REGISTRY.md").write_text("\n".join(lines) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--force", action="store_true",
                        help="re-stamp repos that already exist (git history is preserved)")
    parser.add_argument("--only", nargs="*", default=None,
                        help="service-domain slugs to generate (default: all)")
    parser.add_argument("--dry-run", action="store_true",
                        help="print what WOULD change per repo, write nothing")
    parser.add_argument("--strict", action="store_true",
                        help="treat catalog warnings as errors (CI gate)")
    parser.add_argument("--validate-only", action="store_true",
                        help="validate every catalog entry and exit non-zero on "
                             "any error; writes nothing")
    parser.add_argument("--no-git", action="store_true", help="skip git init/commit")
    args = parser.parse_args()

    catalog = json.loads(CATALOG.read_text())

    # ---- validation first, always.  A malformed entry is an error, never a
    # ---- scaffold.  This is the fix for the 48-identical-services root cause.
    known_patterns = set(catalog.get("functionalPatterns", [])) & set(PATTERN_NOUN)
    bad, warn = catalog_validate.validate_catalog(
        catalog, known_patterns, set(AREA_NAMESPACE), SCHEMA)
    if warn:
        total = sum(len(v) for v in warn.values())
        print(f"catalog warnings: {total} across {len(warn)} domains "
              f"(incomplete, not wrong — written into each repo's "
              f"docs/RULES-GAPS.md; --strict makes these fatal)")
        for name, ws in sorted(warn.items()):
            for w in ws[:3]:
                print(f"  ! {w}")
            if len(ws) > 3:
                print(f"  ! … {len(ws) - 3} more in {name}")
    if args.strict and warn:
        for name in warn:
            bad.setdefault(name, []).extend(warn[name])
    if bad:
        print(f"CATALOG VALIDATION FAILED for {len(bad)} entries:", file=sys.stderr)
        for name, errs in sorted(bad.items()):
            print(f"  {name}:", file=sys.stderr)
            for e in errs[:20]:
                print(f"    - {e}", file=sys.stderr)
            if len(errs) > 20:
                print(f"    … {len(errs) - 20} more", file=sys.stderr)
    else:
        print(f"catalog v{catalog.get('version')} validated clean: "
              f"{sum(1 for _ in iter_service_domains(catalog))} service domains, "
              f"0 errors")
    if args.validate_only:
        return 1 if bad else 0

    if not args.dry_run:
        args.out.mkdir(parents=True, exist_ok=True)

    entries, created, updated, skipped, refused = [], 0, 0, 0, 0
    for area, domain, sd in iter_service_domains(catalog):
        ctx = build_context(area, domain, sd)
        if args.only and not ({ctx["__SD_SLUG__"], ctx["__ARTIFACT_ID__"]}
                              & set(args.only)):
            continue
        repo_dir = args.out / ctx["__ARTIFACT_ID__"]
        entries.append({
            "repo": ctx["__ARTIFACT_ID__"],
            "serviceDomain": sd["name"],
            "businessArea": area,
            "businessDomain": domain,
            "functionalPattern": sd["functionalPattern"],
            "assetType": sd["assetType"],
            "controlRecord": ctx["__CONTROL_RECORD__"],
            "namespace": ctx["__NAMESPACE__"],
            "package": ctx["__PACKAGE__"],
        })

        # Graduated repos (deep, hand/Fable-authored domain code) own ALL their
        # files — the generator never touches them again, even with --force.
        # See docs/adr/0004-graduation.md.
        if (repo_dir / ".bian-graduated").exists():
            print(f"GRADUATED, refusing to touch (even with --force): {repo_dir}")
            skipped += 1
            continue

        # A domain the validator rejected is REFUSED, not scaffolded.
        if sd["name"] in bad:
            print(f"REFUSING to stamp {ctx['__ARTIFACT_ID__']}: "
                  f"{len(bad[sd['name']])} catalog errors (see above)",
                  file=sys.stderr)
            refused += 1
            continue

        exists = repo_dir.exists()
        if exists and not (args.force or args.dry_run):
            skipped += 1
            continue

        files = planned_files(ctx, sd, warn.get(sd["name"], []))
        if args.dry_run:
            print(f"\n{ctx['__ARTIFACT_ID__']}  "
                  f"({'exists' if exists else 'NEW'})  ->  {repo_dir}")
            for line in diff_report(repo_dir, files, superseded(ctx)):
                print(line)
            continue
        stamp(repo_dir, files, superseded(ctx))
        if not args.no_git:
            git_commit(repo_dir, sd["name"])
        created += 0 if exists else 1
        updated += 1 if exists else 0

    if not args.dry_run and not args.only:
        write_registry(args.out, entries)

    if args.dry_run:
        print(f"\n--dry-run: nothing written. {refused} domain(s) would be "
              f"REFUSED for catalog errors, {skipped} skipped (graduated or "
              f"already present).")
        return 1 if refused else 0
    print(f"done: {created} created, {updated} re-stamped, {skipped} skipped, "
          f"{refused} REFUSED for catalog errors · registry: {len(entries)} entries")
    return 1 if refused else 0


if __name__ == "__main__":
    sys.exit(main())
