#!/usr/bin/env bash

set -e

export PYTHONPATH=":fast_channels"


# Cleaning existing cache:
if [ "$1" == "-nc" ]; then
  rm -rf .mypy_cache
fi


mypy fast_channels
