# Phase 2: Technology Mapping Report — AGREED
Date: 2026-05-16
Project: eda-kicad-agent v2 (redesign)

## Decisions
1. **Render stack:** kicad-cli SVG export + cairosvg PNG conversion + lxml background injection. Layers: Edge_Cuts, B.Cu, F.Cu, F.Mask, F.SilkS. Default 150 DPI, dark BG (#1a1a1a). Two views per checkpoint (full + copper-only). Sub-2 s budget.
2. **Render dependencies:** cairosvg, lxml (pip) + GTK3 runtime (Chocolatey).
3. **Supplier DRC schema:** YAML with extensible `suppliers:` map + Pydantic validation. JLCPCB profile populated for v2.0.
4. **KiCad integration:** emit `.kicad_dru` from profile loader; known gaps for solder mask clearance (UI-only), non-plated holes (external check), thickness/copper weight (metadata).
5. **Critique loop pattern:** Self-Refine (per-checkpoint) + Reflexion (cross-checkpoint within session) + CoVe (verification). Max 3 iter/checkpoint, ~12K tokens/cycle.
6. **Three new skill files** + **one new rule file** to add to `agent_docs/`.
7. **Five anti-patterns** named with explicit detection rules.

## Raw Outputs

### Three Phase 2 research streams completed

| Stream | Output | Saved to |
|---|---|---|
| Supplier DRC rules + schema | JLCPCB rules table, YAML schema (extensible), KiCad DRU mapping, supplier comparator, risk callouts | `research/supplier_drc_research.md` |
| Rendering toolchain | kicad-cli SVG + cairosvg pipeline, layer composition, render_board() function design, speed budget | `research/rendering_toolchain_research.md` |
| Self-critique patterns | Self-Refine + Reflexion hybrid, skill file scaffolding, convergence numbers, failure-mode catalog, anti-patterns | `research/self_critique_patterns_research.md` |

### Technology Mapping Report

| Category | Choice | Performance Edge | Maturity | Capability Score | Justification |
|---|---|---|---|---|---|
| **PCB→PNG render** | `kicad-cli pcb export svg --mode-single` + `cairosvg.svg2png(scale=dpi/96)` + `lxml` background injection | ~1.3 s end-to-end at 150 DPI; meets <2 s budget. Faster than PLOT_CONTROLLER on Windows; faster than Playwright; lighter than Wand. | Mature | 5 | Lowest-friction Python+Windows path. KiCad CLI is the supported export surface; cairosvg is the default in the Python+SVG world. lxml for surgical SVG mutation. |
| **Render dependencies** | `cairosvg>=2.7.0`, `lxml>=5.0.0` (Python); `gtk3-runtime-bin-x64` (system, via Chocolatey) | n/a | Mature | 5 | Documented installer path; Chocolatey one-liner. Alternative manual GTK install path for non-Choco users. |
| **Layer composition for visual judgment** | `Edge_Cuts, B.Cu, F.Cu, F.Mask, F.SilkS` composited in single SVG, default KiCad palette, dark background (#1a1a1a) | n/a | Mature | 5 | Default KiCad palette already distinguishes F.Cu/B.Cu/SilkS/Edge_Cuts. Dark BG matches KiCad UI; better contrast for vision model. |
| **Multi-view strategy** | Per checkpoint: `<board>_full.png` (all 5 layers) + `<board>_copper.png` (F.Cu+B.Cu only). Components view deferred. | ~2.0 s for both renders sequential | — | 4 | Two views catch routing-specific issues without an N=5 explosion. |
| **Supplier DRC schema** | YAML with extensible `suppliers:` map, `metadata` + grouped `design_rules` (trace, via, pad, solder_mask, silkscreen, board, cost_premiums). Validate with Pydantic. | Schema-first lets new fabs plug in without rework — owner-mandated extensibility | New (internal) | 5 | YAML matches v1 repo conventions (configs are JSON, but YAML is more readable for nested rules). Pydantic gives type-checked load + clear error messages. |
| **Primary supplier profile** | JLCPCB populated for v2.0 (trace/space 0.127 mm = 5 mil; via 0.6/0.3 mm; copper-to-edge 0.3 mm; annular ring 0.15 mm; silk 0.15 mm line / 1.0 mm text) | Most common low-cost fab; published spec is comprehensive | Mature | 5 | Owner's pick. Schema accommodates PCBWay / OSH Park / Eurocircuits as future profiles. |
| **KiCad DRC integration** | Emit `<board>.kicad_dru` from loaded supplier profile via `emit_kicad_dru(profile, path)`. Most rules expressible in DRU syntax. | Native KiCad enforcement; no custom Python re-checker needed | Mature | 4 | Gaps: solder mask clearance is UI-only (set globally in BOARD_DESIGN_SETTINGS, not DRU); non-plated holes need external script; board thickness/copper weight are metadata. |
| **Critique loop pattern** | Self-Refine (Madaan 2023) per-checkpoint + Reflexion (Shinn 2023) episodic memory across checkpoints + CoVe for verification steps | Empirically ~20% improvement over single-shot generation; well-documented agentic pattern | Mature | 5 | These are the most established patterns in the agentic-design literature; directly applicable to render → critique → refine. |
| **Loop limits** | Max 3 iterations per checkpoint; ~12K token budget per critique cycle; convergence rule = monotonic issue count ↓ AND monotonic confidence ↑ | Avoids thrashing (>3 iter) and runaway token cost (>15K/cycle) | — | 5 | Numbers based on Self-Refine literature + PCB determinism. Iter 4+ historically causes oscillation. |
| **Anti-pattern detection** | Track per-iter: issue_count_delta, confidence, modifications_applied, new_issues_introduced. Escalate on rubber-stamping, thrashing, over-correction, early escalation, local optimum trap. | Catches the 5 named failure modes before they burn cycles | — | 5 | Explicit detection cheaper than waiting for failed audition. |
| **Skill files (new)** | `agent_docs/skills/visual-review-skill.md`, `agent_docs/skills/iterative-refinement-skill.md`, `agent_docs/skills/self-critique-skill.md` | n/a | New (internal) | 5 | Three new skills; scaffolds already designed in research. |
| **Rule file (new)** | `agent_docs/rules/supplier-drc-rules.md` — mandatory rule: pick supplier from contract, load profile, emit DRU, validate before routing | n/a | New (internal) | 5 | Aligns with v1's rules/skills split (hard rule = mandatory; skill = workflow). |

### Implementation-ready function signatures (from research)

```python
# scripts/render_board.py
def render_board(
    pcb_path: Path,
    output_dir: Optional[Path] = None,
    layers: Optional[list[str]] = None,
    dpi: int = 150,
    generate_variants: bool = True
) -> dict[str, Path]:
    """Returns {'full': PNG path, 'copper': PNG path | None, 'svg': SVG path}"""

# scripts/supplier_drc/loader.py
def load_supplier_profile(name: str) -> SupplierProfile:
    """Pydantic-validated supplier rule set."""

def emit_kicad_dru(profile: SupplierProfile, out_path: Path) -> Path:
    """Writes .kicad_dru file consumable by KiCad."""
```

## User Feedback
Owner approved all selections as recommended. No pushback.

## Cross-Phase Consistency Check
✓ Phase 0 Medium-size classification (3 stages) still holds — the three new subsystems map cleanly onto Stage 1 (foundation: render + supplier-DRC) and Stage 2 (iterative build + critique skills) and Stage 3 (audition).
✓ Phase 1 decisions all carry through:
  - Render = kicad-cli + cairosvg ✓
  - Hybrid judge = visual-review-skill (agent self-critique) + 3 human milestones — confirmed; the three skill files implement the self-critique side
  - Supplier scope = JLCPCB primary, schema-first — confirmed; YAML schema design supports extensibility
  - No reference image — confirmed; visual loop is intra-build, not contract-bundled
✓ No contradictions found across Phase 0, Phase 1, Phase 2.

## Revision History
(none yet)
