#!/bin/bash

set -e
set -x

docker_compose_file=docker-compose.prod.yml
results_dir=results/
backup_dir=${1}


function _clean_db() {
    docker-compose -f ${docker_compose_file} stop postgres
    docker-compose -f ${docker_compose_file} rm -f postgres
    docker-compose -f ${docker_compose_file} up -d postgres
    until docker-compose -f ${docker_compose_file} exec postgres pg_isready ; do sleep 1 ; done
}



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
cat ${backup_dir}/postgres_backup.sql.gz | gunzip | docker-compose -f ${docker_compose_file} exec -T postgres psql -U $POSTGRES_USER


cat ${backup_dir}/redis_backup.rdb.gz | gunzip | docker-compose -f ${docker_compose_file} exec -T redis  bash -ic 'dd of=/data/dump.rdb'


