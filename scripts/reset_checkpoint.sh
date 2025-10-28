#!/usr/bin/env bash
set -e
CP_DIR=${1:-./spark-checkpoints}
read -p "This will delete checkpoint directory ${CP_DIR}. Are you sure? (y/N): " ans
if [[ "$ans" != "y" && "$ans" != "Y" ]]; then
  echo "Aborted."
  exit 0
fi
rm -rf "${CP_DIR}"
echo "Checkpoint dir ${CP_DIR} removed."
