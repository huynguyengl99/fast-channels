#!/usr/bin/env bash

if [ "$1" == "--fix" ]; then
  ruff check . --fix && black ./fast_channels && toml-sort ./*.toml
else
  ruff check . && black ./fast_channels --check && toml-sort ./*.toml --check
fi
