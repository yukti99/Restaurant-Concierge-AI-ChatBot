# Reference: https://docs.aws.amazon.com/opensearch-service/latest/developerguide/integrations.html#integrations-dynamodb

import boto3
import requests
from requests_aws4auth import AWS4Auth

region = 'us-west-2'
service = 'es'
credentials = boto3.Session().get_credentials()
awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)
#host = 'https://search-restaurants1-t47dakpcn5uotstcp3ubiiywwi.us-west-2.es.amazonaws.com'
host = 'https://search-restaurant-v2-a4qf6vmhyxf3yfil77qj65dgt4.us-west-2.es.amazonaws.com'
index = 'lambda-index'
type = '_doc'
url = host + '/' + index + '/' + type + '/'
headers = { "Content-Type": "application/json" }


def lambda_handler(event, context):
    count = 0
    for record in event['Records']:
        id = record['dynamodb']['Keys']['restaurant_id']['S']
        open_search_url = url + id
        if record['eventName'] == 'REMOVE':
            r = requests.delete(url + id, auth=awsauth)
        else:
            document = record['dynamodb']['NewImage']
            data = {'restaurant_id': document['restaurant_id']['S'], 'cuisine':document['cuisine']['S']}
            r = requests.put(url=open_search_url, auth=awsauth, json=data, headers=headers)
        count += 1
    return str(count) + ' records processed.'

