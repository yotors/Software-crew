# Software Crew

A Python prototype for coordinating software-development tools through specialized agents. It explores **Agent-to-Agent (A2A)** discovery and messaging, **Model Context Protocol (MCP)** tool services, and Gemini-based routing.

The repository contains the orchestration and integration code. It is a development prototype, not a verified production service or a one-command demo.

## How it is organized

1. The FastAPI orchestrator accepts a task or message and asks Gemini to select an agent.
2. Agent cards describe the filesystem, GitHub, and Vercel capabilities.
3. An agent selects a capability and calls its corresponding MCP tool service.
4. Tool implementations operate on local files, GitHub repositories, or the Vercel CLI.

| Component | Source | Responsibility |
| --- | --- | --- |
| Orchestrator | [orchestrator.py](orchestrator.py) | Agent discovery, model-based routing, HTTP entry points |
| Shared agent | [agents/base.py](agents/base.py) | Agent cards, capability selection, tool calls |
| Filesystem | [agents/filesystem_agent.py](agents/filesystem_agent.py), [mcp/filesystem.py](mcp/filesystem.py) | Directory and file operations, command execution |
| GitHub | [agents/github_agent.py](agents/github_agent.py), [mcp/github_mcp.py](mcp/github_mcp.py) | Repository creation, branches, code updates, repository information |
| Vercel | [agents/vercel_agent.py](agents/vercel_agent.py), [mcp/vercel.py](mcp/vercel.py) | CLI login, deployment, environment variables, deployment status |
| Launcher | [run.py](run.py) | Construct and start the orchestrator and services |

The intended orchestrator API is `POST /task`, `POST /message`, and `GET /agents` on port 8006. A2A agent servers use ports 8000, 8004, and 8005; MCP services use 8001–8003.

## Inspect the code locally

The imports use the package name `software_crew`, so clone into that directory name:

```sh
git clone https://github.com/yotors/Software-crew.git software_crew
cd software_crew
python -m compileall -q agents mcp orchestrator.py run.py
```

This syntax check requires no API keys and makes no network requests. Passing it does not verify imports, dependency compatibility, agent behavior, or external integrations.

The source entry point is `python -m software_crew.run`, invoked from the parent directory of `software_crew`. Address the development gaps below before trying live operations.

## Development dependencies and configuration

[requirements.txt](requirements.txt) lists the current dependency constraints. They are not a tested lockfile or a complete environment specification: the code also directly imports `google.generativeai`, `requests`, and `flask`, whose distributions are not explicitly listed.

The runtime expects:

- `GOOGLE_API_KEY` for Gemini-based routing.
- `GITHUB_TOKEN` for GitHub operations.
- An installed, separately authenticated Vercel CLI for Vercel operations.

[.env.example](.env.example) contains variable names only. Keep actual values in a local `.env` or a development secret store. Never commit credentials.

## Current limitations

- **Dependency and model setup:** compatible versions and an available Gemini model need to be selected and tested. The source currently relies on the SDK's default model.
- **Registry configuration:** the agent registry URL strings in `orchestrator.py` contain literal `f{registry_url}` text and need correction.
- **Task contract:** the orchestrator passes dictionaries, while `VercelAgent.handle_task` expects an A2A task object with `message`, `artifacts`, and `status`.
- **Command execution:** the filesystem command tool calls asynchronous subprocess APIs without awaiting them. It is not a working command runner in its current form.
- **Reliability:** the repository has no automated behavior tests, CI workflow, or recorded end-to-end smoke test. HTTP tool calls do not set a request timeout.

These are known development gaps, not verified working features. A useful next milestone is a dependency-pinned, mock-backed test suite covering routing, tool failures, and the task/message contracts before enabling real side effects.

## Safety boundary

Use only disposable local files, test repositories, and test deployment projects during development. The current servers bind to `0.0.0.0` and have no application-level authentication or approval gate. Filesystem paths are not confined to a sandbox, and the Vercel deploy command requests a production deployment with `--prod`.

Do not expose these services publicly or give them production credentials. Add access control, path restrictions, bounded tool execution, and explicit approval for writes/deployments before shared use.
