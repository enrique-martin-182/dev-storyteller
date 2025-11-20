#!/bin/bash

# Build the Docker image
echo "Building Docker image for backend..."
docker build -t dev-storyteller-backend .

# Run the Docker container
echo "Running Docker container..."
docker run -d --name dev-storyteller-backend-container -p 8000:8000 dev-storyteller-backend

echo "Backend deployed and running on port 8000."
echo "To stop the container, run: docker stop dev-storyteller-backend-container"
echo "To remove the container, run: docker rm dev-storyteller-backend-container"
echo "To view logs, run: docker logs dev-storyteller-backend-container"
