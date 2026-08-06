#!/bin/bash
# filepath: setup-hooks.sh
cp hooks/commit-msg .git/hooks/commit-msg
cp hooks/pre-push .git/hooks/pre-push
chmod +x .git/hooks/commit-msg
chmod +x .git/hooks/pre-push
echo "Git hooks installed successfully!"
