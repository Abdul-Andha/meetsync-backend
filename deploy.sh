#!/bin/bash

ENV = $1

if [ "$ENV" = "prod" ]; then
    export APP_ENV=dev
else
    export APP_ENV=prod
fi

git pull origin main

sudo docker-compose down
sudo docker-compose up --build -d --force-recreate

echo "Deployment complete!"
