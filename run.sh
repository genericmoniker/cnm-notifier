#!/usr/bin/env sh
#
# Build and run the Docker image.
#
# The `docker run` command uses the following options:
#
#   --rm                        Remove the container after exiting
#   --env-file .env             Load environment variables from the .env file
#   -it $(docker build -q .)    Build the image, then use it as a run target
#   $@                          Pass any arguments to the container

if [ -t 1 ]; then
    INTERACTIVE="-it"
else
    INTERACTIVE=""
fi

docker run \
    --rm \
    --env-file .env \
    $INTERACTIVE \
    $(docker build -q .) \
    "$@"
