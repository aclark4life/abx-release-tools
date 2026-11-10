#!/usr/bin/env bash
# Log the container runtime in to the DevProd ECR registry that holds the
# Garasign and SilkBomb images.
#
# Assume the ECR read-only role with ec2.assume_role in the project config
# first, and pass the session credentials in through the environment:
# ec2.assume_role is an Evergreen built-in and has no shell equivalent.
#
# Optional environment:
#   ECR_REGISTRY   Registry to log in to. Defaults to the DevProd registry.
#   ECR_REGION     Registry region. Default us-east-1.
#   CONTAINER_CMD  docker or podman. Default docker.
set -euo pipefail

ECR_REGISTRY="${ECR_REGISTRY:-901841024863.dkr.ecr.us-east-1.amazonaws.com}"
ECR_REGION="${ECR_REGION:-us-east-1}"
CONTAINER_CMD="${CONTAINER_CMD:-docker}"

# pipefail matters here: without it a failing aws call is masked by the exit
# status of the login it pipes into.
aws ecr get-login-password --region "$ECR_REGION" \
    | "$CONTAINER_CMD" login --username AWS --password-stdin "$ECR_REGISTRY"
