#!/bin/bash

echo "Raven is running..."
echo "Please input tail -f logs/collect.log to monitor the logs."
nohup python3 "$RAVEN_HOME"/raven.py &

sleep 1
tail -f logs/info.log
