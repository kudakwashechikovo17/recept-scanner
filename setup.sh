#!/bin/sh
# Simple helper script to install required packages
set -e

python -m pip install --upgrade pip || true

if ls wheels/*.whl >/dev/null 2>&1; then
  echo "Installing packages from local wheels..."
  pip install wheels/*.whl
else
  echo "Installing packages from requirements.txt..."
  if ! pip install -r requirements.txt; then
    echo "Failed to install packages. Ensure you have internet access or pre-downloaded wheels." >&2
    exit 1
  fi
fi
