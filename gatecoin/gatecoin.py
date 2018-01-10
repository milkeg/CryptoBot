from urllib.parse import urlencode as _urlencode
from collections import OrderedDict
import json
import time
import base64
import hashlib
import hmac
import requests
import decimal
# logger
import logging
logger = logging.getLogger("TradingBot")

sleep_time_in_second = 5


class Gatecoin(object):

    def __init__(self, url, key, secret, timeout=10, json_nums=decimal.Decimal):

        # URL
        self.url = url
        # Nonce
        self._nonce = 0
        # Logger
        self.logger = logger
        # json number datatypes
        self.jsonNums = json_nums
        # Grab keys, set timeout, ditch coach?
        self.key, self.secret, self.timeout = \
            key, secret, timeout
        # Set time labels
        self.MINUTE, self.HOUR, self.DAY, self.WEEK, self.MONTH, self.YEAR = \
            60, 60 * 60, 60 * 60 * 24, 60 * 60 * 24 * \
            7, 60 * 60 * 24 * 30, 60 * 60 * 24 * 365

    @property
    def nonce(self):
        self._nonce = time.time()
        return str(self._nonce)

    def __call__(self, method, command, args={}):
        if not self.key or not self.secret:
            raise Exception("A Key and Secret needed!")

        # Signature generation
        method_name = method
        if method == 'Get':
            content_type = ''
        else:
            content_type = 'application/json'

        now = self.nonce

        message_to_encrypt = method_name + self.url + command + content_type + now
        message_to_encrypt = message_to_encrypt.lower()
        signature = hmac.new(self.secret.encode(), msg=message_to_encrypt.encode(), digestmod=hashlib.sha256).digest()
        signature_base64 = base64.b64encode(signature, altchars=None)

        headers = {
            'API_PUBLIC_KEY': self.key,
            'API_REQUEST_SIGNATURE': signature_base64,
            'API_REQUEST_DATE': now,
            'Content-Type': content_type
        }

        successful = False
        if method == 'Post':
            data = json.dumps(args)
            logger.debug("Gatecoin - Request Post: %s with %s", self.url + command, data)
            response = requests.post(
                self.url + command,
                data=data,
                headers=headers,
                timeout=self.timeout)
            successful = True
        # put
        elif method == 'Put':
            data = json.dumps(args)
            logger.debug("Gatecoin - Request Put: %s with %s", self.url + command, data)
            response = requests.put(
                self.url + command,
                data=data,
                headers=headers,
                timeout=self.timeout)
            successful = True
        # get
        elif method == 'Get':
            logger.debug("Gatecoin - Request Get: %s", self.url + command + _urlencode(args))
            response = requests.get(
                self.url + command + _urlencode(args),
                headers=headers,
                timeout=self.timeout)
            successful = True
        # Delete
        elif method == 'Delete':
            logger.debug("Gatecoin - Request Delete: %s", self.url + _urlencode(args))
            response = requests.delete(
                self.url + command + _urlencode(args),
                headers=headers,
                timeout=self.timeout)
            successful = True
        else:
            raise Exception("Gatecoin - Invalid Command!: " + command)

        if successful is False or response is None:
            logger.error("Gatecoin - Request not succesful" )
            raise Exception("Gatecoin - Request not succesful")

        if response.status_code != 200:
            logger.error("Gatecoin - Response error: HTTP " + str(response.status_code) + " returned with the content " + str(response.text) + ".")
            raise Exception("Gatecoin - Response error: HTTP " + str(response.status_code) + " returned with the content " + str(response.text) + ".")

        # decode json
        if not self.jsonNums:
            response_json = json.loads(response.text, parse_float=str)
        else:
            response_json = json.loads(
                response.text,
                parse_float=self.jsonNums,
                parse_int=self.jsonNums)


        if response_json['responseStatus']['message'] != 'OK':
            logger.error("Gatecoin - Response contains a functional error: " + str(response_json))
            raise Exception("Gatecoin - Response contains a functional error: " + str(response_json))

        # check if gatecoin returned an error
        # Commented as it should be case specific error handling
        #if 'error' in response_json:
        #    raise Exception(response_json['error'])

        return response_json

    # --BALANCE SECTION-------------------------------------------------------
    def get_balances(self):
        """
        Get the available balance for each currency for the logged in account
        """
        self.current_rate['Balance'].append(time.time())
        return self.__call__('Get', '/Balance/Balances')

    def get_balance(self, currency):
        """
        Get the available balance for s currency for the logged in account
        """
        self.current_rate['Balance'].append(time.time())
        return self.__call__('Get', '/Balance/Balances/' + str(currency))

    def get_balance_deposits(self):
        """
        Get all account deposits, including wire, okpay and digital currency, of the logged in user
        """
        self.current_rate['Balance'].append(time.time())
        return self.__call__('Get', '/Balance/Deposits')

    def get_balance_withdrawals(self):
        """
        Get all account deposits, including wire, okpay and digital currency, of the logged in user
        """
        self.current_rate['Balance'].append(time.time())
        return self.__call__('Get', '/Balance/Withdrawals')

    # --TRADE SECTION-------------------------------------------------------
    def get_open_orders(self):
        """
        Get open orders for the logged in trader
        """
        self.current_rate['Trade'].append(time.time())
        logger.debug("Gatecoin - Get all open orders")
        return self.__call__('Get', '/Trade/Orders')

    def place_limit_order(self, code, way, amount, price):
        """
        Get open orders for the logged in trader
        """
        self.current_rate['Trade'].append(time.time())
        logger.debug("Gatecoin - Placed a limit " + str(way) + " order on " + str(code) + " with quantity: " + str(amount) + " and price " + str(price))
        return self.__call__('Post', '/Trade/Orders', {
            'Code': str(code),
            'Way': str(way),
            'Amount': str(amount),
            'Price': str(price),
        })

    def delete_orders(self):
        """
        Cancel all existing orders
        """
        self.current_rate['Trade'].append(time.time())
        logger.debug("Gatecoin - Deleted all open orders")
        return self.__call__('Delete', '/Trade/Orders')

    def delete_order(self, order_id):
        """
        Cancel an existing order
        """
        self.current_rate['Trade'].append(time.time())
        logger.debug("Gatecoin - Deleted order " + str(order_id))
        return self.__call__('Delete', '/Trade/Orders/' + str(order_id))

    def get_order(self, order_id):
        """
        Get an existing order
        """
        self.current_rate['Trade'].append(time.time())
        logger.debug("Gatecoin - Get order " + str(order_id))
        return self.__call__('Get', '/Trade/Orders/' + str(order_id))

    def get_trades(self, count=0):
        """
        Get all transactions of logged in user
        """
        self.current_rate['Trade'].append(time.time())
        return self.__call__('Get', '/Trade/Trades?Count=' + str(count))

    def get_usertrades(self, after):
        """
        Get all transactions of logged in user
        """
        self.current_rate['Trade'].append(time.time())
        return self.__call__('Get', '/Trade/UserTrades/' + str(after))

    # --PUBLIC SECTION-------------------------------------------------------
    def get_orderbook(self, currency_pair):
        """
        Get prices and market depth for the currency pair
        """
        return self.__call__('Get', '/Public/MarketDepth/' + str(currency_pair))

    def get_transactions(self, currency_pair):
        """
        Get recent transactions
        """
        return self.__call__('Get', '/Public/Transactions/' + str(currency_pair))

    def get_transactions_history(self, currency_pair):
        """
        Gets recent transactions
        """
        return self.__call__('Get', '/Public/TransactionsHistory/' + str(currency_pair))

    def get_liveticker(self):
        """
        Get live ticker for all currency
        """
        return self.__call__('Get', '/Public/LiveTicker')

    def get_ticker(self, currency_pair):
        """
        Get live ticker by currency
        """
        return self.__call__('Get', '/Public/LiveTicker/' + str(currency_pair))

    def get_ticker_history(self, currency, timeframe):
        """
        Get live ticker by currency
        """
        if timeframe not in ['1m', '15m', '1h', '6h', '24h']:
            raise Exception('Incorrect parameters: timeframe in get_public_ticker_history')

        return self.__call__('Get', '/Public/TickerHistory/' + str(currency) + '/' + str(timeframe))

    def get_clean_balance(self):
        balances = {}
        raw_balance = self.get_balances()
        balances = self.clean_balances(raw_balance)
        return balances

    def clean_balances(self, raw_balances):
        balances = {}
        for balance_currency in raw_balances['balances']:
            balances[balance_currency['currency']] = {}
            balances[balance_currency['currency']]['Balance'] = balance_currency['balance']
            balances[balance_currency['currency']]['AvailableBalance'] = balance_currency['availableBalance']
            balances[balance_currency['currency']]['OpenOrder'] = balance_currency['openOrder']
            balances[balance_currency['currency']]['Pending'] = balance_currency['pendingIncoming'] - balance_currency['pendingOutgoing']
        return balances

    def clean_orderbook(self, currency_pair):
        # Output a cleaned dictionnary:
        # {'buy': {Price: Amount, Price: Amount, ...},
        # 'sell' {Price: Amount, Price: Amount, ...}}

        raw_orderbook = self.get_orderbook(currency_pair)

        orderbook_unordered = {'buy': {}, 'sell': {}}
        orderbook_cleaned = {'buy': {}, 'sell': {}}

        for buy in raw_orderbook['bids']:
            quantity = buy['volume']
            price = buy['price']
            orderbook_unordered['buy'][price] = quantity
        orderbook_cleaned['buy'] = OrderedDict(sorted(orderbook_unordered['buy'].items(), key=lambda t: t[0], reverse=True))

        for sell in raw_orderbook['asks']:
            quantity = sell['volume']
            price = sell['price']
            orderbook_unordered['sell'][price] = quantity
        orderbook_cleaned['sell'] = OrderedDict(sorted(orderbook_unordered['sell'].items(), key=lambda t: t[0]))

        return orderbook_cleaned
