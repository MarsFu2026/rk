# create_prs.sh
#!/bin/bash

REPO="你的账号/frank-ai-concurrency-test"
BASE="master"
PR_COUNT=3  # 同时创建5个PR

for i in $(seq 1 $PR_COUNT); do
  BRANCH="test-pr-$i"
  
  # 创建分支并push
  git checkout -b $BRANCH master
  echo "test change $i - $(date)" > test_$i.txt
  git add . && git commit -m "test: PR $i"
  git push origin $BRANCH
  
  # 用GitHub CLI创建PR
  gh pr create \
    --repo $REPO \
    --base $BASE \
    --head $BRANCH \
    --title "Test PR $i" \
    --body "Concurrency test PR $i"
  
  git checkout master
done

echo "Created $PR_COUNT PRs simultaneously"