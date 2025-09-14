#!/bin/bash

# Setup Passwordless Sudo for Unattended Updates
# This script helps configure sudo access for automated system updates

echo "🔐 Setup Passwordless Sudo for Unattended Updates"
echo "================================================="
echo
echo "Your automated update system runs at 3 AM when you're not available"
echo "to enter passwords. This script helps set up secure unattended operation."
echo
echo "Available options:"
echo
echo "1. 📋 SAFEST: Use Touch ID + temporary sudo access"
echo "   - Requires you to authenticate once after login"
echo "   - Sudo access expires after inactivity"
echo "   - Most secure, but may need occasional re-authentication"
echo
echo "2. 🔑 MODERATE: Configure specific passwordless sudo for Homebrew"
echo "   - Only allows brew commands without password"
echo "   - More targeted security"
echo "   - Recommended for automated systems"
echo
echo "3. ⚠️  HIGH RISK: General passwordless sudo (NOT RECOMMENDED)"
echo "   - Allows all sudo commands without password"
echo "   - Security risk - not recommended"
echo
echo "4. 🚫 NO SETUP: Skip casks requiring sudo in unattended mode"
echo "   - Safest option"
echo "   - Some cask updates will be skipped"
echo "   - You can run 'updates now' manually when needed"
echo

read -p "Choose option (1-4): " choice

case $choice in
    1)
        echo
        echo "🔐 Setting up Touch ID + sudo access..."
        echo
        echo "This will:"
        echo "1. Enable Touch ID for sudo (if available)"
        echo "2. Show you how to maintain sudo access for unattended runs"
        echo
        
        # Check if Touch ID is available
        if ls /usr/lib/pam/pam_tid.so >/dev/null 2>&1; then
            echo "Touch ID is available. Adding to sudo configuration..."
            
            # Backup original file
            sudo cp /etc/pam.d/sudo /etc/pam.d/sudo.backup.$(date +%Y%m%d)
            
            # Add Touch ID to sudo if not already present
            if ! grep -q "pam_tid.so" /etc/pam.d/sudo; then
                echo "auth       sufficient     pam_tid.so" | sudo tee /etc/pam.d/sudo.new > /dev/null
                sudo cat /etc/pam.d/sudo >> /etc/pam.d/sudo.new
                sudo mv /etc/pam.d/sudo.new /etc/pam.d/sudo
                echo "✅ Touch ID enabled for sudo"
            else
                echo "✅ Touch ID already enabled for sudo"
            fi
        else
            echo "Touch ID not available on this system"
        fi
        
        echo
        echo "📋 For unattended operation, you can:"
        echo "1. Run 'sudo -v' after login to cache credentials"
        echo "2. Set up a login script to authenticate sudo automatically"
        echo "3. The system will skip sudo-requiring updates when credentials expire"
        echo
        ;;
        
    2)
        echo
        echo "🔑 Setting up passwordless sudo for Homebrew..."
        echo
        
        SUDOERS_FILE="/etc/sudoers.d/homebrew-updates"
        USERNAME=$(whoami)
        
        echo "This will create: $SUDOERS_FILE"
        echo "Allowing user '$USERNAME' to run brew commands without password"
        echo
        
        read -p "Continue? (y/n): " confirm
        if [[ $confirm == "y" || $confirm == "Y" ]]; then
            echo "# Allow $USERNAME to run brew commands without password for automated updates" | sudo tee "$SUDOERS_FILE" > /dev/null
            echo "$USERNAME ALL=(ALL) NOPASSWD: /opt/homebrew/bin/brew" | sudo tee -a "$SUDOERS_FILE" > /dev/null
            echo "$USERNAME ALL=(ALL) NOPASSWD: /usr/local/bin/brew" | sudo tee -a "$SUDOERS_FILE" > /dev/null
            
            # Set proper permissions
            sudo chmod 440 "$SUDOERS_FILE"
            
            # Validate sudoers file
            if sudo visudo -c; then
                echo "✅ Passwordless sudo for brew configured successfully"
                echo "✅ Sudoers file syntax is valid"
            else
                echo "❌ Error in sudoers configuration. Removing file..."
                sudo rm "$SUDOERS_FILE"
                exit 1
            fi
        else
            echo "Setup cancelled"
        fi
        ;;
        
    3)
        echo
        echo "⚠️  WARNING: This is NOT RECOMMENDED for security reasons"
        echo "This would allow ALL sudo commands without password"
        echo
        echo "Consider option 2 (specific Homebrew passwordless sudo) instead"
        echo
        read -p "Are you sure you want to continue? (type 'YES' to confirm): " confirm
        if [[ $confirm == "YES" ]]; then
            echo "Setting up general passwordless sudo (NOT RECOMMENDED)..."
            USERNAME=$(whoami)
            echo "$USERNAME ALL=(ALL) NOPASSWD: ALL" | sudo tee "/etc/sudoers.d/$USERNAME-nopasswd" > /dev/null
            sudo chmod 440 "/etc/sudoers.d/$USERNAME-nopasswd"
            echo "⚠️  WARNING: Passwordless sudo enabled for ALL commands"
            echo "⚠️  This is a significant security risk"
        else
            echo "Setup cancelled (good choice!)"
        fi
        ;;
        
    4)
        echo
        echo "🚫 No sudo setup - using safest approach"
        echo
        echo "The update system will:"
        echo "- ✅ Update all packages that don't require sudo"
        echo "- ✅ Skip cask updates requiring sudo in unattended mode"
        echo "- ✅ Log which updates were skipped"
        echo "- ✅ Allow you to run 'updates now' manually when needed"
        echo
        echo "This is the most secure option."
        echo "No changes made to sudo configuration."
        ;;
        
    *)
        echo "Invalid option. Exiting..."
        exit 1
        ;;
esac

echo
echo "🎯 Testing current sudo access..."
if sudo -n true 2>/dev/null; then
    echo "✅ Current sudo access: AVAILABLE"
    echo "   Unattended updates will work until sudo access expires"
else
    echo "❌ Current sudo access: NOT AVAILABLE"
    echo "   Cask updates requiring sudo will be skipped in unattended mode"
fi

echo
echo "🧪 You can test the system by running: updates now"
echo "📋 Check system status anytime with: updates check"
echo "📖 Full documentation: ~/bin/UPDATE_SYSTEM_README.md"