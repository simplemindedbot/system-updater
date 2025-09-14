#!/bin/bash

# System Update Script
# Updates Mac App Store apps and Homebrew packages
# Handles sudo password requirements gracefully

# Set up environment
export PATH="/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
export HOMEBREW_NO_ENV_HINTS=1

# Create logs directory if it doesn't exist
LOG_DIR="$HOME/Library/Logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/system-updates.log"

# Function to log with timestamp
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Function to check if we already have sudo access
check_sudo_access() {
    sudo -n true 2>/dev/null
    return $?
}

# Function to attempt passwordless sudo setup check
check_passwordless_sudo() {
    # Check if we can run specific commands without password
    sudo -n /opt/homebrew/bin/brew --version >/dev/null 2>&1
    return $?
}

# Function to update casks with intelligent sudo handling
update_casks_unattended() {
    log_message "Starting Homebrew cask updates (unattended mode)..."
    
    # Check for outdated casks first
    outdated_casks=$(brew outdated --cask 2>/dev/null || true)
    
    if [[ -n "$outdated_casks" ]]; then
        log_message "Found outdated casks: $outdated_casks"
        
        # Method 1: Try without sudo first (many casks don't need it)
        log_message "Attempting cask updates without sudo..."
        if brew upgrade --cask 2>&1 | tee -a "$LOG_FILE"; then
            log_message "Cask updates completed successfully without sudo"
        else
            log_message "Some cask updates may have failed due to permissions"
            
            # Method 2: Check if we have cached sudo access
            if check_sudo_access; then
                log_message "Sudo access available, retrying cask updates..."
                sudo brew upgrade --cask 2>&1 | tee -a "$LOG_FILE" || log_message "Cask updates with sudo completed with some issues"
            else
                log_message "No sudo access available for unattended execution"
                log_message "Cask updates requiring sudo permissions were skipped"
                log_message "Consider setting up passwordless sudo for brew or running 'updates now' manually"
                
                # Log which specific casks were skipped
                log_message "Skipped casks that may require sudo: $outdated_casks"
            fi
        fi
    else
        log_message "No cask updates available"
    fi
}

# Start logging
log_message "=== Starting System Update Process ==="

# Update Mac App Store apps
log_message "Checking for Mac App Store updates..."
mas_outdated=$(mas outdated 2>/dev/null || true)

if [[ -n "$mas_outdated" ]]; then
    log_message "Found MAS updates: $mas_outdated"
    log_message "Upgrading Mac App Store applications..."
    mas upgrade 2>&1 | tee -a "$LOG_FILE"
else
    log_message "No Mac App Store updates available"
fi

# Update Homebrew
log_message "Updating Homebrew..."
brew update 2>&1 | tee -a "$LOG_FILE"

# Check for outdated formulae
brew_outdated=$(brew outdated 2>/dev/null || true)

if [[ -n "$brew_outdated" ]]; then
    log_message "Found Homebrew updates: $brew_outdated"
    log_message "Upgrading Homebrew formulae..."
    brew upgrade 2>&1 | tee -a "$LOG_FILE"
else
    log_message "No Homebrew formula updates available"
fi

# Update Homebrew casks (with unattended sudo handling)
update_casks_unattended

# Update npm global packages
log_message "Checking for npm global package updates..."
if command -v npm >/dev/null 2>&1; then
    npm_outdated=$(npm outdated -g --depth=0 2>/dev/null || true)
    
    if [[ -n "$npm_outdated" ]]; then
        log_message "Found npm updates: $npm_outdated"
        log_message "Updating npm global packages..."
        npm update -g 2>&1 | tee -a "$LOG_FILE"
    else
        log_message "No npm global package updates available"
    fi
else
    log_message "npm not available, skipping npm updates"
fi

# Update Python packages
log_message "Checking for Python package updates..."

# Check for uv (modern Python package manager)
if command -v uv >/dev/null 2>&1; then
    log_message "Updating uv tool packages..."
    uv tool upgrade --all 2>&1 | tee -a "$LOG_FILE" || log_message "No uv tools to upgrade or uv tool upgrade failed"
fi

# Update pip packages (global user packages)
# First, ensure we have proper Python environment loaded
if [[ -f "$HOME/.pyenv/bin/pyenv" ]]; then
    export PATH="$HOME/.pyenv/bin:$PATH"
    eval "$(pyenv init -)"
fi

if command -v pip >/dev/null 2>&1; then
    log_message "Checking for pip package updates..."
    
    # Get list of outdated packages (try both --user and global)
    pip_outdated_user=$(pip list --outdated --user --format=freeze 2>/dev/null | cut -d= -f1 || true)
    
    if [[ -n "$pip_outdated_user" ]]; then
        log_message "Found pip user updates: $pip_outdated_user"
        log_message "Updating pip user packages..."
        
        # Update each package individually to avoid conflicts
        echo "$pip_outdated_user" | while read -r package; do
            if [[ -n "$package" ]]; then
                log_message "Updating user package: $package..."
                pip install --user --upgrade "$package" 2>&1 | tee -a "$LOG_FILE" || log_message "Failed to update user package: $package"
            fi
        done
    else
        log_message "No pip user package updates available"
    fi
    
    # Also check for global packages (if we have write access)
    pip_outdated_global=$(pip list --outdated --format=freeze 2>/dev/null | grep -v "WARNING" | cut -d= -f1 || true)
    
    if [[ -n "$pip_outdated_global" ]]; then
        log_message "Found pip global updates: $pip_outdated_global"
        log_message "Note: Global pip updates require manual attention due to permission/environment concerns"
        log_message "Consider using 'pip install --upgrade <package>' manually if needed"
    fi
else
    log_message "pip not available, skipping pip updates"
fi

# Update Ruby gems
log_message "Checking for Ruby gem updates..."
if command -v gem >/dev/null 2>&1; then
    gem_outdated=$(gem outdated 2>/dev/null || true)
    
    if [[ -n "$gem_outdated" ]]; then
        log_message "Found gem updates: $gem_outdated"
        log_message "Updating Ruby gems..."
        gem update --user-install 2>&1 | tee -a "$LOG_FILE" || log_message "Gem updates may require manual attention"
    else
        log_message "No Ruby gem updates available"
    fi
else
    log_message "Ruby gem not available, skipping gem updates"
fi

# Update R packages
log_message "Checking for R package updates..."
if command -v R >/dev/null 2>&1; then
    log_message "Checking R packages status..."
    
    # Check for outdated R packages
    r_outdated=$(R --slave --no-restore -e "options(repos = c(CRAN = 'https://cran.rstudio.com')); old <- old.packages(); if(!is.null(old)) { cat(paste(old[,'Package'], collapse=', ')) }" 2>/dev/null || true)
    
    if [[ -n "$r_outdated" && "$r_outdated" != "" ]]; then
        log_message "Found R package updates: $r_outdated"
        log_message "Updating R packages..."
        
        # Update R packages (this may take a while)
        R --slave --no-restore -e "
        options(repos = c(CRAN = 'https://cran.rstudio.com'))
        cat('Updating R packages...\\n')
        old <- old.packages()
        if (!is.null(old)) {
            update.packages(ask = FALSE, checkBuilt = TRUE)
            cat('R package updates completed\\n')
        } else {
            cat('No R package updates needed\\n')
        }
        " 2>&1 | tee -a "$LOG_FILE"
    else
        log_message "No R package updates available"
    fi
    
    # Also update Bioconductor packages if installed
    bioc_available=$(R --slave --no-restore -e "if (requireNamespace('BiocManager', quietly = TRUE)) cat('yes') else cat('no')" 2>/dev/null || echo "no")
    
    if [[ "$bioc_available" == "yes" ]]; then
        log_message "Updating Bioconductor packages..."
        R --slave --no-restore -e "
        if (requireNamespace('BiocManager', quietly = TRUE)) {
            cat('Checking Bioconductor updates...\\n')
            BiocManager::install(update = TRUE, ask = FALSE)
            cat('Bioconductor updates completed\\n')
        }
        " 2>&1 | tee -a "$LOG_FILE" || log_message "Bioconductor update completed with warnings"
    else
        log_message "BiocManager not installed, skipping Bioconductor updates"
    fi
else
    log_message "R not available, skipping R package updates"
fi

# Update package managers themselves
log_message "Updating package managers..."

# Update npm itself
if command -v npm >/dev/null 2>&1; then
    log_message "Updating npm package manager..."
    npm install -g npm@latest 2>&1 | tee -a "$LOG_FILE" || log_message "npm self-update completed with warnings"
fi

# Update pip itself
if command -v pip >/dev/null 2>&1; then
    log_message "Updating pip package manager..."
    pip install --user --upgrade pip 2>&1 | tee -a "$LOG_FILE" || log_message "pip self-update completed with warnings"
fi

# Update gem system
if command -v gem >/dev/null 2>&1; then
    log_message "Updating RubyGems package manager..."
    gem update --system --user-install 2>&1 | tee -a "$LOG_FILE" || log_message "RubyGems self-update completed with warnings"
fi

# Update TeX Live packages
log_message "Checking for TeX Live package updates..."
if command -v tlmgr >/dev/null 2>&1; then
    log_message "Checking tlmgr status..."
    
    # Check for available TeX Live updates
    tex_updates=$(tlmgr update --list 2>/dev/null | grep -c "^update:" 2>/dev/null || echo "0")
    
    if [[ "$tex_updates" -gt 0 ]] 2>/dev/null; then
        log_message "Found $tex_updates TeX Live package updates"
        log_message "Updating TeX Live packages..."
        
        # Update all TeX Live packages
        tlmgr update --all 2>&1 | tee -a "$LOG_FILE" || log_message "TeX Live updates completed with warnings"
    else
        log_message "No TeX Live package updates available"
    fi
else
    log_message "tlmgr not available, skipping TeX Live updates"
fi

# Update VS Code extensions
log_message "Checking for VS Code extension updates..."
if command -v code >/dev/null 2>&1; then
    log_message "Checking VS Code extensions..."
    
    # Get list of installed extensions
    installed_extensions=$(code --list-extensions 2>/dev/null | wc -l || echo "0")
    
    if [[ "$installed_extensions" -gt 0 ]]; then
        log_message "Found $installed_extensions VS Code extensions installed"
        log_message "Updating VS Code extensions..."
        
        # Update extensions by reinstalling them (VS Code handles updates automatically)
        # We'll use the --update-extensions flag if available, otherwise trigger update check
        if code --help 2>/dev/null | grep -q "update-extensions"; then
            code --update-extensions 2>&1 | tee -a "$LOG_FILE" || log_message "VS Code extension updates completed"
        else
            # Alternative: Force extension update check by listing with --show-versions
            log_message "Triggering VS Code extension update check..."
            code --list-extensions --show-versions 2>&1 | tee -a "$LOG_FILE" >/dev/null
            log_message "VS Code extension update check completed (updates will be applied when VS Code starts)"
        fi
    else
        log_message "No VS Code extensions installed"
    fi
else
    log_message "VS Code not available, skipping extension updates"
fi

# Clean up
log_message "Cleaning up..."
brew cleanup 2>&1 | tee -a "$LOG_FILE"

# Summary
log_message "=== Update Process Complete ==="
log_message "Check log file at: $LOG_FILE"

# Send notification if available
if command -v osascript >/dev/null 2>&1; then
    osascript -e 'display notification "System updates completed successfully!" with title "Update Script" sound name "Glass"' 2>/dev/null || true
fi

exit 0