#!/bin/bash

DIR=$(cd $(dirname $0); pwd) 

cd $DIR

source ./args

export CLI=~/.guru/unity/guru_unity_cli.py
export PY=python3
export CLI_URL=https://raw.githubusercontent.com/castbox/guru-unity-cli/refs/heads/main/cmd/guru_unity_cli.py

# download cli file
if [ ! -f "$CLI" ]; then
  echo "download guru_unity_cli"
  curl -L $CLI_URL -o $CLI 
fi 

if [ "$RUN_MODE" = "install" ]; then
  # install sdk
  $PY $CLI install --version $VERSION  --proj "$PROJECT"
elif [ "$RUN_MODE" = "sync" ]; then
  # sync sdk into local
  $PY $CLI sync
elif [ "$RUN_MODE" = "debug" ]; then  
  $PY $CLI debug_source --branch $BRANCH
fi  



