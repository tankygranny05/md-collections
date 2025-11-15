# [Edited by 019a7288-1f3d-7a62-9461-b7fb2aa3dfe4]
"""
Template for parsing SSE (Server-Sent Events) JSONL logs with centralized
resources, color coding, and verification logic.

When using this template, agents should try NOT to copy all the dos strings
and comments verbatism. The added strings' purposes are only to demonstrate
how to use this template.

Centralization Strategy
----------------------
- Single-file projects: Define COLORS, CONSTANTS, RESOURCES, and Adapters as
  static classes in this module. Keep all I/O and configuration centralized.
- Multi-file projects: Prefer a single shared config module that defines
  COLORS/CONSTANTS/RESOURCES/Adapters and import them across files.
- Larger projects: Each class can be promoted to its own module
  (e.g., colors.py, constants.py, resources.py, adapters.py) while preserving
  the same responsibilities and boundaries.

Principles
----------
- Centralize color codes in COLORS.
- Centralize magic numbers/strings in CONSTANTS.
- Centralize file paths/resources in RESOURCES.
- Centralize I/O operations in Adapters.
- Centralize verification logic in Verifier.
- Always use COLORS when printing, with a label that identifies the code
  origin (class and function), e.g. TopLevel.main.

Print Style Guide
-----------------
- For multi-line prints, prefer string continuation style:
      print(f"{label} Found {COLORS.HIGHLIGHT}{len(url_list):,}{COLORS.RESET} "
            f"unique URLs.")
  rather than wrapping in parentheses. This keeps prints visually distinct from
  function calls and makes log scanning easier.
- Include a label prefix showing the code origin. Example used in this file:
      label = (f"{COLORS.LABEL_CLASS}TopLevel{COLORS.RESET}."
               f"{COLORS.LABEL_FUNC}main{COLORS.RESET}:")
      print(f"{label} Found ...")
"""

import os
from lib.utilities import U
import pandas as pd
import json


class RESOURCES:
    """
    Centralized file paths and external resources.

    Define all file paths, URLs, and external resources here. Use
    os.path.expanduser() when paths include '~'. In multi-file projects,
    prefer a single shared module that defines RESOURCES and import it
    everywhere to avoid duplication and drift.
    """
    CENTRALIZED_LOG_FN = "/tmp/log-dir2/sse_lines.jsonl"


class CONSTANTS:
    """
    SESSION METADATA FORMAT:
    ------------------------
    This section captures the user's color preferences wrt printed logs of agents'
    sessions. This must be strictly followed for consistent aesthetic across apps.

    Sample session meta-data print format:
        [s:2b856 (#17) f:20184 (#18) c:0.25k 2025-11-11 17:07:03]

    Format breakdown:
        s:2b856 means session_id: ...2b856 (last N chars, see COMPACT_IDS)
        f:20184 means flow_id   : ...20184 (last N chars, see COMPACT_IDS)
        c:0.25k means current context window = 250 tokens (0.25k)
        (#17) means session counter (17th session in this run)
        (#18) means flow counter (18th flow in this session)

    The number of characters displayed can be set with --compact-ids,
    default is 5. Any value > 10 displays full UUIDs (36 characters).
    """
    UUID_LENGTH = 36
    IGNORED_URLS = 'https://proxycodeclaude.mellot-jules.workers.dev/v1/messages?beta=true',


class COLORS:
    """
    Centralized ANSI color codes and print conventions.

    All outputs should use these colors for consistent styling and to make
    code-origin labeling obvious in logs. Top-level functions can use a
    "TopLevel" label, while class methods should include the class and method
    names in the label for traceability.

        SESSION METADATA FORMAT:
    ------------------------
    This section captures the user's color preferences wrt printed logs of agents'
    sessions. This must be strictly followed for consistent aesthetic across apps.

    Sample session meta-data print format:
        [s:2b856 (#17) f:20184 (#18) c:0.25k 2025-11-11 17:07:03]

    Format breakdown:
        s:2b856 means session_id: ...2b856 (last N chars, see COMPACT_IDS)
        f:20184 means flow_id   : ...20184 (last N chars, see COMPACT_IDS)
        c:0.25k means current context window = 250 tokens (0.25k)
        (#17) means session counter (17th session in this run)
        (#18) means flow counter (18th flow in this session)

    The number of characters displayed can be set with --compact-ids,
    default is 5. Any value > 10 displays full UUIDs (36 characters).
    """
    HIGHLIGHT = "\x1b[93m"
    RESET = "\x1b[0m"
    DIM = "\x1b[90m"
    FILENAME = "\x1b[96m"
    LABEL_CLASS = "\x1b[36m"
    LABEL_FUNC = "\x1b[90m"
    SUCCESS = "\x1b[92m"
    FAILURE = "\x1b[91m"

    #   This section captures the user's color preferences wrt printed logs of agents'
    # sessions. This should be strictly followed for consistent aesthetic across apps.

    REASONING_HEADER = "\x1b[36m"
    REASONING_CONTENT = "\x1b[96m"
    ASSISTANT_TEXT = "\x1b[95m"
    USER_PROMPT = "\x1b[33m"
    SESSION_METADATA = "\x1b[90m" # e.g. [s:2b856 (#17) f:20184 (#18) c:0.25k 2025-11-11 17:07:03]
    FUNC_CALL = "\x1b92m" # jsons and partial jsons


class DataVerifications:
    """
    Static verification utilities.

    Keep data-quality checks centralized here so that validation logic remains
    clear and consistent for all agents and scripts.
    """
    @staticmethod
    def verify_that_all_line_starts_with_correct_prefix(data_df):
        """
        Assert every row's 'line' value starts with the 'data: ' prefix.

        Args:
            data_df (pd.DataFrame): DataFrame with a 'line' column.

        Raises:
            AssertionError: If any row fails the prefix check.
        """
        label = (f"{COLORS.LABEL_CLASS}DataVerfifications{COLORS.RESET}."
                 f"{COLORS.LABEL_FUNC}verify_that_all_line_starts_with_correct_prefix"
                 f"{COLORS.RESET}: "
                 f"Running tests for dataframe with {len(data_df):,} rows...")
        print(label, end=" ")
        count = data_df['line'].map(lambda x: x.startswith('data: ')).sum()
        assert len(data_df) == count, (
            f"Sai, Expected all lines to start with 'data: ', "
            f"but found {count} lines that don't."
        )
        print(f"{COLORS.SUCCESS}SUCCEEDED!{COLORS.RESET}")


class Adapters:
    """
    Centralized data loading and persistence entry points.

    All I/O should go through this class to keep data access patterns
    consistent. In multi-file repositories, prefer exposing this class from
    a shared module and import it elsewhere to avoid divergence.
    """
    @staticmethod
    def load_data():
        """
        Load raw SSE lines from the centralized JSONL file.

        Returns:
            list[str]: Raw JSONL lines as strings, one per event.
        """
        fn = os.path.expanduser(RESOURCES.CENTRALIZED_LOG_FN)
        U.set_pd_display_options()
        with open(fn, "r") as f:
            lines = f.readlines()
        label = (f"{COLORS.LABEL_CLASS}Adapters{COLORS.RESET}."
                 f"{COLORS.LABEL_FUNC}load_data{COLORS.RESET}")
        print(f"{label}: "
              f"Loaded {COLORS.HIGHLIGHT}{len(lines):,}{COLORS.RESET} lines from "
              f"{COLORS.FILENAME}{fn}{COLORS.RESET}")

        return lines


def main():
    """
    Demonstrate the centralized structure for agents.

    Steps:
    1) Load data via Adapters
    2) Parse and filter using CONSTANTS
    3) Verify using Verifier
    4) Print results using COLORS with labeled prefixes
    """
    raw_lines = Adapters.load_data()
    raw_data_df = pd.DataFrame(map(json.loads, raw_lines))

    agent_sessions_df = (
        raw_data_df[raw_data_df['sid'].map(len) == CONSTANTS.UUID_LENGTH]
    )
    list(sorted(agent_sessions_df['event'].unique()))
    agent_sessions_df = (
        agent_sessions_df[~agent_sessions_df['url']
            .isin(CONSTANTS.IGNORED_URLS)])
    agent_sessions_df = agent_sessions_df.reset_index(drop=True)
    DataVerifications.verify_that_all_line_starts_with_correct_prefix(
        data_df=agent_sessions_df
    )
    label = (
        f"{COLORS.LABEL_CLASS}TopLevel{COLORS.RESET}."
        f"{COLORS.LABEL_FUNC}main{COLORS.RESET}:")

    session_id_list = agent_sessions_df['sid'].unique().tolist()
    print(f"{label} Found {COLORS.HIGHLIGHT}{len(session_id_list):,}"
          f"{COLORS.RESET} unique sessions.")
    flow_id_list = agent_sessions_df['flow_id'].unique().tolist()
    print(f"{label} Found {COLORS.HIGHLIGHT}{len(flow_id_list):,}"
          f"{COLORS.RESET} unique flows.")


if __name__ == "__main__":
    main()

# Co-authored by [Claude: e544228f-21b7-4f7d-a993-741c3742b856]
# [Edited by 019a7288-1f3d-7a62-9461-b7fb2aa3dfe4]
