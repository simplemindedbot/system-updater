#!/bin/bash

# Check Updates Script
# View recent system update logs and status

LOG_FILE="$HOME/Library/Logs/system-updates.log"
STDOUT_LOG="$HOME/Library/Logs/system-updates-stdout.log"
STDERR_LOG="$HOME/Library/Logs/system-updates-stderr.log"

echo "=== System Update Status ==="
echo

# Check if LaunchAgent is loaded
if launchctl list | grep -q com.user.systemupdater; then
    echo "✅ LaunchAgent is loaded and scheduled"
else
    echo "❌ LaunchAgent is NOT loaded"
fi

echo

# Show recent log entries
if [[ -f "$LOG_FILE" ]]; then
    echo "=== Recent Update Activity (last 20 lines) ==="
    tail -20 "$LOG_FILE"
    echo
    
    echo "=== Last Update Summary ==="
    echo "Log file size: $(wc -l < "$LOG_FILE") lines"
    echo "Last modified: $(stat -f %Sm "$LOG_FILE")"
else
    echo "❌ No update log found at $LOG_FILE"
fi

echo

# Check for any errors
if [[ -f "$STDERR_LOG" && -s "$STDERR_LOG" ]]; then
    echo "⚠️  Recent errors found:"
    tail -10 "$STDERR_LOG"
else
    echo "✅ No recent errors"
fi

echo

# Show current package status
echo "=== Current Update Status ==="
echo "Mac App Store outdated packages:"
mas outdated 2>/dev/null || echo "  None or mas not available"

echo
echo "Homebrew outdated packages:"
brew outdated 2>/dev/null || echo "  None or brew not available"

echo
echo "Homebrew outdated casks:"
brew outdated --cask 2>/dev/null || echo "  None or brew not available"

echo
echo "npm outdated global packages:"
npm outdated -g --depth=0 2>/dev/null || echo "  None or npm not available"

echo
echo "Python pip outdated packages (user):"
# Load pyenv if available
if [[ -f "$HOME/.pyenv/bin/pyenv" ]]; then
    export PATH="$HOME/.pyenv/bin:$PATH"
    eval "$(pyenv init -)" 2>/dev/null || true
fi
pip list --outdated --user 2>/dev/null || echo "  None or pip not available"

echo
echo "uv tool packages:"
if command -v uv >/dev/null 2>&1; then
    uv tool list 2>/dev/null || echo "  No uv tools installed"
else
    echo "  uv not available"
fi

echo
echo "Ruby gem outdated packages:"
gem outdated 2>/dev/null || echo "  None or gem not available"

echo
echo "R package outdated packages:"
if command -v R >/dev/null 2>&1; then
    R --slave --no-restore -e "options(repos = c(CRAN = 'https://cran.rstudio.com')); old <- old.packages(); if(!is.null(old)) { cat(paste(old[,'Package'], '(', old[,'Installed'], ' -> ', old[,'ReposVer'], ')', sep='', collapse='\n')) } else { cat('  No updates available') }" 2>/dev/null || echo "  Error checking R packages"
else
    echo "  R not available"
fi

echo
echo "Bioconductor packages status:"
if command -v R >/dev/null 2>&1; then
    bioc_status=$(R --slave --no-restore -e "if (requireNamespace('BiocManager', quietly = TRUE)) cat('BiocManager installed') else cat('Not installed')" 2>/dev/null || echo "Error")
    echo "  $bioc_status"
else
    echo "  R not available"
fi

echo
echo "Package manager versions:"
if command -v npm >/dev/null 2>&1; then
    npm_version=$(npm --version 2>/dev/null || echo "Error")
    echo "  npm: $npm_version"
fi
if command -v pip >/dev/null 2>&1; then
    pip_version=$(pip --version 2>/dev/null | cut -d' ' -f2 || echo "Error")
    echo "  pip: $pip_version"
fi
if command -v gem >/dev/null 2>&1; then
    gem_version=$(gem --version 2>/dev/null || echo "Error")
    echo "  RubyGems: $gem_version"
fi

echo
echo "TeX Live package updates:"
if command -v tlmgr >/dev/null 2>&1; then
    tex_updates=$(tlmgr update --list 2>/dev/null | grep -c "^update:" 2>/dev/null || echo "0")
    if [[ "$tex_updates" -gt 0 ]] 2>/dev/null; then
        echo "  $tex_updates packages need updating"
        tlmgr update --list 2>/dev/null | grep "^update:" | head -3 | sed 's/^/    /'
        if [[ "$tex_updates" -gt 3 ]]; then
            echo "    ... and $((tex_updates - 3)) more"
        fi
    else
        echo "  No updates available"
    fi
else
    echo "  tlmgr not available"
fi

echo
echo "VS Code extensions status:"
if command -v code >/dev/null 2>&1; then
    extension_count=$(code --list-extensions 2>/dev/null | wc -l || echo "0")
    echo "  $extension_count extensions installed"
    if [[ "$extension_count" -gt 0 ]]; then
        echo "  Recent extensions:"
        code --list-extensions 2>/dev/null | head -3 | sed 's/^/    /'
        if [[ "$extension_count" -gt 3 ]]; then
            echo "    ... and $((extension_count - 3)) more"
        fi
    fi
else
    echo "  VS Code not available"
fi

echo
echo "=== Manual Commands ==="
echo "View full log: less '$LOG_FILE'"
echo "Run update now: ~/bin/update-system.sh"
echo "Force update now: ~/bin/force-update.sh"
echo "Trigger via LaunchAgent: launchctl start com.user.systemupdater"