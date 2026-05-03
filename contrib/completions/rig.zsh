#compdef rig

_rig() {
  local -a commands
  commands=(
    'init:initialize Rig in the current repository'
    'run:run an agent'
    'list:list recent runs'
    'show:show a run'
    'worktree:manage isolated worktree run changes'
    'history:inspect run history'
    'guide:generate setup guidance'
    'env:inspect the agent environment'
  )

  if (( CURRENT == 2 )); then
    _describe 'command' commands
    return
  fi

  if [[ "$words[2]" == "run" ]] || [[ "$words[2]" == "worktree" && "$words[3]" == "run" ]]; then
    _arguments \
      '--task[task text]:task:' \
      '--task-file[task file path]:filename:_files' \
      '--dry-run[create artifacts without executing]'
    return
  fi

  case "$words[2]" in
    worktree)
      local -a worktree_commands
      worktree_commands=(
        'run:run an agent in an isolated worktree'
        'show:show captured changes'
        'apply:apply captured changes'
        'prune:remove Rig-created worktrees'
      )
      _describe 'worktree command' worktree_commands
      ;;
    history)
      local -a history_commands
      history_commands=(
        'list:list recent runs'
        'show:show a run'
        'complete:complete a waiting manual run'
        'fail:fail a waiting manual run'
      )
      _describe 'history command' history_commands
      ;;
    guide)
      local -a guide_commands
      guide_commands=('agents:generate an AGENTS.md snippet')
      _describe 'guide command' guide_commands
      ;;
    env)
      local -a env_commands
      env_commands=(
        'doctor:diagnose environment'
        'plan:show environment plan'
        'bootstrap:create Rig-owned environment files'
      )
      _describe 'env command' env_commands
      ;;
  esac
}

_rig "$@"
