# crawler_api


## Requirements

- docker
- docker-compose
 
### setup in intellij

for setup in intellij i recommend to have a separate virtualenv, since its not fun to make intellij work with the environment of the docker container.

this would be something like
`virtuelenv -p python3.6 env_local`

then activate it with
`source env_local/bin/activate` (on bash)
`. env_local/bin/activate` (on fish)

in intellij you can point the interpreter to `env_local/bin/python`


## getting a shell
 
    `docker-compose run --rm service /bin/bash`
 
on first start you should install your requirements (which is at least zappa and flask) and save it to requirements.txt

`pip install zappa flask`
`pip freeze > requirements.txt`

 
## starting the service for local dev

when you have a requirements file, you can start the service for localdev

    `docker-compose up`
 
 
## testing

`python -m unittest`

or use pytest and just run

`pytest`


## deploying

### first deployment

on first deploy of the stage, you have to run
`zappa deploy <stage>` (where stage is `dev` or `prod`)

to update the lambda

    `zappa update <stage>`
        
