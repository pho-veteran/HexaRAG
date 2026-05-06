#!/bin/sh
set -eu

until pg_isready -h postgres -U hexarag -d hexarag; do
  sleep 1
done

exec "$@"
