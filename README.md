# Incandescent Server

Serverless application for headless home automation of various devices

Currently supports the following vendors:

- LightwaveRF Smart series (switches and dimmers) https://lightwaverf.com/


## Build and deploy

    sam build
    sam deploy --stack-name <name for the stack>

Deploy and watch for local changes:

    sam sync --stack-name <name for the stack> --watch


## Things to do/fix

- There's no housekeeping removing old devices
- Test creating a new stack from scratch
- Create a test->prod delivery pipeline https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/continuous-delivery-codepipeline-basic-walkthrough.html
- Lambda tests https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-using-automated-tests.html
- Evaluate IDEs ( VSCode https://github.com/aws/aws-toolkit-vscode)
- Separate secrets per account with runtime management, and more frequent secret rotation