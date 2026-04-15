#!/bin/bash
set -euo pipefail

INSTALL_DIR="${HOME}/.local/share/granola-sync"
REPO="https://github.com/jngo/granola-sync.git"

if ! command -v git &>/dev/null; then
    echo "Error: git is required — https://git-scm.com"
    exit 1
fi

if ! command -v python3 &>/dev/null; then
    echo "Error: Python 3 is required — https://python.org"
    exit 1
fi

if [ -d "${INSTALL_DIR}/.git" ]; then
    echo "Updating granola-sync..."
    git -C "${INSTALL_DIR}" pull --ff-only
else
    echo "Installing granola-sync..."
    git clone --depth 1 "${REPO}" "${INSTALL_DIR}"
fi

python3 "${INSTALL_DIR}/skills/granola-sync/granola.py" --setup

if [[ ":${PATH}:" != *":${HOME}/.local/bin:"* ]]; then
    echo ""
    echo "Add ~/.local/bin to your PATH:"
    echo "  echo 'export PATH=\"\$HOME/.local/bin:\$PATH\"' >> ~/.zshrc"
fi
