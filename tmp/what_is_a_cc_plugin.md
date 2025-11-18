# What's a Claude Code Plugin?

A **plugin** is a **modular extension package** for Claude Code that adds custom functionality. Think of it like a VSCode extension or a browser plugin, but for Claude Code.

## 🎯 What Can Plugins Contain?

A plugin can bundle together any combination of these components:

### 1. **Slash Commands** (`/command-name`)
Custom commands you can invoke in the chat
```bash
/feature-dev    # Guided feature development workflow
/commit         # Create git commit
/code-review    # Review a pull request
```

### 2. **Agents** (Specialized AI workers)
Custom agents with specific instructions for specialized tasks
- `code-explorer` - Analyzes existing codebase
- `code-architect` - Designs feature architecture
- `code-reviewer` - Reviews code quality

### 3. **Hooks** (Event listeners)
Code that runs when certain events happen
- **PreToolUse**: Before Claude uses a tool (e.g., before running bash command)
- **PostToolUse**: After Claude uses a tool
- **Stop**: Before Claude stops working
- **UserPromptSubmit**: When you submit a message

### 4. **Skills** (Knowledge modules)
Specialized knowledge/instructions for specific tasks
- `frontend-design` - How to create beautiful UIs
- `writing-rules` - How to write hookify rules

### 5. **MCP Servers** (External integrations)
Model Context Protocol servers for external tool integration

### 6. **Output Styles** (Formatting)
Custom ways to format Claude's responses

---

## 📦 Plugin Structure

Every plugin has this structure:

```
my-plugin/
├── .claude-plugin/
│   └── plugin.json          # Metadata (name, version, author)
├── commands/                 # Slash commands (optional)
│   └── my-command.md
├── agents/                   # Custom agents (optional)
│   └── my-agent.md
├── hooks/                    # Event hooks (optional)
│   └── pretooluse.py
├── skills/                   # Knowledge modules (optional)
│   └── my-skill/
│       └── SKILL.md
└── README.md                # Documentation
```

---

## 🔍 Real Example: `hookify` Plugin

Let me show you a complete plugin structure:

```
hookify/
├── .claude-plugin/
│   └── plugin.json          # Name: "hookify", v0.1.0
│
├── commands/                # 4 slash commands:
│   ├── hookify.md           # /hookify - Create a new rule
│   ├── configure.md         # /hookify-configure
│   ├── help.md              # /hookify-help
│   └── list.md              # /hookify-list
│
├── agents/                  # 1 agent:
│   └── conversation-analyzer.md  # Analyzes patterns
│
├── hooks/                   # 4 event hooks:
│   ├── pretooluse.py        # Check before tools run
│   ├── posttooluse.py       # Check after tools run
│   ├── stop.py              # Check before stopping
│   └── userpromptsubmit.py  # Check user prompts
│
├── skills/                  # 1 skill:
│   └── writing-rules/       # Teaches how to write rules
│       └── SKILL.md
│
├── examples/                # Example rule files
│   ├── dangerous-rm.local.md
│   └── console-log-warning.local.md
│
└── core/                    # Python code
    ├── config_loader.py
    └── rule_engine.py
```

**What hookify does:**
- Monitors your conversation with Claude
- Checks for patterns you define (like `rm -rf` or `console.log`)
- Warns or blocks operations based on rules you create
- Helps prevent mistakes before they happen

---

## 🆚 Plugins vs Skills

| **Plugin** | **Skill** |
|------------|-----------|
| A package/bundle | A single knowledge module |
| Can contain: commands, agents, hooks, skills, etc. | Just instructions for Claude |
| Installed as a unit | Can be part of a plugin |
| Example: `hookify` plugin | Example: `frontend-design` skill |

**Analogy:**
- **Plugin** = VSCode Extension (full package)
- **Skill** = Code snippet (one specific thing)

---

## 💡 Examples from the Repo

### Simple Plugin: `frontend-design`
```
frontend-design/
├── .claude-plugin/plugin.json
├── skills/frontend-design/SKILL.md  # Just 1 skill
└── README.md
```
**Does**: Teaches Claude how to design beautiful UIs

### Complex Plugin: `feature-dev`
```
feature-dev/
├── .claude-plugin/plugin.json
├── commands/feature-dev.md          # 1 command
├── agents/                          # 3 agents
│   ├── code-explorer.md
│   ├── code-architect.md
│   └── code-reviewer.md
└── README.md
```
**Does**: 7-phase workflow for building features (exploration → architecture → implementation → review)

### Very Complex Plugin: `hookify`
```
hookify/
├── .claude-plugin/plugin.json
├── commands/          # 4 commands
├── agents/            # 1 agent
├── hooks/             # 4 hooks
├── skills/            # 1 skill
├── examples/          # Example files
└── core/              # Python code
```
**Does**: Pattern matching and behavior enforcement

---

## 🎁 Why Use Plugins?

1. **Reusability**: Share workflows across projects
2. **Modularity**: Install only what you need
3. **Team consistency**: Everyone uses same commands/agents
4. **Extensibility**: Build custom functionality
5. **Shareability**: Distribute via marketplace

---

## Summary

**A plugin is a packaged extension for Claude Code that can bundle:**
- Slash commands (`/command`)
- Specialized agents
- Event hooks
- Skills (knowledge)
- MCP servers
- Output styles

**Think of it as:** An app for Claude Code that adds new capabilities!

---

**[Created by Claude: 0ecc17a2-0ac2-4db8-b89e-78c39bcc28e6]**
