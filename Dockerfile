FROM python:3.8-slim-buster

# extra setup to compile psycopg2 if neccessary
RUN apt-get update && apt-get install libpq-dev python-dev gcc build-essential -y

WORKDIR /var/task

RUN echo "PS1='${debian_chroot:+($debian_chroot)}\u@\h:\w\$ '" >> /root/.bashrc

# prepare for virtualenv
RUN echo 'if [ ! -d "env_docker" ]; then' >> /root/.bashrc && \
    echo '    python3 -m venv env_docker' >> /root/.bashrc && \
    echo 'fi' >> /root/.bashrc && \
    echo '' >> /root/.bashrc && \
    echo 'source env_docker/bin/activate' >> /root/.bashrc


