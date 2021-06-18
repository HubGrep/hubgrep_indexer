# crawler_controller

WIP


backend for various crawlers

## setup


create a config by copying `.env.dist` to `.env`, and add the missing values.

then start the service and database

    docker-compose up

run the initial migration in the container:

    docker-compose run --rm service /bin/bash
    flask cli init-db

also, you can import (and export) a list of hosting services:

    flask cli export-hosters
    flask cli import-hosters

## dev setup

and maybe you want to have a container to run cli commands:

    docker-compose run --rm service /bin/bash

in the container you have to run the db migrations

    # to create the migration files
    flask db migrate

    # to run the actual upgrade
    flask db upgrade




afterwards, set up your crawlers for the added platforms (see crawler repos)






