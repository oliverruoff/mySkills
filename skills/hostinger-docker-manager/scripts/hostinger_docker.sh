#!/usr/bin/env bash
set -euo pipefail

API_BASE="${HOSTINGER_API_BASE:-https://developers.hostinger.com/api/vps/v1}"
CONFIG_HOME="${XDG_CONFIG_HOME:-${HOME:-.}/.config}"
CONFIG_PATH="${HOSTINGER_DOCKER_CONFIG:-${CONFIG_HOME}/hostinger-docker-manager/config.json}"

usage() {
  echo "Usage: $0 {doctor|setup|ensure-setup|show-config|vms|projects|status|logs [lines]|errors|verify|check|update-images|restart|deploy|deploy-and-verify}" >&2
}

install_hint() {
  case "$(uname -s 2>/dev/null || true)" in
    Darwin) echo "Install with: brew install curl jq" ;;
    *)
      if command -v apt-get >/dev/null 2>&1; then echo "Install with: sudo apt-get update && sudo apt-get install -y curl jq"
      elif command -v dnf >/dev/null 2>&1; then echo "Install with: sudo dnf install -y curl jq"
      elif command -v apk >/dev/null 2>&1; then echo "Install with: sudo apk add bash curl jq"
      else echo "Install Bash 3.2+, curl, and jq with the system package manager."
      fi
      ;;
  esac
}

check_dependencies() {
  local missing=0 command_name
  for command_name in curl jq; do
    if ! command -v "$command_name" >/dev/null 2>&1; then
      echo "Missing dependency: ${command_name}" >&2
      missing=1
    fi
  done
  if [[ "$missing" -ne 0 ]]; then install_hint >&2; return 1; fi
}

load_token() {
  if [[ -n "${HOSTINGER_API_TOKEN:-}" ]]; then return 0; fi
  if [[ -t 0 ]]; then
    read -r -s -p "Hostinger API token: " HOSTINGER_API_TOKEN
    echo >&2
    export HOSTINGER_API_TOKEN
  else
    echo "HOSTINGER_API_TOKEN is not set. Ask the user for it securely, export it, and retry." >&2
    return 2
  fi
  [[ -n "$HOSTINGER_API_TOKEN" ]] || { echo "No Hostinger API token provided." >&2; return 2; }
}

api() {
  load_token
  curl --fail --silent --show-error "$@" \
    -H "Authorization: Bearer ${HOSTINGER_API_TOKEN}" \
    -H "Accept: application/json"
}

config_get() {
  local key="$1"
  [[ -f "$CONFIG_PATH" ]] || return 0
  jq -r --arg key "$key" '.[$key] // empty' "$CONFIG_PATH"
}

load_config() {
  VM_ID="${HOSTINGER_DOCKER_VM_ID:-$(config_get vm_id)}"
  PROJECT="${HOSTINGER_DOCKER_PROJECT:-$(config_get project)}"
  SOURCE_URL="${HOSTINGER_DOCKER_SOURCE_URL:-$(config_get source_url)}"
  FRONTEND_URL="${HOSTINGER_DOCKER_FRONTEND_URL:-$(config_get frontend_url)}"
  HEALTH_URL="${HOSTINGER_DOCKER_HEALTH_URL:-$(config_get health_url)}"
}

require_target() {
  load_config
  [[ -n "$VM_ID" ]] || { echo "No VM configured. Run: $0 setup" >&2; return 2; }
  [[ -n "$PROJECT" ]] || { echo "No project configured. Run: $0 setup" >&2; return 2; }
}

discover_setup() {
  local vms vm_count vm_id projects project_count project ip containers logs source_url frontend_url health_url
  vms="$(api "${API_BASE}/virtual-machines")"
  vm_count="$(jq 'length' <<<"$vms")"
  vm_id="${HOSTINGER_DOCKER_VM_ID:-}"
  if [[ -z "$vm_id" && "$vm_count" -eq 1 ]]; then vm_id="$(jq -r '.[0].id' <<<"$vms")"; fi
  if [[ -z "$vm_id" ]]; then
    echo "Multiple or no VPS instances found. Select one and export HOSTINGER_DOCKER_VM_ID:" >&2
    jq '[.[] | {id, hostname, state, ipv4: [.ipv4[].address]}]' <<<"$vms" >&2
    return 3
  fi
  ip="$(jq -r --argjson id "$vm_id" '.[] | select(.id == $id) | .ipv4[0].address // empty' <<<"$vms")"
  projects="$(api "${API_BASE}/virtual-machines/${vm_id}/docker")"
  project_count="$(jq 'length' <<<"$projects")"
  project="${HOSTINGER_DOCKER_PROJECT:-}"
  if [[ -z "$project" && "$project_count" -eq 1 ]]; then project="$(jq -r '.[0].name' <<<"$projects")"; fi
  if [[ -z "$project" ]]; then
    echo "Multiple or no Docker projects found. Select one and export HOSTINGER_DOCKER_PROJECT:" >&2
    jq '[.[] | {name, state, status, path}]' <<<"$projects" >&2
    return 3
  fi
  containers="$(api "${API_BASE}/virtual-machines/${vm_id}/docker/${project}/containers")"
  logs="$(api "${API_BASE}/virtual-machines/${vm_id}/docker/${project}/logs?tail=200")"
  source_url="${HOSTINGER_DOCKER_SOURCE_URL:-$(jq -r '[.[].entries[].line | select(test("Project URL:"))][-1] // ""' <<<"$logs" | sed 's/^.*Project URL: //')}"
  frontend_url="${HOSTINGER_DOCKER_FRONTEND_URL:-}"
  health_url="${HOSTINGER_DOCKER_HEALTH_URL:-}"
  if [[ -z "$frontend_url" && -n "$ip" ]]; then
    if jq -e 'any(.[]; any(.ports[]?; .host_port == 443))' <<<"$containers" >/dev/null; then frontend_url="https://${ip}/"
    elif jq -e 'any(.[]; any(.ports[]?; .host_port == 80))' <<<"$containers" >/dev/null; then frontend_url="http://${ip}/"
    fi
  fi
  if [[ -z "$health_url" && -n "$ip" ]] && jq -e 'any(.[]; any(.ports[]?; .host_port == 8000))' <<<"$containers" >/dev/null; then
    health_url="http://${ip}:8000/health"
  fi
  mkdir -p "$(dirname "$CONFIG_PATH")"
  temporary_config="${CONFIG_PATH}.tmp.$$"
  jq -nc \
    --arg api_base "$API_BASE" --arg vm_id "$vm_id" --arg project "$project" \
    --arg source_url "$source_url" --arg frontend_url "$frontend_url" --arg health_url "$health_url" \
    '{api_base:$api_base,vm_id:$vm_id,project:$project,source_url:$source_url,frontend_url:$frontend_url,health_url:$health_url}' >"$temporary_config"
  chmod 600 "$temporary_config"
  mv "$temporary_config" "$CONFIG_PATH"
  echo "Saved non-secret configuration: ${CONFIG_PATH}"
  jq . "$CONFIG_PATH"
}

wait_for_action() {
  local action_id="$1" response state
  for _ in {1..60}; do
    response="$(api "${API_BASE}/virtual-machines/${VM_ID}/actions/${action_id}")"
    state="$(jq -r '.state' <<<"$response")"
    echo "action ${action_id}: ${state}"
    case "$state" in
      success) return 0 ;;
      failed|error|cancelled) jq . <<<"$response"; return 1 ;;
    esac
    sleep 5
  done
  echo "Timed out waiting for action ${action_id}. Do not start another mutation." >&2
  return 1
}

run_action() {
  local label="$1" endpoint="$2" response action_id
  response="$(api --request POST "$endpoint" -H "Content-Type: application/json" --data '{}')"
  action_id="$(jq -er '.id' <<<"$response")"
  echo "${label} action: ${action_id}"
  wait_for_action "$action_id"
}

command_name="${1:-}"
check_dependencies
if [[ "$command_name" != "doctor" ]]; then load_token; fi

case "$command_name" in
  doctor)
    printf 'bash=%s\ncurl=%s\njq=%s\ntoken=%s\nconfig_path=%s\nconfig=%s\n' \
      "$BASH_VERSION" "$(command -v curl)" "$(command -v jq)" \
      "$([[ -n "${HOSTINGER_API_TOKEN:-}" ]] && echo set || echo missing)" "$CONFIG_PATH" \
      "$([[ -s "$CONFIG_PATH" ]] && echo present || echo missing)"
    ;;
  setup)
    discover_setup
    ;;
  ensure-setup)
    load_config
    if [[ -n "$VM_ID" && -n "$PROJECT" ]]; then echo "Configuration ready: ${CONFIG_PATH}"; else discover_setup; fi
    ;;
  show-config)
    [[ -f "$CONFIG_PATH" ]] || { echo "No runtime config. Run: $0 setup" >&2; exit 2; }
    jq . "$CONFIG_PATH"
    ;;
  vms)
    api "${API_BASE}/virtual-machines" | jq '[.[] | {id, hostname, state, ipv4: [.ipv4[].address]}]'
    ;;
  projects)
    load_config
    [[ -n "$VM_ID" ]] || { echo "Set HOSTINGER_DOCKER_VM_ID or run setup." >&2; exit 2; }
    api "${API_BASE}/virtual-machines/${VM_ID}/docker" | jq '[.[] | {name, state, status, path}]'
    ;;
  status)
    require_target
    api "${API_BASE}/virtual-machines/${VM_ID}/docker/${PROJECT}/containers" | jq '[.[] | {name, state, status, ports}]'
    ;;
  logs)
    require_target
    lines="${2:-100}"
    [[ "$lines" =~ ^[0-9]+$ ]] || { echo "Log line count must be a positive integer." >&2; exit 2; }
    api "${API_BASE}/virtual-machines/${VM_ID}/docker/${PROJECT}/logs?tail=${lines}" | jq '[.[] | {service, entries}]'
    ;;
  errors)
    require_target
    log_response="$(api "${API_BASE}/virtual-machines/${VM_ID}/docker/${PROJECT}/logs?tail=100")"
    filtered_errors="$(jq '[.[] | {service, errors: [.entries[] | select(.line | test("error|exception|failed|traceback"; "i")) | .line]}]' <<<"$log_response")"
    error_count="$(jq '[.[].errors[]] | length' <<<"$filtered_errors")"
    printf '%s\n' "$filtered_errors"
    [[ "$error_count" -eq 0 ]] || { echo "Detected ${error_count} recent error line(s)." >&2; exit 1; }
    ;;
  verify)
    require_target
    "$0" status
    if [[ -n "$FRONTEND_URL" ]]; then
      frontend_code="$(curl --silent --show-error --output /dev/null --write-out '%{http_code}' "$FRONTEND_URL")"
      echo "frontend_url=${FRONTEND_URL} frontend_http=${frontend_code}"
      [[ "$frontend_code" == "200" ]]
    else echo "frontend_url=not-discovered"; fi
    if [[ -n "$HEALTH_URL" ]]; then
      health_code="$(curl --silent --show-error --output /dev/null --write-out '%{http_code}' "$HEALTH_URL")"
      echo "health_url=${HEALTH_URL} health_http=${health_code}"
      [[ "$health_code" == "200" ]]
    else echo "health_url=not-discovered"; fi
    ;;
  check)
    "$0" ensure-setup
    "$0" verify
    "$0" errors
    ;;
  update-images)
    require_target
    run_action "update-images" "${API_BASE}/virtual-machines/${VM_ID}/docker/${PROJECT}/update"
    ;;
  restart)
    require_target
    run_action "restart" "${API_BASE}/virtual-machines/${VM_ID}/docker/${PROJECT}/restart"
    ;;
  deploy)
    require_target
    [[ -n "$SOURCE_URL" ]] || { echo "No source URL discovered. Set HOSTINGER_DOCKER_SOURCE_URL and rerun setup." >&2; exit 2; }
    response="$(api --request POST "${API_BASE}/virtual-machines/${VM_ID}/docker" -H "Content-Type: application/json" \
      --data "$(jq -nc --arg project "$PROJECT" --arg content "$SOURCE_URL" '{project_name:$project,content:$content}')")"
    action_id="$(jq -er '.id' <<<"$response")"
    echo "fresh-deploy action: ${action_id}"
    wait_for_action "$action_id"
    ;;
  deploy-and-verify)
    "$0" ensure-setup
    echo "Preflight status"; "$0" status
    echo "Fresh deployment"; "$0" deploy
    echo "Post-deploy verification"; "$0" verify; "$0" errors
    ;;
  *) usage; exit 2 ;;
esac
