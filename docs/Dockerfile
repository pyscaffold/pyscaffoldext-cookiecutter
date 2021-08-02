# Container with OS-level dependencies (e.g. C-libraries)
# to run the documentation tasks on tox.ini (used for CI)
FROM python:3.9-buster

RUN apt-get update && \
    apt-get install -y git enchant
