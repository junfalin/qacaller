#!/bin/bash
mlflow ui -h 0.0.0.0&
python listener.py --run $RUN_NAME
