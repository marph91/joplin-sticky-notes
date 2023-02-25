#!/bin/sh

black --check .
flake8 .
mypy .
