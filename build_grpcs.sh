#!/usr/bin/env bash

poetry run python \
    -m grpc_tools.protoc \
    -I. \
    --python_out=. \
    --pyi_out=. \
    --grpc_python_out=. \
    webtalk/protos/webtalk.proto
