import boto3
from configs import ACCESS_KEY, ACCESS_ID
from constants import SUPPORTED_CUISINES, DYNAMO_DB_TABLE_NAME
import json


def get_dynamo_db_client():
    db = boto3.resource('dynamodb', region_name='us-west-2', aws_access_key_id=ACCESS_ID,
                        aws_secret_access_key=ACCESS_KEY)
    return db


def load_data_for_a_given_cuisine(cuisine):
    file_content = open(cuisine+'_restaurant_data.json')
    cuisine_data = json.load(file_content)
    cuisine_dict = {}
    for restaurant, restaurant_info in cuisine_data.items():
        individual_restaurant_info = {'restaurant_id': restaurant, 'cuisine': cuisine, 'name': restaurant_info['name'],
                                      'rating': int(restaurant_info['rating']), 'review_count': restaurant_info['review_count'],
                                      'address': restaurant_info['address'], 'zip_code': restaurant_info['zip_code'],
                                      'is_close': str(restaurant_info['is_close']),
                                      'co-ordinates': json.dumps(restaurant_info['co-ordinates']),
                                      'insertedAtTimestamp': restaurant_info['insertedAtTimestamp']}
        cuisine_dict[restaurant] = json.dumps(individual_restaurant_info)
    return cuisine_dict


def load_data_into_dynamo_db(row, db):
    table = db.Table(DYNAMO_DB_TABLE_NAME)
    print("Loading into Dynamodb:{}".format(row))
    for each_entry in row:
        try:
            response = table.put_item(Item=each_entry)
        except Exception as e:
            print('Failed to load the entry:{}. Error is:{}'.format(each_entry, e))


def main():
    dynamo_db_client = get_dynamo_db_client()
    for cuisine in SUPPORTED_CUISINES:
        print("Loading data for cuisine:{}".format(cuisine))
        cuisine_dict = load_data_for_a_given_cuisine(cuisine=cuisine)
        print("Length of {}cuisine_dict: {}".format(cuisine, len(cuisine_dict)))
        restaurant_info_row = []
        for value in cuisine_dict.values():
            restaurant_info_row.append(eval(value))
        load_data_into_dynamo_db(restaurant_info_row, db=dynamo_db_client)


if __name__ == '__main__':
    main()
