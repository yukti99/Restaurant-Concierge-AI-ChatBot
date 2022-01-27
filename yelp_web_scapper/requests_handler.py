import sys
from urllib.error import HTTPError
import requests
from configs import YELP_API_AUTHENTICATION_TOKEN, HOST_NAME, GET_CALL


def make_get_request_call(path, parameter_dictionary=None):
    try:
        req = requests.request(method=GET_CALL, url=HOST_NAME + path, headers={
            'Authorization': 'Bearer %s' % YELP_API_AUTHENTICATION_TOKEN,
        }, params=parameter_dictionary)

        return req.json()

    except HTTPError as error:
        sys.exit(
            'Encountered HTTP error {0} on {1}:\n {2}\nAbort program.'.format(
                error.code,
                error.url,
                error.read(),
            )
        )
