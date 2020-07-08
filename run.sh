#!/bin/bash
celery -A listener worker -l info &
mlflow ui -h 0.0.0.0 -p 8864 &
celery flower --address=0.0.0.0 --broker=amqp://admin:admin@$1//