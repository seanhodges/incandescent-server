
sam package -t template.yml --s3-bucket incandescent-server-deploy-bucket --output-template-file packaged-template.yaml
sam deploy --template-file packaged-template.yaml --stack-name test-stack
aws dynamodb list-tables
aws dynamodb batch-write-item --request-items file://docs/device-db-test-data.json (remember to rename table first)



#set($deviceRef = "home/games-room/computer/" + $input.param('featureset'))
{
    "TableName": "test-stack-DeviceTable-MGKXW4KKJRMR",
    "KeyConditionExpression": "userId=:v_userId and deviceRef=:v_deviceRef",
    "ExpressionAttributeValues": {
        ":v_userId": {"S":"seanhodges"}, 
        ":v_deviceRef": {"S":"$deviceRef"}
    }
}