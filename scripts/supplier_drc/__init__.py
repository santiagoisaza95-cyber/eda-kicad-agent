"""Supplier DRC subsystem: profile loading and KiCad DRU emission.

Public API:
- `load_supplier_profile(name)` -> `SupplierProfile`
- `emit_kicad_dru(profile, out_path)` -> `Path`

See `docs/context/supplier-drc.context.md` for the module boundary.
"""

from scripts.supplier_drc.loader import emit_kicad_dru, load_supplier_profile

__all__ = ["load_supplier_profile", "emit_kicad_dru"]
