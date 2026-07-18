---
name: hostinger-docker-manager
description: Discover, configure, inspect, and deploy Hostinger VPS Docker Manager projects using only a Hostinger API token and a bundled deterministic script. Use when any coding agent, including a small model, must manage a Hostinger Docker project with first-run auto-discovery, cached local configuration, action polling, logs, and HTTP verification.
---

# Hostinger Docker Manager

Follow these instructions exactly. Do not manually recreate Hostinger API calls.

## Files and data separation

The shareable skill contains:

- `SKILL.md`: these instructions
- `scripts/hostinger_docker.sh`: all operational logic
- `config.json`: an empty `{}` template; never put personal data or tokens in it

On first setup, the script writes discovered infrastructure data to the user's runtime config outside the skill:

```text
$XDG_CONFIG_HOME/hostinger-docker-manager/config.json
```

If `XDG_CONFIG_HOME` is unset, use:

```text
$HOME/.config/hostinger-docker-manager/config.json
```

The runtime config never contains the API token. This separation keeps the skill safe to share after use.

## Step 1: Locate the script

Resolve the absolute skill directory from this `SKILL.md` locator. Then set:

```bash
HOSTINGER_MANAGER_SCRIPT="<absolute-skill-directory>/scripts/hostinger_docker.sh"
```

Do not assume the skill is installed under `~/.codex` or that the current directory is the skill directory.

## Step 2: Run diagnostics

Always run:

```bash
"$HOSTINGER_MANAGER_SCRIPT" doctor
```

Requirements:

- Bash 3.2+
- `curl`
- `jq`

If a dependency is missing, use the installation hint printed by `doctor`. Install system software only when authorized. Rerun `doctor` afterward.

## Step 3: Obtain the only required secret

Read `HOSTINGER_API_TOKEN` from the environment.

- If `doctor` prints `token=set`, continue.
- If the token is missing in an interactive terminal, the script requests it with hidden input.
- If the token is missing in a non-interactive agent run, ask the user for it through the agent's secure input mechanism, export it for the session, and retry.

Never print, log, persist, commit, or place the token in the skill or runtime config.

## Step 4: Initialize automatically when needed

Run:

```bash
"$HOSTINGER_MANAGER_SCRIPT" ensure-setup
```

This command:

1. Reuses a valid runtime config when present.
2. Otherwise lists VPS instances via the API.
3. Selects the VPS automatically only when exactly one exists or `HOSTINGER_DOCKER_VM_ID` is set.
4. Lists Docker projects on that VPS.
5. Selects the project automatically only when exactly one exists or `HOSTINGER_DOCKER_PROJECT` is set.
6. Discovers IP address, published ports, project source URL, frontend URL, and likely health URL.
7. Writes the non-secret runtime config with file mode `600`.

If several VPS instances or projects exist, the command exits with code `3` and prints candidates. Do not guess. Ask the user which candidate to use, export the selected value, and rerun:

```bash
export HOSTINGER_DOCKER_VM_ID='<selected VM id>'
export HOSTINGER_DOCKER_PROJECT='<selected project name>'
"$HOSTINGER_MANAGER_SCRIPT" setup
```

If setup cannot discover a source URL, read-only operations still work. Before a source deployment, ask the user for the Compose-file or GitHub URL and export:

```bash
export HOSTINGER_DOCKER_SOURCE_URL='<URL>'
"$HOSTINGER_MANAGER_SCRIPT" setup
```

## Step 5: Choose one workflow

Read-only commands: `doctor`, `show-config`, `vms`, `projects`, `status`, `logs`, `errors`, `verify`, `check`.

Production mutations: `deploy`, `deploy-and-verify`, `restart`, `update-images`.

### Inspect or health-check

```bash
"$HOSTINGER_MANAGER_SCRIPT" ensure-setup
"$HOSTINGER_MANAGER_SCRIPT" check
```

### Deploy current repository source

Only when the user explicitly requested a production deployment:

```bash
"$HOSTINGER_MANAGER_SCRIPT" ensure-setup
"$HOSTINGER_MANAGER_SCRIPT" deploy-and-verify
```

Use this for Compose services with local `build.context`. It performs preflight status, fresh source deployment, action polling, HTTP checks, and filtered error checks.

### Restart only

```bash
"$HOSTINGER_MANAGER_SCRIPT" ensure-setup
"$HOSTINGER_MANAGER_SCRIPT" status
"$HOSTINGER_MANAGER_SCRIPT" restart
"$HOSTINGER_MANAGER_SCRIPT" check
```

### Refresh image tags only

Use only for services based on `image:` tags, not local source builds:

```bash
"$HOSTINGER_MANAGER_SCRIPT" ensure-setup
"$HOSTINGER_MANAGER_SCRIPT" status
"$HOSTINGER_MANAGER_SCRIPT" update-images
"$HOSTINGER_MANAGER_SCRIPT" check
```

### Show raw logs

```bash
"$HOSTINGER_MANAGER_SCRIPT" logs 100
```

Prefer `errors` unless raw logs are requested. Raw logs may contain user/session data; do not repeat secrets.

## Step 6: Interpret failures

- Exit `0`: success.
- Exit `2`: missing token, dependency, configuration field, or invalid argument. Follow the printed instruction.
- Exit `3`: multiple discovery candidates. Ask the user to select one; never guess.
- HTTP `401`: token invalid or expired. Ask for a replacement; retry once.
- HTTP `404`: cached target is stale. Run `setup` again.
- Action `failed`, `error`, or `cancelled`: stop, run `errors`, and report the failure.
- Action timeout: do not start another mutation. Run `status`; report completion as unknown.
- Non-running container, non-`200` health response, or detected error logs: do not claim success.

## Step 7: Report consistently

```text
Operation: <check/deploy/restart/update-images>
Target: VM <id>, project <name>
Action: <id and final state, or none>
Containers: <states>
Frontend: <URL and HTTP code, or not discovered>
Health: <URL and HTTP code, or not discovered>
Errors: <none or concise summary>
```

Never claim deployment success merely because Hostinger accepted the request. Require action state `success` plus post-operation verification.
