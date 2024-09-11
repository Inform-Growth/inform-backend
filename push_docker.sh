#!/bin/bash

# Define the image name and tag
IMAGE_NAME="sakalthor/inform"
IMAGE_TAG="latest"

#!/bin/bash

# Set variables
DOCKER_IMAGE="sakalthor/inform"
DOCKER_TAG="latest"
REGISTRY_URL="your-registry-url"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Docker is not installed. Please install Docker and try again."
    exit 1
fi

# Build the Docker image
echo "Building Docker image..."
docker build -t $DOCKER_IMAGE:$DOCKER_TAG .

# Tag the image with the registry URL
echo "Tagging image..."
docker tag $DOCKER_IMAGE:$DOCKER_TAG $REGISTRY_URL/$DOCKER_IMAGE:$DOCKER_TAG

# Log in to the container registry
echo "Logging in to container registry..."
docker login $REGISTRY_URL

# Push the image to the registry
echo "Pushing image to registry..."
docker push $REGISTRY_URL/$DOCKER_IMAGE:$DOCKER_TAG

echo "Docker image has been successfully pushed to the registry."