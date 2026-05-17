# Supplier Profiles

YAML files in this directory describe each supported PCB manufacturer's design-rule envelope (trace widths, via tiers, mask clearances, board sizes, cost premiums). Files are validated at load time against `supplier_profiles/schema.py` and emitted to KiCad `.kicad_dru` rule files by `scripts/supplier_drc/loader.py`.

## Current profiles

- `jlcpcb.yaml` — JLCPCB 2-layer FR4 (standard tier).

## Adding a new supplier

1. Copy `jlcpcb.yaml` to `<vendor>.yaml` (e.g. `pcbway.yaml`, `oshpark.yaml`).
2. Update `metadata` block: `name`, `capability_tier`, `last_updated` (ISO date), `source_url` (the official capability page you sourced numbers from).
3. Replace every rule value with the new supplier's specification. Keep the `unit` field explicit on every rule axis — the schema rejects unitless values.
4. Add at minimum the three required rule sections per the schema (`trace_rules`, `via_rules`, `pad_rules`, `solder_mask_rules`, `silkscreen_rules`, `board_rules`). Optional `cost_premiums` only carries if the vendor publishes a cost-tier table.
5. Validate at the command line:
   ```
   python -c "from scripts.supplier_drc import load_supplier_profile; print(load_supplier_profile('<vendor>').metadata.name)"
   ```
   A `pydantic.ValidationError` here means the YAML doesn't match the schema — fix the YAML before committing.
6. Emit a DRU and inspect it in KiCad pcbnew (`Board Setup -> Design Rules -> Custom Rules`):
   ```
   python -c "from pathlib import Path; from scripts.supplier_drc import load_supplier_profile, emit_kicad_dru; emit_kicad_dru(load_supplier_profile('<vendor>'), Path('/tmp/<vendor>.kicad_dru'))"
   ```
7. Reference the new profile from a board contract by setting `supplier: <vendor>` in its YAML front-matter. Agent rule `agent_docs/rules/supplier-drc-rules.md` wires the rest.

## Documented limitations

Three axes are NOT enforceable as DRU rules and are emitted as inline `#` comments at the top of the DRU file:

- Solder mask clearance — native KiCad UI setting only.
- Non-plated hole minimum — external validator (`scripts/supplier_drc/validators.py`), v2.x.
- Board thickness / copper weight — metadata only, not DRC-checkable.

See `docs/context/supplier-drc.context.md` for the module boundary.
