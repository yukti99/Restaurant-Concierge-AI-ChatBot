import json
import random
import boto3
import requests


def lambda_handler(event, context):
    # Polling from queue
    sqs_client = boto3.client('sqs')
    print("invoke lf4")

    queue_url = "https://sqs.us-west-2.amazonaws.com/201565561775/dining-chatbot-sqs"

    response = sqs_client.receive_message(
        QueueUrl=queue_url,
        AttributeNames=[
            'All'],
        MessageAttributeNames=[
            'Location', 'Cuisine', 'DiningTime', 'NumPeople', 'PhoneNo', 'DiningDate'
        ],
        MaxNumberOfMessages=5,
        VisibilityTimeout=1,
        WaitTimeSeconds=2
    )

    print(response)
    # checking if no message is returned to prevent Lambda errors
    if 'Messages' not in response:
        print("There are no messages in SQS!")

    else:
        print("Received {} messages".format(len(response['Messages'])))

        for message in response['Messages']:
            print("Processing message: {}".format(message))
            body = message['Body']
            print(body)

    # Getting required information from message
    if type(body) != dict:
        body = json.loads(body)

    cuisine = body['Cuisine']
    location = body['Location']
    no_of_people = body['NumPeople']
    dining_time = body['DiningTime']
    dinint_date = body['DiningDate']
    user_phone_number = body['PhoneNo']

    response = sqs_client.delete_message(QueueUrl=queue_url, ReceiptHandle=response['Messages'][0]['ReceiptHandle'])
    print("Message deleted successfully ")

    # Open Search
    open_search_host = 'https://search-restaurants1-t47dakpcn5uotstcp3ubiiywwi.us-west-2.es.amazonaws.com/'
    path = 'lambda-index'
    url = open_search_host + path + '/_search' + '?q=cuisine:{}'.format(cuisine)
    aws_auth = ('open-search-user', '<open-search-user-password>')
    headers = {"Content-Type": "application/json"}
    r = requests.get(url, auth=aws_auth, headers=headers)
    print("open_search_response:{}".format(r))
    total_results = len(r.json()['hits']['hits'])
    print("Total results:{}".format(total_results))

    if total_results < 5:
        no_of_suggestions = total_results
    else:
        no_of_suggestions = 5

    list_of_restaurant_ids = []
    for i in range(0, no_of_suggestions):
        list_of_restaurant_ids.append(r.json()['hits']['hits'][i]['_source']['restaurant_id'])

    print("List of restaurant ids:{}".format(list_of_restaurant_ids))

    # Dynamo DB
    db = boto3.resource('dynamodb')
    table = db.Table('yelp-restaurants')
    each_restaurant_info = {}
    random_restaurants = random.sample(list_of_restaurant_ids, no_of_suggestions)
    counter = 0
    for i in range(0, no_of_suggestions):
        response = table.get_item(Key={'restaurant_id': random_restaurants[i]})
        print("printing dynamo db response: {}".format(response))
        if 'Item' in response.keys():
            restaurant_info = response['Item']
            each_restaurant_info[counter] = {'restaurant_id': restaurant_info['restaurant_id'],
                                             'name': restaurant_info['name'],
                                             'rating': float(restaurant_info['rating']),
                                             'address': restaurant_info['address'],
                                             'review_count': float(restaurant_info['review_count']),
                                             'zip_code': restaurant_info['zip_code']}
            counter = counter + 1
        else:
            print("Item key not found.")

    # Message formation:
    opening_message = " Hello! Here are my {} restaurant suggestions for {} people, for the date {} at time {}: ".format(
        cuisine, no_of_people, dinint_date, dining_time)
    restaurant_message = ""
    for i in range(0, counter):
        restaurant_message = restaurant_message + "{}. {}, located at {}, ".format(i + 1,
                                                                                   each_restaurant_info[i]['name'],
                                                                                   each_restaurant_info[i]['address'])
    restaurant_message = restaurant_message[:-2]
    total_message = opening_message + restaurant_message.replace("None", "") + ". Enjoy your meal!"

    print("FINAL MESSAGE:{}".format(total_message))

    # Storing Previous Recommendations:
    table_name = "user-information"
    db_client = boto3.resource('dynamodb')
    user_table = db_client.Table(table_name)

    # push restaurant search info to dynamodb
    row_to_be_added = {'phone_no': user_phone_number, 'previous_message': restaurant_message, 'location': location,
                       'cuisine': cuisine}
    response = user_table.put_item(Item=row_to_be_added)
    print("Pushed user records to db with response:{}".format(response))

    # SNS Notification
    print("Sending Message to user's phone number:{}".format(user_phone_number))
    # session = boto3.client('sns', region_name="us-west-2")

    """
    total_message: 
    "Hello! Here are my mexican restaurant suggestions for 13 people, for today at 20:00: 
    1. The Maze, located at 32 W 32nd StFl 3. Enjoy your meal!"
    """
    sns_client = boto3.client('sns', region_name="us-west-2")
    sns_client_publish = sns_client.publish(TargetArn="arn:aws:sns:us-west-2:201565561775:restaurant",
                                      Message=json.dumps({'default': json.dumps(total_message)}),
                                      MessageStructure='json')
    sns_response = sns_client.publish(PhoneNumber=user_phone_number, Message=total_message, MessageAttributes={
        'AWS.SNS.SMS.SMSType': {
            'DataType': 'String',
            'StringValue': 'Transactional'
        }
    })
    print("sns_request response:{}".format(sns_response))