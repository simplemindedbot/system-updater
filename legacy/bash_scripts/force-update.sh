#!/bin/bash

# Force Update Script
# Manually trigger immediate system updates

echo "🔄 Force updating system packages..."
echo

# Run the update script directly
~/bin/update-system.sh

echo
echo "✅ Force update completed!"
echo
echo "Check results with: ~/bin/check-updates.sh"