#!/bin/bash
declare -a services=("protos")
DESTDIR='build'
for entry in "${services[@]}"/*
do
  if [ -d "${entry}" ]; then
    dir_name=$(basename ${entry})
    PY_OUT=${DESTDIR}/${dir_name}
    mkdir ${PY_OUT}
    touch ${PY_OUT}/__init__.py
    python3 -m grpc_tools.protoc \
    --proto_path=$entry/ \
    --python_out=$PY_OUT \
    --grpc_python_out=$PY_OUT \
    $entry/*.proto
  fi
done

for SERVICE in "${services[@]}"; do
    python3 -m grpc_tools.protoc \
        --proto_path=$SERVICE/ \
        --python_out=$DESTDIR \
        --grpc_python_out=$DESTDIR \
        $SERVICE/*.proto
done