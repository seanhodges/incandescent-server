# Incandescent Server

Serverless application using AWS SAM for headless home automation of various devices.

Currently supports the following vendors:

- LightwaveRF Smart series (switches and dimmers) https://lightwaverf.com/


## Build and deploy

1. Copy secrets.example.yml to secrets.yml and update the secret values.

2. Deploy the stack for the first time:

    sam build
    sam deploy --stack-name <name for the stack>

3. Deploy and watch for local changes:

    sam sync --stack-name <name for the stack> --watch
