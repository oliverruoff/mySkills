# pi.lot Skills Collection

This repository contains a curated collection of **agentic skills** designed for the [pi.lot](https://github.com/oliverruoff/pi.lot) AI assistant harness.

All skills in this repository are:

- **Fully aligned with the official pi.lot agentic skill documentation** — each skill follows the canonical structure (`SKILL.md` manifest, optional `requirements.txt`, and executable scripts under `scripts/`).
- **Self-contained** — every skill bundles its own dependencies, tooling, and instructions. No external configuration files or implicit system state is required to understand or deploy a skill.
- **Modular** — they can be copied individually into a pi.lot `skills/` directory and are discovered automatically.

## Repository Structure

```
skills/
├── brave-search/          # Web & news search via Brave Search API
├── cronjobs/              # Create, edit, and run scheduled pi.lot cronjobs
├── gmail-access/          # Search, read, and download Gmail via IMAP
├── home-assistant/        # Read and control Home Assistant entities
├── hostinger-docker-manager/ # Discover and deploy Hostinger Docker projects
├── memory/                # Persistent markdown-based assistant memory
├── travelplan/            # Fully researched, printable travel plan PDFs with maps & images
├── wetter-forecast/       # 3-day weather forecast with clothing recommendations (DE focused)
└── youtube-summarizer/    # Fetch and summarize YouTube transcripts
```

## Skill Anatomy

Each skill follows the standard pi.lot skill format:

```
skill-name/
├── SKILL.md          # Manifest: description, usage, file references
├── config.json       # (Optional) empty shareable configuration template
├── requirements.txt  # (Optional) Python dependencies
└── scripts/
    └── *.py          # Implementation scripts
```

## System vs. Workspace Skills

| Skill | Origin | Description |
|-------|--------|-------------|
| `brave-search` | pi.lot system | Internet search and news lookup |
| `cronjobs` | pi.lot system | Recurring scheduled tasks and reminders |
| `gmail-access` | pi.lot system | Gmail IMAP integration |
| `home-assistant` | pi.lot system | Home Assistant REST API control |
| `hostinger-docker-manager` | Workspace | Discover, inspect, deploy, and verify Hostinger Docker Manager projects |
| `memory` | pi.lot system | Persistent memory storage |
| `youtube-summarizer` | pi.lot system | YouTube transcript summarization |
| `travelplan` | Workspace | Research and generate travel PDFs |
| `wetter-forecast` | Workspace | Local weather forecast for Germany |

## Usage

To add a skill to your pi.lot instance, copy the desired skill folder into your `skills/` directory (e.g., `/workspace/skills/` or `~/.pi/agent/skills/`) and run `/reload` inside pi.lot to discover it.

### Hostinger Docker Manager

The `hostinger-docker-manager` skill only requires a Hostinger API token:

```bash
export HOSTINGER_API_TOKEN='your-token'
```

On first use, its bundled script discovers the available VPS and Docker project through the Hostinger API. Non-secret target details are cached in the user's config directory, outside the shareable skill. If an account contains multiple VPS instances or projects, the agent asks which candidate to use instead of guessing.

Requirements are Bash 3.2+, `curl`, and `jq`. The skill includes exact setup, deployment, verification, and troubleshooting instructions designed to remain usable by smaller coding models.

## License

See [LICENSE](./LICENSE) for details.
