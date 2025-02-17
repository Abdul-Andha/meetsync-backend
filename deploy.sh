#!/bin/bash

git pull origin main

sudo docker-compose down
sudo docker-compose up --build -d --force-recreate

echo "Deployment complete!"
