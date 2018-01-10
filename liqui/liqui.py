from urllib.parse import urlencode
from collections import OrderedDict
import json
import time
import hashlib
import hmac
import requests
import decimal

# logger
import logging
logger = logging.getLogger("TradingBot")

BASE_URL_PUBLIC = 'https://api.liqui.io/api/3/'
BASE_URL_PRIVATE = 'https://api.liqui.io/tapi'


class Liqui(object):
    """
    Used for requesting Liqui with API key and API secret
    """
    def __init__(self, api_key, api_secret, json_nums=decimal.Decimal, timeout=10):
        # Keys
        self.api_key = str(api_key) if api_key is not None else ''
        self.api_secret = str(api_secret) if api_secret is not None else ''
        # Logger
        self.logger = logger
        # json number datatypes
        self.jsonNums = json_nums
        # Set time-out
        self.timeout = timeout
        # Set time labels
        self.MINUTE, self.HOUR, self.DAY, self.WEEK, self.MONTH, self.YEAR = \
            60, 60 * 60, 60 * 60 * 24, 60 * 60 * 24 * \
            7, 60 * 60 * 24 * 30, 60 * 60 * 24 * 365

    @property
    def nonce(self):
        self._nonce = int(time.time())
        return str(self._nonce)

    def __public__(self, method, command, args=[]):

        data = args
        # get
        if method == 'Get':
            request_url = BASE_URL_PUBLIC + command + "/" + data
            logger.debug("Liqui - Request Get: %s", request_url)
            response = requests.get(
                request_url,
                timeout=self.timeout)

            if response is None:
                logger.error("Liqui - Request not succesful" )
                raise Exception("Liqui - Request not succesful")

            if response.status_code != 200:
                logger.error("Liqui - Response error: HTTP " + str(response.status_code) + " returned with the content " + str(response.text) + ".")
                raise Exception("Liqui - Response error: HTTP " + str(response.status_code) + " returned.")

            # decode json
            if not self.jsonNums:
                response_json = json.loads(response.text, parse_float=str)
            else:
                response_json = json.loads(
                    response.text,
                    parse_float=self.jsonNums,
                    parse_int=self.jsonNums)

            if 'success' in response_json and response_json['success'] != 1:
                logger.error("Liqui - Response contains a functional error: " + str(response_json))
                raise Exception("Liqui - Response contains a functional error: " + str(response_json))

        else:
            raise Exception("Liqui - Invalid method: " + method)

        logger.debug("Liqui - Response content: " + str(response_json))

        return response_json;

    def __private__(self, method, command, args={}):

        if not self.api_key or not self.api_secret:
            raise Exception("A Key and Secret needed!")

        args['method'] = command
        args['nonce'] = self.nonce
        data = urlencode(args)
        signature = hmac.new(self.api_secret.encode(), msg=data.encode(), digestmod=hashlib.sha512).hexdigest()

        headers = {
            'Key': self.api_key,
            'Sign': signature,
        }

        successful = False
        if method == 'Post':
            request_url = BASE_URL_PRIVATE
            logger.debug("Liqui - Request Post: %s with %s", request_url + command, data)
            response = requests.post(
                request_url,
                data=data,
                headers=headers,
                timeout=self.timeout)
            successful = True
        # get
        elif method == 'Get':
            request_url = BASE_URL_PUBLIC
            logger.debug("Liqui - Request Get: %s", request_url + command + urlencode(args))
            response = requests.get(
                request_url,
                headers=headers,
                timeout=self.timeout)
            successful = True
        else:
            raise Exception("Liqui - Invalid method: " + method)

        if successful is False or response is None:
            logger.error("Liqui - Request not succesful" )
            raise Exception("Liqui - Request not succesful")

        if response.status_code != 200:
            logger.error("Liqui - Response error: HTTP " + str(response.status_code) + " returned with the content " + str(response.text) + ".")
            raise Exception("Liqui - Response error: HTTP " + str(response.status_code) + " returned.")

        # decode json
        if not self.jsonNums:
            response_json = json.loads(response.text, parse_float=str)
        else:
            response_json = json.loads(
                response.text,
                parse_float=self.jsonNums,
                parse_int=self.jsonNums)

        logger.debug("Liqui - Response content: " + str(response_json))

        if response_json['success'] != 1:
            logger.error("Liqui - Response contains a functional error: " + str(response_json))
            raise Exception("Liqui - Response contains a functional error: " + str(response_json))

        return response_json;

    def get_orderbook(self, market):
        logger.debug("Liqui - Get orderbook for " + str(market))
        return self.__public__("Get", "depth", market)

    def place_limit_order(self, market, way, quantity, price):
        if way == 'Ask':
            self.sell_limit(market, quantity, price)
        elif way == 'Bid':
            self.buy_limit(market, quantity, price)
        else:
            logger.error("Liqui - Unknown order way " + str(way))
            raise Exception("Liqui - Unknown order way " + str(way))

    def buy_limit(self, market, quantity, rate):
        order = {
            'pair' : market,
            'type' : 'buy',
            'rate' : rate,
            'amount': quantity
        }
        logger.debug("Liqui - Placed a limit Buy order on " + str(market) + " with quantity: " + str(quantity) + " and price " + str(rate))
        return self.__private__("Post", 'trade', order)

    def sell_limit(self, market, quantity, rate):
        order = {
            'pair' : market,
            'type' : 'sell',
            'rate' : rate,
            'amount': quantity
        }
        logger.debug("Liqui - Placed a limit Sell order on " + str(market) + " with quantity: " + str(quantity) + " and price " + str(rate))
        return self.__private__("Post", 'trade', order)

    def get_info(self):
        return self.__private__("Post", 'getInfo')

    def get_balances(self):
        funds = self.get_info()['return']['funds']
        return {currency: balance for currency, balance in funds.items() if balance != 0}

    def get_clean_balance(self):
        balances = {}
        raw_balance = self.get_balances()
        balances = self.clean_balances(raw_balance)
        return balances

    def clean_balances(self, raw_balances):
        balances = {}
        for balance_currency in raw_balances:
            currency = balance_currency.upper()
            balances[currency] = {}
            balances[currency]['Balance'] = 0
            balances[currency]['AvailableBalance'] = raw_balances[balance_currency]
            balances[currency]['OpenOrder'] = 0
            balances[currency]['Pending'] = 0
        return balances

    def clean_orderbook(self, market):
        # Output a cleaned dictionnary:
        # {'buy': {Price: Amount, Price: Amount, ...},
        # 'sell' {Price: Amount, Price: Amount, ...}}

        raw_orderbook = self.get_orderbook(market)
        raw_orderbook = raw_orderbook[market]

        orderbook_unordered = {'buy': {}, 'sell': {}}
        orderbook_cleaned = {'buy': {}, 'sell': {}}

        for buy in raw_orderbook['bids']:
            quantity = buy[1]
            price = buy[0]
            orderbook_unordered['buy'][price] = quantity
        orderbook_cleaned['buy'] = OrderedDict(sorted(orderbook_unordered['buy'].items(), key=lambda t: t[0], reverse=True))

        for sell in raw_orderbook['asks']:
            quantity = sell[1]
            price = sell[0]
            orderbook_unordered['sell'][price] = quantity
        orderbook_cleaned['sell'] = OrderedDict(sorted(orderbook_unordered['sell'].items(), key=lambda t: t[0]))

        return orderbook_cleaned
