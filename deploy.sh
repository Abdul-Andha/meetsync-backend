#!/bin/bash

git pull origin main

docker-compose down
docker-compose up --build -d

echo "Deployment complete!"