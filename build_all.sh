#!/usr/bin/env bash
# Build every deck (each sub-folder with a build.py) then refresh the root
# landing page. Run from anywhere:  ./build_all.sh
set -euo pipefail
cd "$(dirname "$0")"

for b in */build.py; do
  dir="$(dirname "$b")"
  echo "== $dir =="
  ( cd "$dir" && python3 build.py )
done

python3 build_index.py
