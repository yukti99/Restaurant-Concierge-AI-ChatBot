from configs import BUSINESS_SEARCH_PATH, DEFAULT_LOCATION, LIMIT, BUSINESS_PATH
from requests_handler import make_get_request_call
import json
import datetime
import string
from constants import SUPPORTED_CUISINES


def get_all_restaurants(cuisine, offset=0):
    print("Im here")
    query_params = {'term': cuisine, 'location': DEFAULT_LOCATION, 'limit': LIMIT, 'offset': offset}
    businesses = make_get_request_call(path=BUSINESS_SEARCH_PATH, parameter_dictionary=query_params)
    return businesses.get('businesses')


def get_restaurant_info(business_id):
    restaurant_info_path = BUSINESS_PATH + business_id
    restaurant_info = make_get_request_call(path=restaurant_info_path)
    return restaurant_info


def get_proper_name(restaurant_name):
    printable = set(string.printable)
    english_name = ''.join(filter(lambda x: x in printable, restaurant_name))
    return english_name


def get_all_restaurants_data(cuisine):
    offset = 0
    cuisine_info_dict = {}
    while len(cuisine_info_dict) <= 1000:
        print("Current offset is:{}".format(offset))
        restaurants = get_all_restaurants(cuisine=cuisine, offset=offset)
        if not restaurants:
            print('No {} restaurants found.'.format(cuisine))
            break
        for restaurant_info in restaurants:
            restaurant_information_dict = {}
            restaurant_information_dict['id'] = restaurant_info['id']
            restaurant_information_dict['name'] = get_proper_name(restaurant_info.get('name', None))
            restaurant_information_dict['rating'] = restaurant_info.get('rating', None)
            restaurant_information_dict['review_count'] = restaurant_info.get('review_count', None)
            restaurant_information_dict['address'] = str(restaurant_info['location'].get('address1', None)) + str(
                restaurant_info['location'].get('address2', None))
            restaurant_information_dict['zip_code'] = restaurant_info['location'].get('zip_code', None)
            restaurant_information_dict['is_close'] = restaurant_info.get('is_closed', True)
            restaurant_information_dict['co-ordinates'] = restaurant_info.get('coordinates', None)
            restaurant_information_dict['insertedAtTimestamp'] = datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S.%f")
            cuisine_info_dict[restaurant_info['id']] = restaurant_information_dict
        offset = offset + 50
    return cuisine_info_dict


def get_manhattan_restaurant_data():
    for cuisine in SUPPORTED_CUISINES:
        print("Running for cuisine: {}".format(cuisine))
        cuisine_wise_restaurant_info = get_all_restaurants_data(cuisine=cuisine)
        with open(cuisine+'_restaurant_data.json', 'w') as openfile:
            json.dump(cuisine_wise_restaurant_info, openfile)
    return


def push_to_dynamo_db():
    get_manhattan_restaurant_data()


def main():
    get_manhattan_restaurant_data()


if __name__ == "__main__":
    main()






















