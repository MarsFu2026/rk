# create_prs.sh
#!/bin/bash

REPO="MarsFu2026/rk"
BASE="main"
PR_COUNT=10  # 同时创建5个PR

for i in $(seq 1 $PR_COUNT); do
  BRANCH="mars-pr-$i"
  
  # 创建分支并push
  git checkout -b $BRANCH main
  echo "test change $i - $(date)" > mars_$i.txt
  git add . && git commit -m "test: PR $i"
  git push origin $BRANCH
  
  # 用GitHub CLI创建PR
  gh pr create \
    --repo $REPO \
    --base $BASE \
    --head $BRANCH \
    --title "Mars PR $i" \
    --body "Concurrency test PR $i"
  
  git checkout main
done

echo "Created $PR_COUNT PRs simultaneously"