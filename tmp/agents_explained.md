# Built-in Agents vs Custom Agents (Subagents) Explained

## TL;DR

- **Built-in agents**: 3 hardcoded agents (general-purpose, Explore, Plan) built into cli.js
- **Custom agents**: User-created agents in `.claude/agents/` directory (your own subagents!)
- **YES**: When you create custom agents, the main agent can use them via the Task tool!

---

## 1. Built-in Agents (Hardcoded in cli.js)

These are the **3 agents built into Claude Code**:

### 🔵 general-purpose
```yaml
agentType: general-purpose
model: sonnet
tools: * (all tools)
whenToUse: |
  General-purpose agent for researching complex questions, searching 
  for code, and executing multi-step tasks. When you are searching for 
  a keyword or file and are not confident that you will find the right 
  match in the first few tries use this agent to perform the search.
```

**Use cases:**
- Multi-step research
- Searching for code across codebase
- Analyzing multiple files
- Complex questions

---

### 🟠 Explore  
```yaml
agentType: Explore
model: haiku (fast & cheap!)
tools: Glob, Grep, Read, LS, Bash (read-only)
permissionMode: dontAsk
whenToUse: |
  Fast agent specialized for exploring codebases. Use this when you 
  need to quickly find files by patterns, search code for keywords, 
  or answer questions about the codebase. Specify thoroughness level: 
  "quick", "medium", or "very thorough".
```

**Key feature**: READ-ONLY - cannot create/edit files, only search and analyze

**Use cases:**
- Find files by pattern
- Search code for keywords
- Quick codebase exploration
- Answer "how does X work?" questions

---

### 🟢 Plan
```yaml
agentType: Plan  
model: haiku (in some modes) / sonnet
tools: Glob, Grep, Read, LS, Bash (read-only)
permissionMode: dontAsk
whenToUse: |
  Fast agent specialized for exploring codebases and designing 
  implementation plans. READ-ONLY planning task.
```

**Key feature**: Explores codebase and creates implementation blueprints (but doesn't write code)

**Use cases:**
- Architecture design
- Implementation planning
- Pattern analysis

---

## 2. Custom Agents (User-Created Subagents)

**Location**: `.claude/agents/` directory

Custom agents are **markdown files** with YAML frontmatter that define specialized agents.

### Example: Custom Agent File

`.claude/agents/code-explorer.md`:
```markdown
---
name: code-explorer
description: Deeply analyzes existing codebase features
tools: Glob, Grep, LS, Read, NotebookRead, WebFetch, TodoWrite
model: sonnet
color: yellow
permissionMode: default
---

You are an expert code analyst specializing in tracing feature implementations.

## Core Mission
Provide complete understanding of how a specific feature works...

[Rest of instructions...]
```

### How Custom Agents Work

1. **Create**: Put markdown files in `.claude/agents/`
   - Project-level: `<project>/.claude/agents/your-agent.md`
   - Personal: `~/.claude/agents/your-agent.md`
   - Plugin: `<plugin>/agents/your-agent.md`

2. **Use**: The main agent can invoke them via Task tool:
   ```
   Use the Task tool with subagent_type="code-explorer"
   ```

3. **Priority**: When multiple agents have same name:
   - Built-in agents
   - Plugin agents
   - User settings agents (`~/.claude/agents/`)
   - Project settings agents (`<project>/.claude/agents/`)
   - Policy/flag settings

---

## 3. What are Subagents?

**Subagent** = Any agent launched by the **main agent** (you, Claude) via the Task tool

### Types of Subagents:

1. **Built-in subagents**: general-purpose, Explore, Plan
2. **Custom subagents**: Any agent defined in `.claude/agents/`
3. **Plugin subagents**: Agents from plugins (e.g., code-explorer, code-architect, code-reviewer)

### Example Flow:

```
User: "Find all authentication code"
  ↓
Main Agent (Claude): Uses Task tool
  ↓
  subagent_type: "Explore"
  prompt: "Find all authentication-related files"
  ↓
Subagent (Explore): Searches codebase
  ↓
Returns results to Main Agent
  ↓
Main Agent: Summarizes results to user
```

---

## 4. Task Tool: How to Use Agents

When you (the main agent) want to delegate work, use the **Task tool**:

```javascript
{
  "description": "Find auth code",
  "prompt": "Search for all authentication-related files...",
  "subagent_type": "Explore",    // Which agent to use
  "model": "haiku"                // Optional: override model
}
```

### subagent_type Options

You can use **any** of these as `subagent_type`:

1. **Built-in**: `"general-purpose"`, `"Explore"`, `"Plan"`
2. **Custom**: Any `name` from your `.claude/agents/*.md` files
3. **Plugin**: Any agent from installed plugins

---

## 5. Your Question: Can I Tell Main Agent to Use My Custom Agents?

**YES! Exactly right!**

Here's how it works:

### Step 1: Create Custom Agent

`.claude/agents/bug-hunter.md`:
```markdown
---
name: bug-hunter
description: Specialized in finding bugs and security vulnerabilities
tools: Grep, Read, Glob
model: sonnet
---

You are a security-focused bug hunter. Search for common vulnerabilities...
```

### Step 2: Main Agent Uses It

When the main agent (Claude) wants to find bugs, it will:

```javascript
// Main agent uses Task tool:
{
  "description": "Hunt for bugs",
  "prompt": "Find potential security vulnerabilities in authentication code",
  "subagent_type": "bug-hunter"  // ← Your custom agent!
}
```

### Step 3: Your Agent Runs

The `bug-hunter` agent:
- Receives the prompt
- Has access to tools you specified (Grep, Read, Glob)
- Uses model you specified (sonnet)
- Returns findings to main agent

---

## 6. How Main Agent Knows About Custom Agents

The main agent sees **all available agents** in its Task tool description:

```
Available agent types and the tools they have access to:
- general-purpose: General-purpose agent... (Tools: *)
- Explore: Fast agent specialized... (Tools: Glob, Grep, Read...)
- Plan: Planning specialist... (Tools: Glob, Grep, Read...)
- code-explorer: Deeply analyzes... (Tools: Glob, Grep, Read...)
- bug-hunter: Finds bugs... (Tools: Grep, Read, Glob...)
```

**The main agent automatically knows about your custom agents!**

---

## 7. Agent Structure (Custom Agent File)

```markdown
---
name: agent-name              # Required: Used in subagent_type
description: What it does     # Required: Shown to main agent
tools: Glob, Grep, Read       # Optional: Restrict tools (* = all)
disallowedTools: Edit, Write  # Optional: Explicitly block tools
model: sonnet                 # Optional: haiku/sonnet/opus
color: yellow                 # Optional: UI color
permissionMode: dontAsk       # Optional: default/dontAsk/acceptEdits/etc
forkContext: true             # Optional: Access to conversation history
---

# Your agent's system prompt

Instructions for what this agent should do...
Detailed guidelines...
Output format requirements...
```

---

## 8. Real Example: feature-dev Plugin

The `feature-dev` plugin includes 3 custom agents:

### code-explorer
```yaml
name: code-explorer
description: Deeply analyzes existing codebase features
tools: Glob, Grep, LS, Read, NotebookRead, WebFetch, TodoWrite
model: sonnet
color: yellow
```

### code-architect  
```yaml
name: code-architect
description: Designs feature architectures with implementation blueprints
tools: Glob, Grep, LS, Read, NotebookRead, WebFetch, TodoWrite
model: sonnet
color: green
```

### code-reviewer
```yaml
name: code-reviewer
description: Reviews code for bugs, quality issues, conventions
tools: Read, Grep, Glob, TodoWrite
model: sonnet
color: blue
```

**How they're used in /feature-dev command:**

```markdown
## Phase 2: Codebase Exploration

Launch 2-3 code-explorer agents in parallel:
- Task(subagent_type="code-explorer", prompt="Find similar features...")
- Task(subagent_type="code-explorer", prompt="Map architecture...")
- Task(subagent_type="code-explorer", prompt="Analyze patterns...")

## Phase 4: Architecture Design

Launch code-architect agents:
- Task(subagent_type="code-architect", prompt="Design minimal approach...")
- Task(subagent_type="code-architect", prompt="Design clean approach...")

## Phase 6: Code Review

Launch code-reviewer agent:
- Task(subagent_type="code-reviewer", prompt="Review implementation...")
```

---

## 9. Key Differences

| Aspect | Built-in Agents | Custom Agents |
|--------|----------------|---------------|
| **Defined in** | cli.js (hardcoded) | `.claude/agents/*.md` files |
| **Count** | 3 (general-purpose, Explore, Plan) | Unlimited! |
| **Who creates** | Anthropic | You / Plugin authors |
| **Can modify** | ❌ No (compiled) | ✅ Yes (just edit .md file) |
| **Auto-loaded** | ✅ Always | ✅ Auto-discovered |
| **Visible to main** | ✅ Yes | ✅ Yes |

---

## 10. Summary

### What are built-in agents?
**3 hardcoded agents** in cli.js: `general-purpose`, `Explore`, `Plan`

### What are subagents?
**Any agent launched via Task tool** - could be built-in OR custom

### Can I create custom agents?
**YES!** Create `.md` files in `.claude/agents/`

### Will main agent use my custom agents?
**YES!** Main agent sees all agents (built-in + custom + plugin) and can use any via Task tool with `subagent_type="your-agent-name"`

### How does main agent know about them?
**Auto-discovery** - Claude Code scans `.claude/agents/` and shows all agents in the Task tool description

---

## Example Workflow

```
1. You create: .claude/agents/security-scanner.md
2. Claude Code auto-loads it
3. Main agent sees "security-scanner" in available agents list
4. User asks: "Check for security issues"
5. Main agent decides: "I'll use security-scanner agent"
6. Main agent calls: Task(subagent_type="security-scanner", prompt="...")
7. Your agent runs and returns results
8. Main agent presents findings to user
```

**It's that simple!**

---

**[Created by Claude: 0ecc17a2-0ac2-4db8-b89e-78c39bcc28e6]**
