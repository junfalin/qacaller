#!/bin/bash
mlflow ui -h 0.0.0.0 -p 8864 &
python listener.py $RUN_NAME
