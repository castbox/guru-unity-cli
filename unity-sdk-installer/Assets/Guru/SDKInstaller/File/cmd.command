#!/bin/bash

DIR=$(cd $(dirname $0); pwd) 

cd $DIR

source ./args

CLI=~/.guru/unity/guru_unity_cli.py

if [ ! -f "$CLI" ]; then

  echo "download guru_unity_cli"
  # curl -L https://raw.githubusercontent.com/castbox/guru-unity-cli/refs/heads/main/cmd/guru_unity_cli.py?token=GHSAT0AAAAAACUSDGU7I7O6MQZF6RH3MPO4ZZUUINA -o $CLI 
  
fi 

if [ "$RUN_MODE" = "install" ]; then
  
  python3 ~/.guru/unity/guru_unity_cli.py install --version $SDK_VERSION  --unity_proj "$UNITY_PROJECT"
  
fi  



