[Created by Codex: 019a9cf1-5108-7a41-8ef2-eb7f1ee6f9d3]

# Basic smoke test strategy

When requirements call for “smoke testing only,” every coding agent must follow this exact harness:

1. Start from a clean log directory whose name ends with the last five characters of the current agent id. For this session the suffix is `6f9d3`, so the directory is `/tmp/coder-agent-6f9d3`.
2. Always begin the run by deleting the directory to avoid mixing logs between attempts:

   ```
   rm -rf /tmp/coder-agent-6f9d3
   ```

3. Run the Codex exec harness with the dedicated `--log-dir` and your smoke-test prompt. Example (replace `{prompt}` with the scenario-specific text):

   ```
   codex --log-dir /tmp/coder-agent-6f9d3 exec "{prompt}"
   ```

4. After Codex finishes, inspect `/tmp/coder-agent-6f9d3` (especially `sse_lines.jsonl`, `sessions.jsonl`, and `requests/`) to validate behavior.

Guidelines:

- Prefer simple prompts unless the feature under test requires specific reasoning output.
- Do not launch the TUI for smoke tests; `codex exec` avoids blocking sessions and keeps logs deterministic.
- When multiple smoke runs are needed, repeat the delete + exec steps each time so the log folder stays isolated.

Every future requirement doc must reference this strategy whenever smoke tests are requested. Implementation work should cite this file explicitly in the “Smoke tests” or “Validation” section so coder and tester agents share the same harness.

[Created by Codex: 019a9cf1-5108-7a41-8ef2-eb7f1ee6f9d3]
