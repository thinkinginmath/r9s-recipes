# r9s Agent Presets

A collection of ready-to-use agent configurations for common use cases.

## Quick Start

Copy an agent to your local store:

```bash
# Copy a preset to your local agents directory
cp -r presets/agents/code-reviewer ~/.r9s/agents/

# Or use with r9s agent pull (when implemented)
r9s agent pull ./presets/agents/code-reviewer
```

## Available Agents

| Agent | Category | Description | Skills |
|-------|----------|-------------|--------|
| `code-reviewer` | Development | Expert code review with security focus | code-review |
| `documentation-writer` | Development | Technical docs with clear examples | docx |
| `data-analyst` | Data | Transform and analyze data | xlsx, csv |
| `presentation-designer` | Creative | Compelling slide decks | pptx |
| `research-analyst` | Productivity | Deep research with synthesis | - |
| `email-assistant` | Productivity | Professional email drafting | - |
| `contract-analyst` | Enterprise | Legal document analysis | pdf |
| `api-designer` | Specialized | REST/GraphQL API design | - |
| `security-auditor` | Specialized | Security-focused code review | - |
| `devops-assistant` | Specialized | Infrastructure and CI/CD | - |

## Agent Structure

Each agent follows this structure:

```
agent-name/
├── agent.toml              # Agent metadata
└── versions/
    └── 1.0.0.toml          # Version with instructions, model, params
```

### agent.toml

```toml
[agent]
id = "agt_agent_name"
name = "agent-name"
description = "What this agent does"
current_version = "1.0.0"
```

### versions/1.0.0.toml

```toml
version = "1.0.0"
status = "approved"           # draft | approved | deprecated
model = "claude-sonnet-4-20250514"
provider = "r9s"
created_by = "r9s-presets"
change_reason = "Initial release"

[params]
temperature = 0.3
max_tokens = 4096

[instructions]
value = """
Your system prompt here...
"""
variables = ["var1", "var2"]  # Template variables like {{var1}}

[[skills]]
ref = "github:owner/repo/path/to/skill"
```

## Template Variables

Some agents use template variables (e.g., `{{audience_type}}`). These are rendered at runtime:

```bash
r9s chat --agent presentation-designer \
  --var audience_type="executives" \
  --var presentation_topic="Q4 Results"
```

## Skills Integration

Agents can reference skills from:
- **GitHub**: `github:anthropics/skills/skills/document/pptx`
- **Local**: `~/.r9s/skills/my-skill`
- **Registry**: `r9s:skill-name`

See [agentskills.io](https://agentskills.io) for the skills specification.

## Customization

1. Copy the agent to your local store
2. Edit the version file to customize instructions
3. Bump the version for tracking

```bash
r9s agent update my-agent --instructions "..." --bump minor
```

## Contributing

To add a new preset:
1. Create a new directory under the appropriate category
2. Follow the agent.toml + versions/ structure
3. Include a descriptive system prompt
4. Reference relevant skills if applicable
5. Document any template variables used
