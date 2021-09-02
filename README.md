
sam package -t .\template.yml --s3-bucket aws-sam-cli-managed-default-samclisourcebucket-1uhmeo0ymx86b --output-template-file packaged-template.yaml
sam deploy --template-file packaged-template.yaml --stack-name test-stack