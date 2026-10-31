#!/bin/bash
# Resolve rebase conflicts by taking the incoming version for all conflicted files
# Useful when conflicts are in generated build artifacts (HTML, PDFs, tags)

# Take incoming version for all conflicted files
for f in $(git diff --name-only --diff-filter=U); do
  echo "Resolving: $f"
  git checkout --theirs "$f" && git add "$f"
done

# Continue the rebase
git rebase --continue
