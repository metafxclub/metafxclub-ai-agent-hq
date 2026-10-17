# Manager Exec v001 Asset Review Notes

Project: Metafxclub AI Pixel HQ
Asset ID: manager-exec-v001
Agent role: manager
Variant: exec
Version: v001
Review date: 2026-06-09

## Summary

This asset package is ready for map runtime animation and status pose switching.

The package contains a complete 4-direction walk cycle and a complete 12-state status pose set. All runtime frames were verified as 192x192 PNG files with RGBA transparency preserved.

## Folder Structure

Expected folders are present:

- `source/`
- `frames/walk/`
- `frames/status/`
- `registry/`

Current registry files:

- `registry/sprite-registry.json`
- `registry/animation-map.json`
- `registry/review-notes.md`

## Walk Frames

Walk frames verified: 16 / 16

Directions:

- `down`: 4 frames
- `left`: 4 frames
- `right`: 4 frames
- `up`: 4 frames

Expected filename pattern:

```text
agent-manager-exec-walk-{direction}-{frame_number}-192-v001.png
```

All expected walk frame filenames are present.

## Status Frames

Status frames verified: 12 / 12

Statuses:

- `idle`
- `resting`
- `planning`
- `meeting`
- `working`
- `waiting`
- `waiting_approval`
- `blocked`
- `reporting`
- `completed`
- `archived`
- `offline_sleep`

Expected filename pattern:

```text
agent-manager-exec-status-{status_slug}-192-v001.png
```

All expected status frame filenames are present.

## Image Validation

All runtime frame PNG files passed:

- Size: `192x192`
- Mode: `RGBA`
- Transparent alpha preserved
- No blank alpha frames detected
- No frame touches the image edge
- No resize was required during validation

Source sheets:

- `source/agent-manager-exec-walk-sheet-192-v001.png`
- `source/agent-manager-exec-status-sheet-192-v001.png`

## Runtime Registry Validation

`animation-map.json` passed runtime path validation.

It contains:

- `walk.down`
- `walk.left`
- `walk.right`
- `walk.up`
- `status.idle`
- `status.resting`
- `status.planning`
- `status.meeting`
- `status.working`
- `status.waiting`
- `status.waiting_approval`
- `status.blocked`
- `status.reporting`
- `status.completed`
- `status.archived`
- `status.offline_sleep`

All PNG paths in `animation-map.json` point to existing files inside this asset package.

## Notes For Runtime Integration

Use `registry/animation-map.json` as the primary runtime entry point.

Recommended runtime behavior:

- Use `walk.{direction}` frames while `agent.status` is `walking`.
- Use `status.{status}` image when the agent is not walking.
- If a status pose is missing in future variants, fallback to `status.idle`.
- Keep the sprite anchored at the bottom foot point when placing it on the map.
- Do not use GIF as the runtime asset. GIF may be used only as a preview.

## Known Handoff Notes

`sprite-registry.json` includes `original_input` references to the source generation folder under `outputs/`. Those original references are useful for audit history, but runtime should use the local package paths under `source/`, `frames/`, and `registry/`.

This package currently covers map walk animation and status poses. If NPC dialogue mode is required, add a portrait folder:

```text
portrait/
  agent-manager-exec-portrait-dialogue-v001.png
```

Then update `sprite-registry.json` with the portrait path.

## Handoff Status

Runtime animation handoff: ready

NPC dialogue portrait handoff: pending portrait copy/update

Recommended next step:

Integrate `registry/animation-map.json` into the Metafxclub AI Pixel HQ frontend animation controller.
