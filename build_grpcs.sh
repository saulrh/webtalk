#!/usr/bin/env bash

poetry run python \
    -m grpc_tools.protoc \
    -Iprotos/ \
    --python_out=webtalk/protos \
    --pyi_out=webtalk/protos \
    --grpc_python_out=webtalk/protos \
    webtalk/webtalk.proto
