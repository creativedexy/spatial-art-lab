#!/bin/zsh
set -e
M7="/Users/user/Projects/3D Design/experiments/002-living-map/generate/m7"
id=$1; args=()
while IFS= read -r r; do args+=(-i "$r"); done < "$M7/prompts/$id.refs"
codex exec -s workspace-write -C "/Users/user/Projects/3D Design" -c 'model_reasoning_effort="medium"' "${args[@]}" - < "$M7/prompts/$id.md" > "$M7/out/$id.log" 2>&1
echo "$id done"
