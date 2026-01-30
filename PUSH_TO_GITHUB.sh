#!/bin/bash

# Script to push repository to GitHub
# Usage: ./PUSH_TO_GITHUB.sh <github_username> <token>

if [ $# -lt 2 ]; then
    echo "Usage: ./PUSH_TO_GITHUB.sh <github_username> <token>"
    echo ""
    echo "Example:"
    echo "  ./PUSH_TO_GITHUB.sh jokken79 github_pat_xxxxx"
    exit 1
fi

GITHUB_USER=$1
TOKEN=$2
REPO_NAME="UNS-Shain-Daicho-Manager"

echo "=========================================="
echo "Pushing to GitHub"
echo "==========================================" 
echo "User: $GITHUB_USER"
echo "Repo: $REPO_NAME"
echo ""

# Try to create repository via API
echo "[1/3] Creating repository on GitHub..."
RESPONSE=$(curl -s -X POST \
  -H "Authorization: token $TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/user/repos \
  -d "{\"name\":\"$REPO_NAME\",\"description\":\"UNS 社員台帳 Manager - Complete Employee Registry Management System\",\"private\":false,\"auto_init\":false}")

if echo "$RESPONSE" | grep -q "\"id\""; then
    echo "✅ Repository created successfully!"
    REPO_URL="https://github.com/$GITHUB_USER/$REPO_NAME.git"
else
    # Repository might already exist
    echo "⚠️  Repository creation note (might already exist)"
    REPO_URL="https://github.com/$GITHUB_USER/$REPO_NAME.git"
fi

echo ""
echo "[2/3] Adding remote origin..."
git remote remove origin 2>/dev/null || true
git remote add origin "$REPO_URL"
echo "✅ Remote added: $REPO_URL"

echo ""
echo "[3/3] Pushing to GitHub..."
git push -u origin master

echo ""
echo "=========================================="
echo "✅ Done! Repository pushed to GitHub"
echo "=========================================="
echo "View at: $REPO_URL"
