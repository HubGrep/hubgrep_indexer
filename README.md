# crawler_controller

WIP


backend for various crawlers


## dev setup

create a config by copying `.env.dist` to `.env`, and add the missing values.

then start the service and database

    docker-compose up


and maybe you want to have a container to run cli commands:

    docker-compose run --rm service /bin/bash

in the container you have to run the db migrations

    # to create the migration files
    flask db migrate

    # to run the actual upgrade
    flask db upgrade


you can add platforms like so:

    flask cli add-platform github 'https://api.github.com/'
    flask cli del-platform github 'https://api.github.com/'


afterwards, set up your crawlers for the added platforms (see crawler repos)






