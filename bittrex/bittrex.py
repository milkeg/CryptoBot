"""
Original author: https://github.com/mondeja/bittrex_v2
Copyright (c) 2017 Álvaro Mondéjar Rubio mondejar1994@gmail.com. All rights
reserved.

Redistribution and use in source and binary forms are permitted provided that
the above copyright notice and this paragraph are duplicated in all such forms
and that any documentation, advertising materials, and other materials related
to such distribution and use acknowledge that the software was developed by
Álvaro Mondéjar Rubio. The name of the Álvaro Mondéjar Rubio may not be used to
endorse or promote products derived from this software without specific prior
written permission.

THIS SOFTWARE IS PROVIDED “AS IS” AND WITHOUT ANY EXPRESS OR IMPLIED WARRANTIES,
INCLUDING, WITHOUT LIMITATION, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
FITNESS FOR A PARTICULAR PURPOSE.

See https://bittrex.com/Home/Api for more details
"""
import time
import hmac
import hashlib
from collections import OrderedDict
try:
    from urllib import urlencode
except ImportError:
    from urllib.parse import urlencode
import requests
import decimal
import json
# logger
import logging
logger = logging.getLogger("TradingBot")

BUY_ORDERBOOK = 'buy'
SELL_ORDERBOOK = 'sell'
BOTH_ORDERBOOK = 'both'

BASE_URL = 'https://bittrex.com/api/v1.1/%s/'

MARKET_SET = {'getopenorders', 'cancel', 'sellmarket', 'selllimit', 'buymarket', 'buylimit'}

ACCOUNT_SET = {'getbalances', 'getbalance', 'getdepositaddress', 'withdraw', 'getorderhistory'}

sleep_time_in_second = 5


class Bittrex(object):
    """
    Used for requesting Bittrex with API key and API secret
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

    def __call__(self, method, options=None):
        """
        Queries Bittrex with given method and options

        :param method: Query method for getting info
        :type method: str

        :param options: Extra options for query
        :type options: dict

        :return: JSON response from Bittrex
        :rtype : dict
        """
        if not options:
            options = {}
        nonce = str(int(time.time() * 1000))
        method_set = 'public'

        if method in MARKET_SET:
            method_set = 'market'
        elif method in ACCOUNT_SET:
            method_set = 'account'

        request_url = (BASE_URL % method_set) + method + '?'

        if method_set != 'public':
            request_url += 'apikey=' + self.api_key + "&nonce=" + nonce + '&'

        request_url += urlencode(options)

        logger.debug("Bittrex - Request Get: %s", request_url)
        response = requests.get(
            request_url,
            headers={"apisign": hmac.new(self.api_secret.encode(), request_url.encode(), hashlib.sha512).hexdigest()},
            timeout=self.timeout
        )

        if response.status_code != 200:
            logger.error("Bittrex - Response error: HTTP " + str(response.status_code) + " returned with the content " + str(response.text) + ".")
            raise Exception("Bittrex - Response error: HTTP " + str(response.status_code) + " returned.")

        # decode json
        if not self.jsonNums:
            response_json = json.loads(response.text, parse_float=str)
        else:
            response_json = json.loads(
                response.text,
                parse_float=self.jsonNums,
                parse_int=self.jsonNums)

        logger.debug("Bittrex - Response content: " + str(response_json))

        if response_json['success'] is not True:
            logger.error("Bittrex - Response contains a functional error: " + str(response_json))
            raise Exception("Bittrex - Response contains a functional error: " + str(response_json))

        return response_json;

    def get_markets(self):
        """
        Used to get the open and available trading markets
        at Bittrex along with other meta data.

        :return: Available market info in JSON
        :rtype : dict
        """
        return self.__call__('getmarkets')

    def get_currencies(self):
        """
        Used to get all supported currencies at Bittrex
        along with other meta data.

        :return: Supported currencies info in JSON
        :rtype : dict
        """
        return self.__call__('getcurrencies')

    def get_ticker(self, market):
        """
        Used to get the current tick values for a market.

        :param market: String literal for the market (ex: BTC-LTC)
        :type market: str

        :return: Current values for given market in JSON
        :rtype : dict
        """
        return self.__call__('getticker', {'market': market})

    def get_market_summaries(self):
        """
        Used to get the last 24 hour summary of all active exchanges

        :return: Summaries of active exchanges in JSON
        :rtype : dict
        """
        return self.__call__('getmarketsummaries')

    def get_orderbook(self, market, depth_type=BOTH_ORDERBOOK, depth=20):
        """
        Used to get retrieve the orderbook for a given market

        :param market: String literal for the market (ex: BTC-LTC)
        :type market: str

        :param depth_type: buy, sell or both to identify the type of orderbook to return.
            Use constants BUY_ORDERBOOK, SELL_ORDERBOOK, BOTH_ORDERBOOK
        :type depth_type: str

        :param depth: how deep of an order book to retrieve. Max is 100, default is 20
        :type depth: int

        :return: Orderbook of market in JSON
        :rtype : dict
        """

        logger.debug("Bittrex - Get orderbook for " + str(market))
        return self.__call__('getorderbook', {'market': market, 'type': depth_type, 'depth': depth})

    def get_market_history(self, market, count):
        """
        Used to retrieve the latest trades that have occurred for a
        specific market.

        /market/getmarkethistory

        :param market: String literal for the market (ex: BTC-LTC)
        :type market: str

        :param count: Number between 1-100 for the number of entries to return (default = 20)
        :type count: int

        :return: Market history in JSON
        :rtype : dict
        """
        return self.__call__('getmarkethistory', {'market': market, 'count': count})

    def place_limit_order(self, market, way, quantity, price):
        if way == 'Ask':
            self.sell_limit(market, quantity, price)
        elif way == 'Bid':
            self.buy_limit(market, quantity, price)
        else:
            logger.error("Bittrex - Unknown order way " + str(way))
            raise Exception("Bittrex - Unknown order way " + str(way))

    def buy_market(self, market, quantity):
        """
        Used to place a buy order in a specific market. Use buymarket to
        place market orders. Make sure you have the proper permissions
        set on your API keys for this call to work

        /market/buymarket

        :param market: String literal for the market (ex: BTC-LTC)
        :type market: str

        :param quantity: The amount to purchase
        :type quantity: float

        :param rate: The rate at which to place the order.
            This is not needed for market orders
        :type rate: float

        :return:
        :rtype : dict
        """
        return self.__call__('buymarket', {'market': market, 'quantity': quantity})

    def buy_limit(self, market, quantity, rate):
        """
        Used to place a buy order in a specific market. Use buylimit to place
        limit orders Make sure you have the proper permissions set on your
        API keys for this call to work

        /market/buylimit

        :param market: String literal for the market (ex: BTC-LTC)
        :type market: str

        :param quantity: The amount to purchase
        :type quantity: float

        :param rate: The rate at which to place the order.
            This is not needed for market orders
        :type rate: float

        :return:
        :rtype : dict
        """
        logger.debug("Bittrex - Placed a limit Buy order on " + str(market) + " with quantity: " + str(quantity) + " and price " + str(rate))
        return self.__call__('buylimit', {'market': market, 'quantity': quantity, 'rate': rate})

    def sell_market(self, market, quantity):
        """
        Used to place a sell order in a specific market. Use sellmarket to place
        market orders. Make sure you have the proper permissions set on your
        API keys for this call to work

        /market/sellmarket

        :param market: String literal for the market (ex: BTC-LTC)
        :type market: str

        :param quantity: The amount to purchase
        :type quantity: float

        :param rate: The rate at which to place the order.
            This is not needed for market orders
        :type rate: float

        :return:
        :rtype : dict
        """
        logger.debug("Bittrex - Placed a limit Sell order on " + str(market) + " with quantity: " + str(quantity) + " and price " + str(rate))
        return self.__call__('sellmarket', {'market': market, 'quantity': quantity})

    def sell_limit(self, market, quantity, rate):
        """
        Used to place a sell order in a specific market. Use selllimit to place
        limit orders Make sure you have the proper permissions set on your
        API keys for this call to work

        /market/selllimit

        :param market: String literal for the market (ex: BTC-LTC)
        :type market: str

        :param quantity: The amount to purchase
        :type quantity: float

        :param rate: The rate at which to place the order.
            This is not needed for market orders
        :type rate: float

        :return:
        :rtype : dict
        """
        return self.__call__('selllimit', {'market': market, 'quantity': quantity, 'rate': rate})

    def cancel(self, uuid):
        """
        Used to cancel a buy or sell order

        /market/cancel

        :param uuid: uuid of buy or sell order
        :type uuid: str

        :return:
        :rtype : dict
        """
        return self.__call__('cancel', {'uuid': uuid})

    def get_open_orders(self, market):
        """
        Get all orders that you currently have opened. A specific market can be requested

        /market/getopenorders

        :param market: String literal for the market (ie. BTC-LTC)
        :type market: str

        :return: Open orders info in JSON
        :rtype : dict
        """
        return self.__call__('getopenorders', {'market': market}, True)

    def get_balances(self):
        """
        Used to retrieve all balances from your account

        /account/getbalances

        :return: Balances info in JSON
        :rtype : dict
        """
        return self.__call__('getbalances', {}, True)

    def get_balance(self, currency):
        """
        Used to retrieve the balance from your account for a specific currency

        /account/getbalance

        :param currency: String literal for the currency (ex: LTC)
        :type currency: str

        :return: Balance info in JSON
        :rtype : dict
        """
        return self.__call__('getbalance', {'currency': currency}, True)

    def get_deposit_address(self, currency):
        """
        Used to generate or retrieve an address for a specific currency

        /account/getdepositaddress

        :param currency: String literal for the currency (ie. BTC)
        :type currency: str

        :return: Address info in JSON
        :rtype : dict
        """
        return self.__call__('getdepositaddress', {'currency': currency})

    def withdraw(self, currency, quantity, address):
        """
        Used to withdraw funds from your account

        /account/withdraw

        :param currency: String literal for the currency (ie. BTC)
        :type currency: str

        :param quantity: The quantity of coins to withdraw
        :type quantity: float

        :param address: The address where to send the funds.
        :type address: str

        :return:
        :rtype : dict
        """
        return self.__call__('withdraw', {'currency': currency, 'quantity': quantity, 'address': address})

    def get_order_history(self, market, count):
        """
        Used to reterieve order trade history of account

        /account/getorderhistory

        :param market: optional a string literal for the market (ie. BTC-LTC). If ommited, will return for all markets
        :type market: str

        :param count: optional 	the number of records to return
        :type count: int

        :return: order history in JSON
        :rtype : dict

        """
        return self.__call__('getorderhistory', {'market':market, 'count': count})

    def get_clean_balance(self):
        balances = {}
        raw_balance = self.get_balances()
        balances = self.clean_balances(raw_balance)
        return balances

    def clean_balances(self, raw_balances):
        balances = {}
        for balance_currency in raw_balances['result']:
            balances[balance_currency['Currency']] = {}
            balances[balance_currency['Currency']]['Balance'] = balance_currency['Balance']
            balances[balance_currency['Currency']]['AvailableBalance'] = balance_currency['Available']
            balances[balance_currency['Currency']]['OpenOrder'] = balance_currency['Balance'] - balance_currency['Available']
            balances[balance_currency['Currency']]['Pending'] = balance_currency['Pending']
        return balances

    def clean_orderbook(self, market):
        # Output a cleaned dictionnary:
        # {'buy': {Price: Amount, Price: Amount, ...},
        # 'sell' {Price: Amount, Price: Amount, ...}}

        raw_orderbook = self.get_orderbook(market)
        raw_orderbook = raw_orderbook['result']

        orderbook_unordered = {'buy': {}, 'sell': {}}
        orderbook_cleaned = {'buy': {}, 'sell': {}}

        for buy in raw_orderbook['buy']:
            quantity = buy['Quantity']
            price = buy['Rate']
            orderbook_unordered['buy'][price] = quantity
        orderbook_cleaned['buy'] = OrderedDict(sorted(orderbook_unordered['buy'].items(), key=lambda t: t[0], reverse=True))

        for sell in raw_orderbook['sell']:
            quantity = sell['Quantity']
            price = sell['Rate']
            orderbook_unordered['sell'][price] = quantity
        orderbook_cleaned['sell'] = OrderedDict(sorted(orderbook_unordered['sell'].items(), key=lambda t: t[0]))

        return orderbook_cleaned
