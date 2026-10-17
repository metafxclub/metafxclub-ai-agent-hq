# Male Roster Set A Review Notes

- Source image has real alpha transparency and separates cleanly into 10 connected character components.
- These outputs are production-usable as static agent sprites with CSS walking/idle motion.
- Limitation: they are not yet directional walk-cycle sheets. Runtime marks them as `static-alpha-crop` and uses visual walking movement/bob.
- Next asset upgrade: generate per-role directional walk/status frames and keep the same `agent_id` values.
