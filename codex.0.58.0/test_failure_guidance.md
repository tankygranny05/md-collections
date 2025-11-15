[Created by Codex: 019a822d-6085-7c73-9c90-d4bea7f0af00]

# Test failure guidance – tmux vs direct shell

We hit a noisy distinction between running `cargo test -p codex-core` directly from the CLI vs inside a dedicated tmux session. Outside tmux the process inherited many open file descriptors from the main Codex CLI shell, so the test harness tripped macOS’ `EMFILE` limit when Wiremock/Tokio tried to stand up their local servers (`Os { code: 24, message: "Too many open files" }`). Those panics made dozens of suite tests fail even though the code itself was fine.

Running the identical command inside tmux eliminated the descriptor contention, so only the real regression (`suite::approvals::approval_matrix_covers_all_modes`) remained. The sandbox policy allowed `/tmp` writes on the first attempt, so the “OnFailure” scenario never produced an approval prompt and the assertion failed legitimately.

**Guidance**

1. Always run core test suites inside tmux (see tester doc update) so the test process owns its descriptor table.
2. If you see `Too many open files`, capture the tmux log and re-run inside a fresh tmux session named with your agent suffix (details below) before assuming the code regressed.
3. Keep the `/tmp` sandbox nuance in mind: if tests expect a write failure outside the workspace, ensure `/tmp` is either excluded or not the repo root; otherwise, approvals will appear to bypass escalation.

[Created by Codex: 019a822d-6085-7c73-9c90-d4bea7f0af00]
