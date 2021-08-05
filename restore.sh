#!/bin/bash

set -e
set -x

function _clean_db() {
    docker-compose stop postgres
    docker-compose rm -f postgres
    docker-compose up -d postgres
    until docker-compose exec postgres pg_isready ; do sleep 1 ; done
}


docker_compose=docker-compose  #/usr/local/bin/docker-compose
results_dir=results/
backup_dir=${1}

source .env

usage="${0} <backup_path>"

if [ -z "$1" ]; then
  echo "usage: $usage"
  exit 0
fi

# restore exports
mkdir -p ${results_dir}
cp ${backup_dir}/${results_dir}/* ${results_dir} -r

# restore postgres
_clean_db
cat ${backup_dir}/postgres_backup.sql.gz | gunzip | docker-compose exec -T postgres psql -U $POSTGRES_USER


cat ${backup_dir}/redis_backup.rdb.gz | gunzip | docker-compose exec -T redis  bash -ic 'dd of=/data/dump.rdb'


