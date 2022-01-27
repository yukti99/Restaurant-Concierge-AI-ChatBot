import json
import logging
from datetime import *
import boto3

Cuisine_list = ['american', 'thai', 'greek', 'chinese', 'japanese', 'indonesian', 'cuban', 'french']
places = ['manhattan', 'midtown', 'uptown', 'downtown', 'times square']
NUMS = {'one': '1', 'two': '2', 'three': '3', 'four': '4', 'five': '5', 'six': '6', 'seven': '7', 'eight': '8',
        'nine': '9', 'ten': '10', 'eleven': '11', 'twelve': '12', 'thirteen': '13', 'fourteen': '14', 'fifteen': '15',
        'sixteen': '16', 'seventeen': '17', 'eighteen': '18', 'nineteen': '19', 'twenty': '20'}


def lambda_handler(event, context):
    # Setting up the logging configuration
    logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(asctime)s: %(message)s')

    # printing the received event
    print("Received event: {}".format(event))

    # Checking if the event received corresponds to Greeting Intent, then the Greeting function to get executed
    if event["sessionState"]["intent"]["name"] == "GreetingIntent":
        return GreetingIntent(event)

    # if event is suggesting that user wants food/ is hungry /... then Dining suggestion intent mehtod should be called
    if event["sessionState"]["intent"]["name"] == "DiningSuggestionsIntent":
        print("WE WENT TO DINING")
        return DiningSuggestionsIntent(event)

    # if the event is unidentified, then error intent is given to the user
    return {
        "sessionState": {
            "dialogAction": {
                "type": "ElicitIntent",
            },
            "intent": {
                "confirmationState": "Confirmed",
                "name": "GreetingIntent"
            }
        },
        "message": [
            {
                "contentType": "PlainText",
                "content": "Error!"
            }
        ]
    }


'''
Function to push messages obtained from lex bot to the SQS, so that later it can be 
used for elastic search and dynamo db and sending message notifications to user

'''


def push_msg_to_sqs(sqs_name, restaurant_info):
    '''
    Code to create a sqs boto3 client that will interact with SQS to push messages into it

    '''
    # creating the Amazon Simple Queue Service (SQS) client (from aws sqs documentation)
    client = boto3.client('sqs')

    # returns the URL of an existing Amazon SQS queue.
    url = client.get_queue_url(
        QueueName=sqs_name,
    )['QueueUrl']
    logging.info(url)

    # sending the restaurant-info message to SQS
    try:
        send_response = client.send_message(
            QueueUrl=url,
            MessageBody=json.dumps(restaurant_info)
        )
        print("Response after sending message to SQS: {}".format(send_response))

    # In case an error occurs while sending msg to queue, it will be logged
    except ClientError as e:
        print("Error: {} occured".format(e))
        return None

    print("Confirmed Response after sending message to SQS: {}".format(send_response))
    # returning the response back to lambda-handler
    return send_response


def GreetingIntent(event):
    return {
        "sessionState": {
            "dialogAction": {
                "type": "ElicitIntent"
            }
        },
        "messages": [{
            "contentType": "PlainText",
            "content": "Namaste! I am Josh, What can I do for you today?"
        }]

    }


def DiningSuggestionsIntent(event):
    print(event)

    ''' 
    -----------------------------------------------------------------------------------------------------
    DECLARING A DICTIONARY TO STORE THE INFO WE NEED FROM THE USER TO SEARCH FOR RESTAURANTS
    -----------------------------------------------------------------------------------------------------
    '''
    # an object to store the restaurant search info that will be obtained from user conversation with the bot
    restaurant_info = dict.fromkeys(["Location", "Cuisine", "DiningDate", "DiningTime", "NumPeople", "PhoneNo"])

    # A template to set the intent that must be invoked by user-inputs
    intent_to_return = {
        "sessionState": {
            "dialogAction": {
                "type": "ElicitSlot",
                "slotToElicit": "randomslot"
            },
            "intent": {
                "confirmationState": "Confirmed",
                "name": "DiningSuggestionsIntent",
                "state": "InProgress",
                "slots": event["sessionState"]["intent"]["slots"]
            }
        },
        "messages": [
            {
                "contentType": "PlainText",
                "content": "randommsg"
            }
        ]
    }

    ''' 
    -----------------------------------------------------------------------------------------------------
    CODE TO INVOKE INTENTS TO COLLECT RESTAURANT SEARCH INFO FROM USER
    -----------------------------------------------------------------------------------------------------
    '''

    '''
    -------------------------------------------------LOCATION--------------------------------------------
    '''
    print("EVENT = ", event["sessionState"]["intent"]["slots"]["Location"])
    # If location is given by user, we can populate our restaurant_info dictionary with it
    if event["sessionState"]["intent"]["slots"]["Location"]:
        print("INSIDE LOCATION")
        print(event["sessionState"]["intent"]["slots"]["Location"])
        print(event["sessionState"]["intent"]["slots"]["Location"]['value']['interpretedValue'])

        if (event["sessionState"]["intent"]["slots"]["Location"]["value"]["originalValue"]).lower() not in places:
            print(event["sessionState"]["intent"]["slots"]["Location"]["value"]["originalValue"], " is not correct!")
            intent_to_return["sessionState"]["dialogAction"]["slotToElicit"] = "Location"
            intent_to_return["messages"][0]["content"] = "Sorry, I am only aware of the Manhattan area..Pls try again!"
            return intent_to_return
        else:
            print("SETTING LOCATION!!!!!!!!!!!!!!!!!!!111111")
            restaurant_info["Location"] = event["sessionState"]["intent"]["slots"]["Location"]["value"][
                "interpretedValue"]
    else:
        intent_to_return["sessionState"]["dialogAction"]["slotToElicit"] = "Location"
        intent_to_return["messages"][0]["content"] = "Oh I would love to help! Which place do you want to go to eat?"
        print(intent_to_return)
        return intent_to_return

    '''
    -------------------------------------------------CUISINE--------------------------------------------
    '''

    if event["sessionState"]["intent"]["slots"]["Cuisine"]:
        print(event["sessionState"]["intent"]["slots"]["Cuisine"]["value"]["originalValue"])
        if (event["sessionState"]["intent"]["slots"]["Cuisine"]["value"]["originalValue"]).lower() not in Cuisine_list:
            intent_to_return["sessionState"]["dialogAction"]["slotToElicit"] = "Cuisine"
            msg = "Sorry! We don't support that cuisine..Maybe try something else? Cuisines supported : "
            for i in Cuisine_list:
                msg += i.title() + ", "
            intent_to_return["messages"][0]["content"] = msg + "etc."
            return intent_to_return
        restaurant_info["Cuisine"] = event["sessionState"]["intent"]["slots"]["Cuisine"]["value"]["interpretedValue"]
    else:
        intent_to_return["sessionState"]["dialogAction"]["slotToElicit"] = "Cuisine"
        intent_to_return["messages"][0]["content"] = "Cool! What kind of cuisine are you craving for?"
        return intent_to_return

    '''
    -------------------------------------------------DATE--------------------------------------------
    '''
    if event["sessionState"]["intent"]["slots"]["DiningDate"]:
        print("dining date = ", event["sessionState"]["intent"]["slots"]["DiningDate"])
        date_input = event["sessionState"]["intent"]["slots"]["DiningDate"]["value"]

        if "interpretedValue" not in date_input:
            intent_to_return["sessionState"]["dialogAction"]["slotToElicit"] = "DiningDate"
            intent_to_return["messages"][0]["content"] = "Oops! That seems like an invalid date. Pls try again!"
            return intent_to_return

        date_input = datetime.strptime(date_input["interpretedValue"], '%Y-%m-%d').date()
        print("LOOK HERE", date_input, date.today())
        if (date_input < date.today()):
            intent_to_return["sessionState"]["dialogAction"]["slotToElicit"] = "DiningDate"
            intent_to_return["messages"][0]["content"] = "Pls enter a future date!"
            return intent_to_return

        restaurant_info["DiningDate"] = event["sessionState"]["intent"]["slots"]["DiningDate"]["value"][
            "interpretedValue"]
    else:
        intent_to_return["sessionState"]["dialogAction"]["slotToElicit"] = "DiningDate"
        intent_to_return["messages"][0]["content"] = "Yum! Great choice. At what date do you want to eat?"
        return intent_to_return

    '''
    -------------------------------------------------TIME--------------------------------------------
    '''
    if event["sessionState"]["intent"]["slots"]["DiningTime"]:
        print("dining time = ", event["sessionState"]["intent"]["slots"]["DiningTime"])
        time_input = event["sessionState"]["intent"]["slots"]["DiningTime"]["value"]
        print("time input = ", time_input)
        if "interpretedValue" not in time_input:
            intent_to_return["sessionState"]["dialogAction"]["slotToElicit"] = "DiningTime"
            intent_to_return["messages"][0]["content"] = "Oops! That seems like an invalid time. Pls try again!"
            return intent_to_return

        time_input = datetime.strptime(time_input["interpretedValue"], "%H:%M")
        time_input = time_input + timedelta(hours=2)
        time_input = time_input.time()

        print("after processing, time input = ", time_input)
        print(time_input, datetime.now().time())
        if (date_input == date.today() and time_input < datetime.now().time()):
            print("wrong time reached!")
            intent_to_return["sessionState"]["dialogAction"]["slotToElicit"] = "DiningTime"
            intent_to_return["messages"][0]["content"] = "Oops! Pls enter a time at least 2 hours in the future!"
            return intent_to_return

        restaurant_info["DiningTime"] = event["sessionState"]["intent"]["slots"]["DiningTime"]["value"][
            "interpretedValue"]
    else:
        intent_to_return["sessionState"]["dialogAction"]["slotToElicit"] = "DiningTime"
        intent_to_return["messages"][0]["content"] = "Let's Go! Time?"
        return intent_to_return

    '''
    -------------------------------------------------NUMBER OF PEOPLE--------------------------------------------
    '''
    if event["sessionState"]["intent"]["slots"]["NumPeople"]:
        x = event["sessionState"]["intent"]["slots"]["NumPeople"]["value"]["interpretedValue"]
        if (int(x) < 0):
            if (str(x).lower() in list(NUMS.keys())):
                restaurant_info["NumPeople"] = NUMS[str(x)]
            else:
                intent_to_return["sessionState"]["dialogAction"]["slotToElicit"] = "NumPeople"
                intent_to_return["messages"][0]["content"] = "Sorry! No of people is invalid. Please enter again.."
                return intent_to_return
        else:
            restaurant_info["NumPeople"] = event["sessionState"]["intent"]["slots"]["NumPeople"]["value"][
                "interpretedValue"]
    else:
        intent_to_return["sessionState"]["dialogAction"]["slotToElicit"] = "NumPeople"
        intent_to_return["messages"][0]["content"] = "Great! How many people are going to accompany you?"
        return intent_to_return

    '''
    -------------------------------------------------PHONE NUMBER--------------------------------------------
    '''
    if event["sessionState"]["intent"]["slots"]["PhoneNo"]:
        phonenum = event["sessionState"]["intent"]["slots"]["PhoneNo"]["value"]["originalValue"]
        if (len(phonenum) != 10) or (not phonenum.isnumeric()):
            intent_to_return["sessionState"]["dialogAction"]["slotToElicit"] = "PhoneNo"
            intent_to_return["messages"][0][
                "content"] = "Oops! That seems like a wrong phone number. Can you pls enter again?"
            return intent_to_return
        else:
            restaurant_info["PhoneNo"] = event["sessionState"]["intent"]["slots"]["PhoneNo"]["value"][
                "interpretedValue"]

    else:
        intent_to_return["sessionState"]["dialogAction"]["slotToElicit"] = "PhoneNo"
        intent_to_return["messages"][0]["content"] = "May I please have your phone number for sending my suggestions?"
        return intent_to_return

    ''' 
    -----------------------------------------------------------------------------------------------------
    CODE TO SEND RESTAURANT SEARCH INFO TO SQS 
     -----------------------------------------------------------------------------------------------------
    '''
    print("Restaurant Info collected by bot-user conversation: {}".format(restaurant_info))

    # SQS name
    sqs_queue_name = "dining-chatbot-sqs"

    # calling the function to send this information to sqs
    send_response = push_msg_to_sqs(sqs_queue_name, restaurant_info)

    # Testing if response was sent successfully or not
    if send_response:
        print("The restaurant search info has been sent to SQS!")
    else:
        print("Some problem occurred while pushing the message to SQS...")

    ''' 
    -----------------------------------------------------------------------------------------------------
    CODE TO SEND USER HISTORY TO DYNAMO DB
     -----------------------------------------------------------------------------------------------------
    '''

    # user history
    user_phone_no = restaurant_info['PhoneNo']
    table_name = "user-information"

    db_client = boto3.resource('dynamodb')
    user_table = db_client.Table(table_name)
    key = {'phone_no': user_phone_no}
    user_table_response = user_table.get_item(Key=key)
    if 'Item' in user_table_response.keys():
        received_row = user_table_response['Item']
        previous_cuisine = received_row['cuisine']
        previous_location = received_row['location']
        previous_message = received_row['previous_message']
        previous_message = "These are few suggestions based on your previous search for cuisine: {}  and location : {}: ".format(
            previous_cuisine, previous_location) + "\n" + previous_message
        return {
            "sessionState": {
                "dialogAction": {
                    "type": "ElicitIntent"
                }
            },
            "intent": {
                "confirmationState": "Confirmed",
                "name": "ThankYouIntent",
                "state": "Fulfilled"
            },
            "messages": [
                {
                    "contentType": "PlainText",
                    "content": previous_message + " . The new suggestions will be sent to you by message soon! Good bye!"
                }
            ]
        }

    ''' 
    -----------------------------------------------------------------------------------------------------
    CODE TO INVOKE CLOSING INTENT AFTER REQUIRED INFO HAS BEEN COLLECTED AND SENT TO SQS
     -----------------------------------------------------------------------------------------------------
    '''
    return {
        "sessionState": {
            "dialogAction": {
                "type": "ElicitIntent"
            }
        },
        "intent": {
            "confirmationState": "Confirmed",
            "name": "ThankYouIntent",
            "state": "Fulfilled"
        },
        "messages": [
            {
                "contentType": "PlainText",
                "content": "Yay! You’re all set. You will get my suggestions soon! Have a great day !"
            }
        ]
    }
