#!/bin/bash

cd "$(dirname $(realpath $0))"

stdbuf --output=L ./start > $HOME/stdout.log 2> $HOME/stderr.log
