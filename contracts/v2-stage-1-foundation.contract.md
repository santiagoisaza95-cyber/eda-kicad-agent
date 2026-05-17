# Stage Contract: Stage 1 — Foundation (v2.0)

**CRITICAL RULE:** Workers are NOT allowed to mark tasks complete until the relevant batch checklist is fulfilled. Only the Auditor can declare this contract complete.

**Operational expansion**: see `docs/stages/stage-1-foundation-1m.md`. This contract is the interface + verification surface; the stage doc is the operational guide workers consult during implementation.

## Stage Overview
- **Scope**: Build the v2 substrate — visual render pipeline (`scripts/render_board.py`), supplier-anchored DRC profile system (`supplier_profiles/` + `scripts/supplier_drc/`), audition contract for the 555 LED blinker, demotion of 4.6 artifacts to `baselines/4.6/`, refreshed `api_manifest.json`, extended toolchain verifier, 5 `.context.md` files.
- **Depends on**: Nothing (first stage of v2 build). The v1 repo at HEAD provides starting state (working KiCad MCP, surviving routing CLI, existing agent_docs structure, v1 blue_pill artifacts at `scripts/build_blue_pill.py` + `scripts/route_blue_pill.py` + `output/blue_pill.*`).
- **Produces**: All Stage 2 prerequisites — `scripts/render_board.py` callable, `scripts/supplier_drc/{loader,validators,__init__}.py` package exporting `load_supplier_profile` + `emit_kicad_dru`, `supplier_profiles/jlcpcb.yaml` populated, `agent_docs/rules/supplier-drc-rules.md` mandatory rule, `contracts/blinker_555_contract.md` parseable, `tests/test_blinker_555.py` collectible, `baselines/4.6/` populated with provenance README, refreshed `api_manifest.json`, updated `scripts/verify_toolchain.py`, updated `requirements.txt`, 5 of 6 `docs/context/*.context.md` files (the 6th is Stage 2 deliverable).
- **Team composition**: 1–4 workers (batches 1.1 / 1.2 / 1.3 / 1.4 are independent and may be parallelized) + 1 tester + 1 auditor + 1 scribe. CTO must spawn the auditor LAST or serialize TaskCreate-then-spawn to avoid the premature-audit race (per `feedback_auditor_premature_audit_race`).

---

## Batch 1.1: Render pipeline foundation

### Deliverables Table
| Task | Owner | Output | Test |
|------|-------|--------|------|
| Add `cairosvg>=2.7.0` + `lxml>=5.0.0` to requirements | Worker | `requirements.txt` (modified) | `pip install -r requirements.txt` clean |
| Extend toolchain verifier to probe cairosvg + lxml + GTK3 | Worker | `scripts/verify_toolchain.py` (modified) | `python scripts/verify_toolchain.py` exits 0 |
| Implement `render_board()` with subprocess kicad-cli → lxml dark-bg inject → cairosvg | Worker | `scripts/render_board.py` (new, ~120 LOC) | `tests/test_render_board.py` 4 named tests |
| Add CLI entry to render_board.py | Worker | Same file (CLI under `if __name__ == "__main__":`) | `python scripts/render_board.py output/blue_pill.kicad_pcb` produces PNG |
| Author render-board tests | Worker | `tests/test_render_board.py` (new) | `pytest tests/test_render_board.py -v` green |
| Author render-pipeline context doc | Worker | `docs/context/render-pipeline.context.md` (new) | Manual readable; documents return dict + layer order |

### Interface Contract
```python
# scripts/render_board.py
def render_board(
    pcb_path: Path,
    output_dir: Optional[Path] = None,
    layers: Optional[list[str]] = None,
    dpi: int = 150,
    generate_variants: bool = True,
) -> dict[str, Path]:
    """Returns {'full': PNG path, 'copper': PNG path | None, 'svg': SVG path}.
    Default layers: [Edge_Cuts, B.Cu, F.Cu, F.Mask, F.SilkS].
    Copper-only layers: [F.Cu, B.Cu].
    Raises FileNotFoundError if pcb_path doesn't exist or kicad-cli not on PATH.
    Raises subprocess.CalledProcessError if kicad-cli SVG export fails.
    Raises RuntimeError if cairosvg fails (typically GTK3 not installed).
    """
```

**Return dict invariants:**
- `result["full"]` always exists, is a `Path`, points to a non-zero PNG with #1a1a1a (26,26,26) BG
- `result["copper"]` is `None` iff `generate_variants=False`, else a `Path` to a non-zero PNG
- `result["svg"]` always exists as the intermediate SVG (kept for debugging)

**Performance contract**: `render_board(Path("output/blue_pill.kicad_pcb"))` completes in <2.0 s wall time. Enforced via `pytest-timeout`.

### Verification Commands
```
$ pip install -r requirements.txt
Expected: cairosvg + lxml install cleanly (alongside existing deps)
Failure means: requirements.txt malformed, or pip mirror issue. Re-run with --verbose to diagnose.

$ python scripts/verify_toolchain.py
Expected: exit 0; "OK" for cairosvg, lxml, GTK3 (on Windows)
Failure means: missing GTK3 → run `choco install gtk3-runtime-bin-x64`; missing pip package → re-run pip install.

$ pytest tests/test_render_board.py -v
Expected: 4 tests passed (return-dict shape, PNG nonzero, dark BG sample, <2s timeout)
Failure means: render pipeline broken. Check kicad-cli on PATH; check GTK3; check lxml/cairosvg versions.

$ python scripts/render_board.py output/blue_pill.kicad_pcb
Expected: output/blue_pill_full.png + output/blue_pill_copper.png exist, sub-2s wall time
Failure means: real-input regression. Differs from test fixture path resolution; investigate.
```

### Batch Completion Criteria
- [ ] `requirements.txt` contains `cairosvg>=2.7.0` and `lxml>=5.0.0`
- [ ] `python scripts/verify_toolchain.py` exits 0 with cairosvg + lxml + GTK3 checks passing
- [ ] `scripts/render_board.py` exists; implements documented signature; returns dict with `full`/`copper`/`svg` keys
- [ ] `scripts/render_board.py` provides CLI entry: `python scripts/render_board.py <pcb_path>` works
- [ ] `tests/test_render_board.py` contains ≥4 tests covering: (a) return-dict shape, (b) PNGs non-zero, (c) dark BG sample pixel == (26,26,26), (d) <2 s timeout via pytest-timeout
- [ ] `pytest tests/test_render_board.py -v` green
- [ ] `python scripts/render_board.py output/blue_pill.kicad_pcb` produces both PNGs in <2 s wall time
- [ ] `docs/context/render-pipeline.context.md` exists; documents module boundary, return dict schema, layer order rationale, speed budget
- [ ] All verification commands pass
- [ ] No new ruff/lint violations introduced

---

## Batch 1.2: Supplier DRC profile system

### Deliverables Table
| Task | Owner | Output | Test |
|------|-------|--------|------|
| Define Pydantic v2 SupplierProfile schema with 7 nested rule sections | Worker | `supplier_profiles/schema.py` (new, ~150 LOC) | `test_supplier_drc.py::test_schema_loads` |
| Author JLCPCB YAML populated from research table (18 axes) | Worker | `supplier_profiles/jlcpcb.yaml` (new) | `test_supplier_drc.py::test_jlcpcb_profile_valid` |
| Implement `load_supplier_profile(name) -> SupplierProfile` | Worker | `scripts/supplier_drc/loader.py` (new) | included in test suite |
| Implement `emit_kicad_dru(profile, out_path) -> Path` | Worker | Same `scripts/supplier_drc/loader.py` | `test_supplier_drc.py::test_emit_dru` |
| Validator stubs (NotImplementedError) for v2.x external checks | Worker | `scripts/supplier_drc/validators.py` (new, stubs only) | not exercised; import-only |
| Package `__init__.py` re-exporting public API | Worker | `scripts/supplier_drc/__init__.py` (new) | implicit via test imports |
| Supplier-profiles README documenting schema + extension path | Worker | `supplier_profiles/README.md` (new) | Manual readable |
| Author supplier-DRC tests (5 named) | Worker | `tests/test_supplier_drc.py` (new) | `pytest tests/test_supplier_drc.py -v` 5/5 green |
| Mandatory supplier-DRC rule file | Worker | `agent_docs/rules/supplier-drc-rules.md` (new) | Manual: rule loads via CLAUDE.md (Stage 2 wires routing) |
| Supplier-DRC context doc | Worker | `docs/context/supplier-drc.context.md` (new) | Manual readable |

### Interface Contract
```python
# scripts/supplier_drc/loader.py
def load_supplier_profile(name: str) -> SupplierProfile:
    """Load supplier_profiles/<name>.yaml; Pydantic-validate; return model.
    Raises FileNotFoundError if YAML missing.
    Raises pydantic.ValidationError if YAML malformed against schema."""

def emit_kicad_dru(profile: SupplierProfile, out_path: Path) -> Path:
    """Write .kicad_dru file containing 7 expressible rules:
       track_width, clearance, edge_clearance, annular_width, hole_size (via),
       silk_line_width, silk_text_height.
       Documents 3 gaps inline as ;; comments:
       solder mask clearance (UI-only), non-plated hole min (external),
       board thickness/copper weight (metadata).
    Returns out_path for chaining."""
```

**`supplier_profiles/jlcpcb.yaml` value invariants** (per `research/supplier_drc_research.md` table):
- `min_trace_width.value == 0.127` (mm, 5 mil)
- `min_trace_spacing.value == 0.127`
- `copper_to_edge.value == 0.3`
- `min_via_drill.value == 0.3`
- `min_via_pad_diameter.value == 0.6`
- `min_annular_ring.value == 0.15` with `recommended: 0.2`
- `min_line_width.value == 0.15` (silkscreen)
- `min_text_height.value == 1.0` (silkscreen)
- `min_mask_clearance.value == 0.05` with `direction: per_side`
- `min_mask_web.value == 0.1`
- `thickness.standard == 1.6`
- `copper_weight.standard == 1`

### Verification Commands
```
$ pytest tests/test_supplier_drc.py -v
Expected: 5/5 green — test_schema_loads, test_jlcpcb_profile_valid, test_emit_dru, test_unknown_supplier_raises, test_malformed_yaml_raises
Failure means: schema mismatch or loader bug. Check pydantic model vs YAML structure.

$ python -c "from scripts.supplier_drc import load_supplier_profile, emit_kicad_dru; from pathlib import Path; p = load_supplier_profile('jlcpcb'); emit_kicad_dru(p, Path('/tmp/test.kicad_dru')); print(open('/tmp/test.kicad_dru').read()[:500])"
Expected: DRU header + (rule "Min Trace Width ..." (constraint track_width (min 0.127mm))) and similar lines visible
Failure means: emitter not writing expected text format. Compare against research/supplier_drc_research.md DRU mapping table.

$ test -f agent_docs/rules/supplier-drc-rules.md && echo OK
Expected: OK
Failure means: rule file not authored.

$ test -f docs/context/supplier-drc.context.md && echo OK
Expected: OK
Failure means: context doc not authored.

Manual: open /tmp/test.kicad_dru in KiCad pcbnew DRC settings, verify it parses without errors.
```

### Batch Completion Criteria
- [ ] `supplier_profiles/schema.py` defines `SupplierProfile` with nested `trace_rules`, `via_rules`, `pad_rules`, `solder_mask_rules`, `silkscreen_rules`, `board_rules`, `cost_premiums`
- [ ] `supplier_profiles/jlcpcb.yaml` exists; all 12 value invariants above hold
- [ ] `scripts/supplier_drc/loader.py` exports `load_supplier_profile` + `emit_kicad_dru` with documented signatures
- [ ] `scripts/supplier_drc/validators.py` defines 2 stub functions raising NotImplementedError with docstrings naming v2.x deferral
- [ ] `scripts/supplier_drc/__init__.py` re-exports the 2 public functions
- [ ] `supplier_profiles/README.md` documents schema + how to add a new supplier
- [ ] `tests/test_supplier_drc.py` contains 5 named tests covering schema_loads, jlcpcb_profile_valid, emit_dru, unknown_supplier_raises, malformed_yaml_raises
- [ ] `pytest tests/test_supplier_drc.py -v` 5/5 green
- [ ] `agent_docs/rules/supplier-drc-rules.md` exists; is a mandatory rule (load profile → emit DRU → block routing); lists the 5 risk axes from research (annular ring HIGH, silk-on-pad MEDIUM, trace-to-via MEDIUM, copper-to-edge MEDIUM, mask web LOW)
- [ ] `docs/context/supplier-drc.context.md` exists; documents module boundary, DRU emission semantics, 3 documented gaps
- [ ] Generated `.kicad_dru` parses without errors in KiCad pcbnew (manual verification)
- [ ] No new ruff/lint violations introduced

---

## Batch 1.3: 555 LED blinker audition contract

### Deliverables Table
| Task | Owner | Output | Test |
|------|-------|--------|------|
| Author 555 audition contract | Worker | `contracts/blinker_555_contract.md` (new) | Manual: parseable, supplier metadata present, "DESIGN FROM THIS CONTRACT ONLY" clause |
| Author audition test suite | Worker | `tests/test_blinker_555.py` (new) | `pytest tests/test_blinker_555.py -v --collect-only` enumerates 5 tests |
| Author contracts context doc | Worker | `docs/context/contracts.context.md` (new) | Manual readable |

### Interface Contract
**`contracts/blinker_555_contract.md` required structure:**
- YAML front-matter with: `supplier: jlcpcb`, `layer_count: 2`, `board_dimensions: 20x30 mm`, `fr4_thickness: 1.6 mm`, `copper_weight: 1 oz`, `surface_finish: HASL (lead-free)`
- "## DESIGN FROM THIS CONTRACT ONLY" clause (verbatim heading)
- Components table with 7 rows: U1 (NE555), R1 (1k), R2 (10k), R3 (470Ω), C1 (10μF timing), C2 (0.1μF decoupling), D1 (LED), J1 (power header) — 8 items total, 5–7 active components ± header
- Netlist with ~6 nets: VCC, GND, TRIG, THR, DISCH, OUT
- "## Success Criteria" checklist with at minimum: DRC 0 errors, all nets routed, all components on F.Cu, board within stated dimensions, owner-credible visual judgment

**`tests/test_blinker_555.py` required tests** (mirror `tests/test_blue_pill.py` pattern):
- `test_component_count` — asserts 7 footprints
- `test_nets_routed` — walks netlist, no unconnected pads
- `test_drc_zero` — runs DRC against `output/blinker_555.kicad_dru`, expects 0 violations + 0 unconnected
- `test_dimensions` — asserts board ≤20.5 × 30.5 mm
- `test_components_on_f_cu` — all footprints on F.Cu layer

All tests must use `@pytest.fixture(scope="module") def board()` that skips if `output/blinker_555.kicad_pcb` doesn't exist (audition not yet run).

### Verification Commands
```
$ test -f contracts/blinker_555_contract.md && echo OK
Expected: OK
Failure means: contract not authored.

$ grep "DESIGN FROM THIS CONTRACT ONLY" contracts/blinker_555_contract.md
Expected: at least one match
Failure means: required clause missing.

$ grep "supplier: jlcpcb" contracts/blinker_555_contract.md
Expected: match in YAML front-matter
Failure means: supplier metadata missing or wrong value.

$ pytest tests/test_blinker_555.py -v --collect-only
Expected: 5 tests enumerated (test_component_count, test_nets_routed, test_drc_zero, test_dimensions, test_components_on_f_cu); no import errors
Failure means: tests/test_blinker_555.py has syntax error or missing pcbnew import.

$ test -f docs/context/contracts.context.md && echo OK
Expected: OK
```

### Batch Completion Criteria
- [ ] `contracts/blinker_555_contract.md` exists with YAML front-matter containing all 6 metadata fields (supplier, layer_count, board_dimensions, fr4_thickness, copper_weight, surface_finish)
- [ ] "DESIGN FROM THIS CONTRACT ONLY" clause present
- [ ] Components table has 7 rows for: U1, R1, R2, R3, C1, C2, D1, J1 (8 items total)
- [ ] Netlist documents at least: VCC, GND, TRIG, THR, DISCH, OUT
- [ ] "Success Criteria" checklist contains DRC, connectivity, F.Cu layer, dimensions, owner-credible items
- [ ] `tests/test_blinker_555.py` exists with the 5 named tests above
- [ ] `pytest tests/test_blinker_555.py -v --collect-only` enumerates 5 tests without import errors
- [ ] Tests fixture skips cleanly when `output/blinker_555.kicad_pcb` doesn't exist (audition not yet run)
- [ ] `docs/context/contracts.context.md` exists; documents per-board metadata expectations + "DESIGN FROM CONTRACT ONLY" semantics
- [ ] No new ruff/lint violations introduced

---

## Batch 1.4: 4.6 baselines preservation + API manifest refresh + routing primitives doc

### Deliverables Table
| Task | Owner | Output | Test |
|------|-------|--------|------|
| Create `baselines/4.6/` directory and `git mv scripts/build_blue_pill.py` | Worker | `baselines/4.6/build_blue_pill.py` | `git log --oneline -5 baselines/4.6/build_blue_pill.py` shows pre-move history |
| `git mv scripts/route_blue_pill.py` | Worker | `baselines/4.6/route_blue_pill.py` | git log shows pre-move history |
| `git mv output/blue_pill.{kicad_pcb,kicad_pro,kicad_prl}` | Worker | `baselines/4.6/blue_pill.{kicad_pcb,kicad_pro,kicad_prl}` | git log shows pre-move history |
| Author baselines README documenting provenance | Worker | `baselines/4.6/README.md` (new) | Manual readable; documents 2026-03-06 production, 54/54 tests, owner verdict |
| Author baselines context doc | Worker | `docs/context/baselines.context.md` (new) | Manual readable |
| Author routing-primitives context doc | Worker | `docs/context/routing-primitives.context.md` (new) | Manual readable; documents v1 survivors |
| Refresh api_manifest.json via discover_api.py | Worker | `api_manifest.json` (regenerated) | `python -c "import json; m=json.load(open('api_manifest.json')); print(m['verified_count'] == m['total_count'])"` → True |

### Interface Contract
**`baselines/4.6/README.md` required content:**
- Status: pytest 54/54 passing (commit `4787d57`), DRC 0/0, owner-judged goal-failed
- Provenance: produced 2026-03-06 under Opus 4.6
- Purpose in v2: Stage 3 stretch-test baseline; `scripts/render_board.py` renders this for the v2-vs-4.6 comparison
- Files manifest: build_blue_pill.py, route_blue_pill.py, blue_pill.kicad_pcb, .kicad_pro, .kicad_prl
- "NOT for re-execution" warning — running these scripts replays 4.6's outputs

**`docs/context/routing-primitives.context.md` required content:**
- What survives unchanged from v1: `scripts/routing_cli.py` (A* iterative router with JSON I/O), `scripts/routing/{actions,perception,pathfinder}.py`
- The 45° angle validation rule
- The MCP-routing-tools-BANNED rule (no `route_trace`, `route_pad_to_pad`, `route_differential_pair`)
- Pointer to `agent_docs/skills/routing-skill.md` for operational detail

**`api_manifest.json` post-refresh invariant:**
- `verified_count == total_count` (100% verified)
- Timestamp updated (newer than v1's 72-day-old version)

### Verification Commands
```
$ git log --oneline -10
Expected: visible "git mv" entries for build_blue_pill.py, route_blue_pill.py, blue_pill.*; no `rm`+`add` pattern (that would lose blame)
Failure means: worker used `mv`+`git add` instead of `git mv`; blame history lost. RED verdict — re-do with git mv.

$ test -d baselines/4.6 && ls baselines/4.6/
Expected: README.md, build_blue_pill.py, route_blue_pill.py, blue_pill.kicad_pcb, blue_pill.kicad_pro, blue_pill.kicad_prl (6 items)
Failure means: demotion incomplete or directory missing.

$ test -f baselines/4.6/README.md && grep -E "(2026-03-06|54/54|goal-failed|Round 2)" baselines/4.6/README.md
Expected: at least 3 of those substrings match
Failure means: README provenance incomplete.

$ python -c "import json; m=json.load(open('api_manifest.json')); print(m['verified_count'], '/', m['total_count'])"
Expected: equal counts (e.g. "N / N" with N > 0)
Failure means: api_manifest refresh failed or partial.

$ test -f docs/context/baselines.context.md && test -f docs/context/routing-primitives.context.md && echo OK
Expected: OK
Failure means: one or both context docs missing.

$ ls docs/context/ | wc -l
Expected: 5 (render-pipeline, supplier-drc, contracts, baselines, routing-primitives — agent-skills is Stage 2)
Failure means: wrong file count in docs/context/.
```

### Batch Completion Criteria
- [ ] `baselines/4.6/` directory exists
- [ ] `baselines/4.6/build_blue_pill.py` exists, moved via `git mv` (blame history preserved per `git log -- baselines/4.6/build_blue_pill.py`)
- [ ] `baselines/4.6/route_blue_pill.py` exists, moved via `git mv`
- [ ] `baselines/4.6/blue_pill.kicad_pcb`, `.kicad_pro`, `.kicad_prl` exist, all moved via `git mv`
- [ ] `scripts/build_blue_pill.py` and `scripts/route_blue_pill.py` no longer exist in `scripts/`
- [ ] `output/blue_pill.kicad_pcb`, `.kicad_pro`, `.kicad_prl` no longer exist in `output/`
- [ ] `baselines/4.6/README.md` exists with provenance (2026-03-06, Opus 4.6, 54/54 tests passing, owner-judged goal-failed, purpose for v2 stretch comparison)
- [ ] `docs/context/baselines.context.md` exists; mirrors README at module-boundary level
- [ ] `docs/context/routing-primitives.context.md` exists; documents routing_cli.py + routing/ + 45° rule + MCP-routing-BANNED
- [ ] `api_manifest.json` refreshed; `verified_count == total_count`; both > 0
- [ ] `docs/context/` contains exactly 5 files (render-pipeline, supplier-drc, contracts, baselines, routing-primitives)
- [ ] No new ruff/lint violations introduced

---

## Stage Integration Criteria (ALL batches done)
- [ ] All 4 batch checklists fulfilled (1.1 / 1.2 / 1.3 / 1.4)
- [ ] Full test suite green: `pytest -v` → all existing v1 tests + new Stage 1 tests pass (no regressions)
- [ ] Cross-module: `python scripts/render_board.py baselines/4.6/blue_pill.kicad_pcb` produces a PNG (proves render works against the demoted real-input fixture)
- [ ] Cross-module: `python -c "from scripts.supplier_drc import load_supplier_profile, emit_kicad_dru; from pathlib import Path; emit_kicad_dru(load_supplier_profile('jlcpcb'), Path('/tmp/integ.kicad_dru'))"` writes a parseable DRU
- [ ] `python scripts/verify_mcp.py` still exits 0 (no MCP regressions)
- [ ] `python scripts/verify_toolchain.py` exits 0 (cairosvg + lxml + GTK3 + kicad-cli all OK)
- [ ] `git status` shows clean working tree (all Stage 1 work committed)
- [ ] `docs/context/` contains 5 files (1 short of the final 6; the 6th is Stage 2 deliverable)
- [ ] `project_summary.md` updated with Stage 1 completion entry (scribe responsibility)
- [ ] Auditor has signed off on all items above with GREEN verdict
