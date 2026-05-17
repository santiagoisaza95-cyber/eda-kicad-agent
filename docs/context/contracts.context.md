# Contracts — Module Context

**Module:** `contracts/`
**Status:** Stage 1 Batch 1.3 deliverable (v2.0 foundation).
**Owners:** Per-board design contracts + per-stage orchestration contracts.

## Boundary

`contracts/` holds two distinct kinds of markdown files. They share a directory but serve different consumers and have different schemas:

| Kind | Filename pattern | Consumer | Lifecycle |
|------|------------------|----------|-----------|
| **Per-PCB design contract** | `<board_name>_contract.md` (e.g. `blue_pill_contract.md`, `blinker_555_contract.md`) | The PCB-design agent reads it as the single source of truth for one board (specs, components, netlist, success criteria). | Authored once per board; immutable during a build session; updated only between sessions. |
| **Per-stage orchestration contract** | `v2-stage-<N>-<slug>.contract.md` (e.g. `v2-stage-1-foundation.contract.md`) | The CTO/auditor/worker agents read it as the orchestration plan for one build stage (batches, deliverables, verification commands, completion criteria). | Authored once per stage; immutable during execution; the auditor grades against it. |

Files in `contracts/` are **always markdown**. No YAML, no JSON, no Python — those live elsewhere (`supplier_profiles/`, `api_manifest.json`, `scripts/`). Templates that bootstrap new contracts live alongside the real contracts (e.g. `EXAMPLE_CONTRACT.md`).

`contracts/` does NOT own:
- Skill / rule definitions — those live in `agent_docs/skills/` and `agent_docs/rules/`.
- Test code — `tests/test_<board>.py` lives in `tests/`, paired with but separate from the contract.
- Supplier DRC values — those live in `supplier_profiles/jlcpcb.yaml` and are referenced by metadata, not duplicated.
- Build output — `output/<board>.kicad_pcb` and per-checkpoint renders live in `output/`.

## Required Metadata Fields (Per-PCB Contracts)

Every per-PCB contract MUST begin with a YAML front-matter block containing **all six** fields below. Stage 1 supplier-DRC and visual-render machinery keys off these:

```yaml
---
supplier: jlcpcb              # required — names the profile loaded from supplier_profiles/<supplier>.yaml
layer_count: 2                # required — copper layer count; the test suite asserts this matches GetCopperLayerCount()
board_dimensions: 20x30 mm    # required — nominal WxH; tests assert bbox is within these + tolerance
fr4_thickness: 1.6 mm         # required — JLCPCB-standard thickness; documentation only (not DRC-checkable)
copper_weight: 1 oz           # required — documentation only
surface_finish: HASL (lead-free)  # required — documentation only; flags through to fab order
---
```

The `supplier:` field is the most load-bearing: it tells the agent which `supplier_profiles/*.yaml` to load and emit as `.kicad_dru` before routing. Changing `supplier: jlcpcb` to `supplier: pcbway` in a contract switches the entire DRC ruleset without touching the agent's code.

Stage-orchestration contracts have a different shape — they don't need this front-matter; they document batches, deliverables, and verification commands instead.

## "DESIGN FROM CONTRACT ONLY" Semantics

Every per-PCB contract MUST contain a verbatim heading **`## DESIGN FROM THIS CONTRACT ONLY`** (or, in v1 historical files, **`## CONSTRAINT: DESIGN FROM THIS CONTRACT ONLY`**) followed by an explicit list of what the agent must NOT use as inputs.

This clause exists because v2's central hypothesis is that the agent should produce a credible design **from the contract alone** — without WebSearch, reference images, or peeking at existing implementations. Crutches mask whether the architecture (visual feedback + iterative checkpoints + supplier-anchored DRC + Opus 4.7) is actually sufficient.

The clause typically forbids:
- `WebSearch` / `WebFetch` lookups for pinouts, layouts, or schematics related to the board
- Reading any file in `reference/`
- Reading other boards' implementations (e.g. `baselines/4.6/blue_pill.kicad_pcb`) for "inspiration"
- Browsing the web for similar designs

…and explicitly allows:
- This contract
- `agent_docs/skills/` and `agent_docs/rules/`
- `supplier_profiles/<supplier>.yaml` (loaded via the front-matter metadata)
- `api_manifest.json`
- MCP tools (except the banned routing tools)
- `scripts/routing_cli.py` for actual routing

The auditor verifies the clause is present at Stage 1 (existence check) and again at Stage 3 audition (the agent's journal must show no forbidden tool usage during the build).

If the owner decides that purity is too restrictive (P7 in the architecture proposal — currently deferred), a future v2.x extension will allow optional reference images per contract. v2.0 keeps the clause hard.

## How to Add a New Board Contract

1. **Copy the template.** Start from `contracts/EXAMPLE_CONTRACT.md` — it has the canonical structure (specs, components table, netlist, design rules, verification commands, completion criteria).
2. **Author YAML front-matter.** Fill in all six required metadata fields. Pick a supplier whose profile exists in `supplier_profiles/` (currently: `jlcpcb`).
3. **Add the DESIGN FROM THIS CONTRACT ONLY clause** immediately after the title.
4. **List components in a table** with columns: Ref, Value, Footprint, Purpose. Use KiCad-canonical footprint names (e.g. `Capacitor_SMD:C_0603_1608Metric`, `Package_DIP:DIP-8_W7.62mm`).
5. **List nets in a table** with columns: Net Name, Connected Pins. Pins use `<Ref>.<PinNumber>` notation (e.g. `U1.8`, `J1.2`).
6. **Reference the supplier profile for design rules** — do NOT duplicate clearance/trace-width values. Cite `supplier_profiles/jlcpcb.yaml` instead.
7. **Write Success Criteria** as a markdown checklist covering at minimum: DRC 0/0, connectivity, components on F.Cu, dimensions, and an owner-credible visual judgment item.
8. **Pair with a test file.** Create `tests/test_<board>.py` mirroring `tests/test_blinker_555.py` (the 5 named tests: `test_component_count`, `test_nets_routed`, `test_drc_zero`, `test_dimensions`, `test_components_on_f_cu`).
9. **Verify collection.** Run `pytest tests/test_<board>.py --collect-only` — tests must collect cleanly even before the board is built (they SKIP until `output/<board>.kicad_pcb` exists).

The contract is parseable by the agent if all four of these succeed:
- `grep "supplier:" contracts/<board>_contract.md` → matches the YAML front-matter
- `grep "DESIGN FROM THIS CONTRACT ONLY" contracts/<board>_contract.md` → at least one match
- `pytest tests/test_<board>.py --collect-only` → enumerates tests without import errors
- `cat contracts/<board>_contract.md` shows a Success Criteria checklist with ≥ 5 items

After audition, the auditor grades the build against the Success Criteria — that's the gate for declaring the contract complete.
