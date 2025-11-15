[Edited by Codex: 019a831a-80db-70c0-993c-4be61d23f406]

# Showing the session banner immediately

This guide documents how to render the `<status>` banner (the bordered panel that shows version/model/directory) the moment the TUI starts rather than waiting for the first `SessionConfigured` event.

## Overview

1. **Capture the expected header locally.** Create a shared `SessionHeaderSnapshot` from the initial `Config` so the UI knows the model, reasoning effort, directory, and `env!("CARGO_PKG_VERSION")` without waiting on the server.
2. **Emit the banner at construction time.** Call `new_live_session_info(shared_header.clone())` inside `ChatWidget::new`/`new_from_existing` immediately after struct initialization and before returning the widget.
3. **Update shared state when the session config arrives.** When `SessionConfigured` is received, update the shared `SessionHeader` fields (`set_model`, `set_reasoning_effort`) so future banners (e.g., `/status`) reflect any server-side adjustments without re-rendering the initial cell.

## Detailed steps

### 1. Shared session header state

- Add a `SessionHeaderSnapshot` struct that stores the banner data.
- Wrap it in an `Arc<RwLock<_>>` and expose getters/setters (`shared`, `set_model`, `set_reasoning_effort`).
- Existing banner rendering (`SessionHeaderHistoryCell`) should read from this shared snapshot so any consumer (initial banner or `/status`) stays consistent.

### 2. Immediate banner emission

In `ChatWidget::new`:

```rust
let mut this = Self { ... };
this.maybe_emit_initial_session_banner();
this
```

Where `maybe_emit_initial_session_banner` checks `show_welcome_banner` and enqueues:

```rust
self.add_to_history(history_cell::new_live_session_info(
    self.session_header.shared(),
));
```

This pushes the same header/help cell that would normally appear after the first event, so the user sees the status block before typing anything.

### 3. SessionConfigured synchronization

Inside `on_session_configured`:

- Call `self.session_header.set_model(&event.model);`
- Call `self.session_header.set_reasoning_effort(event.reasoning_effort);`

This keeps the shared snapshot aligned with what the backend ultimately negotiated (e.g., if the server swaps models or reasoning levels).

### 4. Subsequent banners (`/status`, resume)

All call sites that render the banner (`new_session_info`, `new_status_output`) now read from a shared snapshot, so they automatically pick up the latest state without extra work.

## Testing

1. `cargo test -p codex-tui` to verify snapshot tests.
2. Launch the TUI and confirm the banner appears before the first prompt area updates.
3. Trigger `/status` to verify it reuses the shared snapshot and shows updated reasoning/model if the session changes.
