# Daytona Research: Environment Sandbox for AI Agents

**[Created by Claude: 1e0e8807-bbac-4ccd-bc20-b9e18746e83c]**

## Executive Summary

**Yes, both Claude Code CLI and Claude Desktop CAN use Daytona!** Daytona provides native MCP (Model Context Protocol) integration specifically designed for Claude agents.

**Pricing Quick Facts:**
- 💰 $200 in free credits (≈2,985 hours of default usage)
- 📊 Pay-as-you-go: ~$0.067/hour for 1 vCPU + 1GB RAM
- 🚀 Startup credits: $10K-$75K for eligible companies
- ⏱️ Per-second billing with auto-stop after 15min inactivity
- 🎁 5GB free storage included

---

## What is Daytona?

Daytona is an open-source, secure infrastructure platform for running AI-generated code in isolated sandbox environments. Originally a development environment tool, Daytona pivoted in February 2025 to focus on AI agent code execution.

**Key Stats:**
- 31.2k GitHub stars
- Sub-90ms sandbox spin-up time
- AGPL-3.0 licensed
- Active development and community support

---

## Core Features

### 1. **Blazing Fast Performance**
- Sandbox creation: <90ms
- Startup time: ~200ms
- Optimized for rapid iteration cycles

### 2. **Complete Isolation**
- Dedicated, isolated infrastructure per sandbox
- No shared compute
- Zero cross-tenant risk
- Execute AI-generated code with zero risk to your infrastructure

### 3. **Stateful Sandboxes**
- Filesystem persists across interactions
- Environment variables preserved
- Process memory maintained
- Sandboxes can remain active indefinitely

### 4. **Massive Parallelization**
- Support for concurrent AI workflows
- Scale to multiple sandboxes simultaneously

### 5. **Comprehensive APIs**
- File management
- Git integration
- LSP (Language Server Protocol) support
- Code execution
- Container compatibility (any OCI/Docker image)

---

## Daytona MCP Server Integration

### What It Provides

The Daytona MCP Server enables AI agents to:

1. **Automatic Capability Discovery** - Agents detect available features
2. **Sandbox Management** - Create and destroy isolated environments
3. **File Operations** - Upload/download files to/from sandboxes
4. **Code Execution** - Run commands and scripts securely
5. **Repository Access** - Clone repos and generate preview links for web apps

### Compatible AI Agents

✅ **Claude Desktop App** - Fully supported
✅ **Claude Code CLI** - Fully supported
✅ **Cursor** - Fully supported
✅ **Windsurf** - Fully supported

---

## Setup Instructions

### Prerequisites
```bash
# Install Daytona CLI
brew install daytonaio/cli/daytona
```

### Configuration for Claude

```bash
# 1. Login to Daytona
daytona login

# 2. Initialize MCP server for Claude
daytona mcp init claude

# 3. Generate MCP configuration
daytona mcp config

# 4. Start the MCP server
daytona mcp start
```

The `daytona mcp init claude` command works for both:
- **Claude Desktop App**
- **Claude Code CLI**

After initialization, the configuration is automatically added to your Claude settings.

### Manual Configuration (if needed)

The `daytona mcp config` command outputs JSON configuration that you can manually copy into:
- Claude Desktop: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Claude Code: Your project's MCP configuration file

---

## Use Cases

### 1. **React Development with Live Previews**
- Create sandbox with Node.js environment
- Run development server
- Generate preview links for instant access
- Test changes in isolation

### 2. **Python Data Analysis**
- Upload datasets to sandbox
- Execute analysis scripts
- Download results
- Complete isolation from local environment

### 3. **Code Testing & Validation**
- Test AI-generated code safely
- Run in disposable environments
- Quick iteration cycles
- No pollution of local system

### 4. **Multi-Language Projects**
- Use any Docker/OCI container image
- Pre-configured environments
- Consistent across team/agents

---

## SDKs Available

- **Python SDK** - Released November 2025
- **TypeScript/JavaScript SDK** - Available
- **CLI** - Full-featured command-line interface

### Example Usage (Python)

```python
from daytona import Daytona

# Initialize client with API key
client = Daytona(api_key="your-api-key")

# Create sandbox
sandbox = client.create_sandbox(image="python:3.11")

# Execute code
result = sandbox.execute("python script.py")

# Retrieve results
print(result.output)
```

---

## Pricing

### Pay-As-You-Go Model

Daytona uses **per-second billing** - you only pay for active compute time when sandboxes are running.

**Hourly Rates:**
- **Compute (vCPU):** $0.0504/hour
- **Memory (GiB):** $0.0162/hour
- **Storage (GiB):** $0.000108/hour

**Per-Second Rates:**
- **Compute (vCPU):** $0.00001400/second
- **Memory (GiB):** $0.00000450/second
- **Storage (GiB):** $0.00000003/second

### Cost Examples

**Example 1: Light Testing (1 vCPU, 1GB RAM, 5GB storage for 1 hour)**
- Compute: $0.0504
- Memory: $0.0162
- Storage: $0.00054 (5GB)
- **Total: ~$0.067/hour** or **~$1.61/day** (24 hours)

**Example 2: Development Work (2 vCPU, 4GB RAM, 10GB storage for 8 hours)**
- Compute: $0.0504 × 2 × 8 = $0.8064
- Memory: $0.0162 × 4 × 8 = $0.5184
- Storage: $0.000108 × 10 × 8 = $0.00864
- **Total: ~$1.33 for 8 hours of work**

### Free Tier & Credits

**Individual Accounts:**
- **$200 in free compute credits** for new accounts
- **5 GB of storage** is free
- Credits cover approximately 2,985 hours of default sandbox usage (1 vCPU, 1GB RAM)

**Startup Grid Program:**

Daytona offers substantial credits for eligible startups:

| Track | Initial Credits | Total Potential | Qualification |
|-------|----------------|-----------------|---------------|
| **Standard Track** | $10,000 | Up to $50,000 | Apply at daytona.io/startups |
| **Partner Fast Track** | $25,000 | Up to $75,000 | Referral from partner VCs/accelerators |

**Startup Program Benefits:**
- Direct access to engineering team for implementation support
- Priority support
- Application takes <5 minutes
- Team reviews and responds promptly
- Accepts AI-generated application text (their words!)

**Eligibility:** Targets early-stage companies building AI and developer tools. No complex documentation required - just a 100-word startup story and pitch deck.

### Default Resource Allocations

**New Sandboxes Include:**
- 1 vCPU
- 1GB RAM
- 3GB disk space
- All resources are customizable

### Auto-Management Features (Cost Saving)

**Automatic Resource Control:**
- **Auto-stop:** Sandboxes automatically stop after **15 minutes of inactivity**
- **Auto-archive:** Stopped sandboxes archive after **7 days**
- **Archived sandboxes:** Data moves to cold storage, freeing all compute (no quota impact)

This means you won't accidentally rack up charges from forgotten sandboxes!

### Organization Tiers

Organizations are automatically placed into tiers based on verification status:

| Tier | Network Access | Features |
|------|---------------|----------|
| **Tier 1 & 2** | Restricted | Cannot override at sandbox level |
| **Tier 3 & 4** | Full Internet | Default access, production-ready |

Upgrade your tier through verification steps in the Daytona dashboard.

### Comparison with Competitors

| Feature | Daytona | E2B | Modal |
|---------|---------|-----|-------|
| **Cold Start** | <90ms | 150ms | Sub-second |
| **Free Tier** | $200 credits | Limited | Generous free tier |
| **Isolation** | Docker/Kata Containers | Firecracker microVMs | gVisor |
| **Session Length** | Indefinite | Up to 24hr (Pro) | Auto-scaling |
| **MCP Integration** | ✅ Native | ❌ No | ❌ No |
| **Claude Support** | ✅ Official | ⚠️ Custom | ⚠️ Custom |
| **Multi-Language** | ✅ Any OCI image | ✅ Yes | ⚠️ Python-focused |
| **Best For** | AI agent workflows | Demos/hackathons | Python ML workloads |

**Cost Context:** Northflank's CPU pricing is about 65% less expensive than Modal for CPU-only workloads, though Daytona's pricing is competitive for AI agent use cases due to per-second billing and auto-stop features.

### Pricing Advantages

✅ **Per-second billing** - No wasted money on idle time
✅ **Auto-stop after 15 min** - Prevents runaway costs
✅ **Auto-archive after 7 days** - Automatic cleanup
✅ **$200 free credits** - Extensive testing before paying
✅ **Startup credits up to $75K** - Excellent for early-stage companies
✅ **5GB free storage** - No charges for small projects
✅ **No minimums** - Pay only for what you use

### Account Setup

Create account at: https://app.daytona.io

### Pricing FAQ

**Q: How long will my $200 free credit last?**
A: With default resources (1 vCPU, 1GB RAM), you get approximately 2,985 hours. With auto-stop after 15min of inactivity, this can last months for typical AI agent usage.

**Q: What happens when I run out of credits?**
A: You'll need to add a payment method to continue. You can monitor usage in the Daytona dashboard.

**Q: Can I avoid unexpected charges?**
A: Yes! Auto-stop after 15min of inactivity and auto-archive after 7 days prevent runaway costs. You can also set up alerts in your dashboard.

**Q: How do I calculate my costs?**
A: Use the formula: `(vCPUs × $0.0504) + (GiB RAM × $0.0162) + (GiB storage × $0.000108)` per hour. Multiply by hours of active usage.

**Q: Is the startup program worth applying for?**
A: Absolutely! If you're building AI tools, the application takes <5 minutes and provides $10K-$75K in credits plus engineering support.

**Q: Are there any hidden fees?**
A: No. You only pay for compute, memory, and storage while sandboxes are active. No setup fees, no monthly minimums, no data transfer charges mentioned.

**Q: How does pricing compare to running locally?**
A: For isolation and security, Daytona is cost-effective. You avoid polluting your local environment and get complete isolation for ~$0.067/hour.

---

## Production Use Case: Coherence

**Real-world example:** Coherence automated MCP server generation using Claude Code and Daytona, enabling AI agents to integrate with any API securely and at scale.

The combination of Daytona's secure environments and Claude Code's generation capabilities solved the challenge of making any API instantly accessible to AI agents.

---

## Advantages for Your Workflow

### For Claude Code CLI:
✅ Execute code without polluting your local environment
✅ Test AI-generated scripts safely
✅ Upload files and run them in isolation
✅ Fast iteration cycles (<90ms sandbox creation)
✅ Automatic cleanup of disposable environments

### For Claude Desktop:
✅ Same capabilities through chat interface
✅ Generate and test code interactively
✅ Preview web applications with generated links
✅ Seamless integration via MCP

---

## Alternatives Considered

According to research, Daytona is positioned as a leading solution, with comparisons to:
- **microsandbox** - Another AI sandbox solution
- **Northflank** - Traditional cloud infrastructure
- **E2B** - AI code execution platform

Daytona stands out for its speed (<90ms), native MCP integration, and agent-first design.

---

## Getting Started Checklist

- [ ] Review pricing model and cost examples above
- [ ] Install Daytona CLI: `brew install daytonaio/cli/daytona`
- [ ] Create account at https://app.daytona.io (get $200 free credits)
- [ ] (Optional) Apply for Startup Grid if eligible: daytona.io/startups
- [ ] Login: `daytona login`
- [ ] Initialize MCP for Claude: `daytona mcp init claude`
- [ ] Start MCP server: `daytona mcp start`
- [ ] Test with Claude Code CLI or Claude Desktop
- [ ] Upload test file and execute in sandbox
- [ ] Monitor usage in dashboard to track credit consumption
- [ ] Set up billing alerts (recommended)

---

## Additional Resources

- **GitHub**: https://github.com/daytonaio/daytona
- **Official Site**: https://www.daytona.io/
- **Create Account**: https://app.daytona.io
- **Startup Grid Program**: https://daytona.io/startups
- **MCP Documentation**: https://www.daytona.io/docs/mcp/
- **Python SDK**: https://pypi.org/project/daytona/
- **MCP Server Guide**: https://www.daytona.io/dotfiles/introducing-daytona-mcp-server
- **Pricing Info**: https://daytonaio-ai.framer.website/pricing

---

## Conclusion

**Daytona is an excellent fit for your needs.** It provides:

1. ✅ Environment sandbox capability
2. ✅ File upload functionality
3. ✅ Code execution support
4. ✅ Native integration with Claude Code CLI
5. ✅ Native integration with Claude Desktop
6. ✅ Fast, secure, and isolated environments
7. ✅ Generous free tier ($200 credits = ~2,985 hours)
8. ✅ Cost-effective pricing (~$0.067/hour for basic usage)
9. ✅ Auto-stop features prevent runaway costs

The MCP integration means minimal setup and automatic capability discovery by your Claude agents. You can start using it immediately after a simple `brew install` and configuration.

**Cost Assessment:**
- **For Testing/Learning:** The $200 free credit is more than sufficient (covers months of light usage)
- **For Development:** Very affordable at ~$1.33 for a full workday (8 hours)
- **For Startups:** Apply for $10K-$75K in credits through Startup Grid program
- **Cost Control:** Auto-stop after 15min and per-second billing ensure you never overpay

**Recommendation: Proceed with Daytona installation and testing.** Start with the free $200 credits to evaluate if it meets your needs before any payment is required.

---

**[Created by Claude: 1e0e8807-bbac-4ccd-bc20-b9e18746e83c]**
*Research completed: 2025-11-19*
