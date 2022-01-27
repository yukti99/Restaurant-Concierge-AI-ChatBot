import logging
import boto3


def lambda_handler(event, context):
    logging.basicConfig(level=logging.DEBUG,format='%(levelname)s: %(asctime)s: %(message)s')
    print("Received event: {}".format(event))
   
    # Boto Client to communicate with Lex Bot
    client = boto3.client('lexv2-runtime')
   
    # If there is no response received, or except block is executed, this custom message will tell the user 
    # that lex bot could not understand what they said, so they should repeat.
    bot_response = "Sorry! I couldn't quite understand. Can you repeat?"
   
    try:
        # text entered by user to interact with the bot
        user_input = event['messages'][0]['unstructured']['text']
        
        # printing the user input to observe on cloud watch
        print("User input:{}".format(user_input))
       
       # sending the user input to our lex bot
       # info about our lex bot obtained from Lex intent testing console to recognise the text we obtain from the bot
        response = client.recognize_text(
            botAliasId="TSTALIASID",
            botId="WCRUAVKAU9",
            localeId= "en_US",
            text = user_input,
            sessionId= "201565561775646"
        )
       
        print("Lex Response:{}".format(response))
        # storing the lex bot response by extracting the content of message received from response json
        bot_response = response['messages'][0]['content']
       
    except Exception as e:
        print("Error: {} occured for event- {}".format(e, event))

    # returning the status code and lex bot message 
    return {
        'statusCode': 200,
        'messages': [{"type": "unstructured", "unstructured": {"text":bot_response}}]
    }
       