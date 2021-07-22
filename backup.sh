#!/bin/bash

set -e
set -x

docker_compose=docker-compose  #/usr/local/bin/docker-compose
results_dir=results/
backup_dir=${1}

source .env

usage="${0} <backup_path>"

if [ -z "$1" ]; then
  echo "usage: $usage"
  exit 0
fi

# make backup dir
mkdir -p ${backup_dir}

# delete old export files, mark as deleted in db
$docker_compose run --rm hubgrep_indexer bash -ic 'flask cli prune-exports --keep 3'

# redis
## trigger save to disc
$docker_compose exec redis redis-cli save
## backup data file
$docker_compose exec redis cat /data/dump.rdb | gzip > ${backup_dir}/redis_backup.rdb.gz


# postgres
$docker_compose exec -T postgres /usr/bin/pg_dump -U $POSTGRES_USER $POSTGRES_DB | gzip  > ${backup_dir}postgres_backup.sql.gz

# local
cp ${results_dir} ${backup_dir} -r
