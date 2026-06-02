#compdef rig

_rig() {
  local -a commands
  commands=(
    'init:initialize Rig in the current repository'
    'delegate:delegate a task to a configured coding agent'
    'patch:create, inspect, and apply isolated agent patches'
    'history:list and inspect runs'
    'doctor:diagnose the local Rig setup'
    'harness:show companion Codex harness guidance'
    'mcp:expose Rig as MCP tools'
  )

  if (( CURRENT == 2 )); then
    _describe 'command' commands
    return
  fi

  if [[ "$words[2]" == "delegate" ]] || [[ "$words[2]" == "patch" && "$words[3]" == "create" ]]; then
    _arguments \
      '--task[task text]:task:' \
      '--task-file[task file path]:filename:_files' \
      '--dry-run[create artifacts without executing]' \
      '--timeout-seconds[override the configured agent timeout]:seconds:' \
      '--json[print JSON output]'
    return
  fi

  if [[ "$words[2]" == "init" ]]; then
    _arguments \
      '--force[reset generated Rig config and instructions]' \
      '--reset[reset selected Rig-owned config]:target:(config instructions all)'
    return
  fi

  if [[ "$words[2]" == "doctor" ]] || [[ "$words[2]" == "harness" ]] || [[ "$words[2]" == "history" && "$words[3]" != "show" ]]; then
    _arguments '--json[print JSON output]'
    return
  fi

  case "$words[2]" in
    patch)
      local -a patch_commands
      patch_commands=(
        'create:delegate a task in an isolated worktree and capture a patch'
        'show:show a captured patch'
        'apply:apply a captured patch'
        'prune:remove Rig-created worktrees'
      )
      _describe 'patch command' patch_commands
      ;;
    history)
      local -a history_commands
      history_commands=('show:show one run metadata and result')
      _describe 'history command' history_commands
      ;;
    mcp)
      local -a mcp_commands
      mcp_commands=('serve:run the Rig MCP server over stdio')
      _describe 'mcp command' mcp_commands
      ;;
  esac
}

_rig "$@"
