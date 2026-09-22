#!/bin/zsh
# Phase 12 M2: one free Codex image_gen run per frame. Usage: run_boards.sh <id>
set -e
M2="/Users/user/Projects/3D Design/experiments/002-living-map/generate/m2"
id=$1
args=()
for r in $(python3 -c "import json,os;[print(os.path.abspath(os.path.join('$M2',p)).replace(' ',' ')) for p in json.load(open('$M2/prompts/$id.refs.json'))]"); do
  args+=(-i "${r//$' '/ }")
done
codex exec -s workspace-write -C "/Users/user/Projects/3D Design" -c 'model_reasoning_effort="medium"' "${args[@]}" - < "$M2/prompts/$id.md" > "$M2/boards/$id.log" 2>&1
echo "$id done: $(ls "$M2/boards" | grep -c "^$id")"
