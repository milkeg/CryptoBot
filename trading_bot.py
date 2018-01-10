import strategy_config

from gatecoin import gatecoin
from bittrex import bittrex
from liqui import liqui

import datetime
import logging
from pprint import pprint

logger = logging.getLogger("TradingBot")
logger.setLevel(logging.DEBUG)
# Create a file handler
handler = logging.FileHandler('./log_' + datetime.datetime.now().strftime("%Y-%m-%d") + '.log')
handler.setLevel(logging.INFO)
# Create a logging format
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
# Add the handlers to the logger
logger.addHandler(handler)

if __name__ == "__main__":

    logger.info("------------------------------------------------------------------------------")
    logger.info("------------------------------- CONFIGURATION --------------------------------")
    logger.info("------------------------------------------------------------------------------")

    exchange = {}
    orderbook = {}
    orderbook_raw = {}
    exchange['Gatecoin'] = gatecoin.Gatecoin(
        "https://api.gatecoin.com",
        strategy_config.gatecoin['public'],
        strategy_config.gatecoin['private'])
    orderbook['Gatecoin'] = {}

    exchange['Bittrex'] = bittrex.Bittrex(
        strategy_config.bittrex['public'],
        strategy_config.bittrex['private'])
    orderbook['Bittrex'] = {}

    exchange['Liqui'] = liqui.Liqui(
        strategy_config.liqui['public'],
        strategy_config.liqui['private'])
    orderbook['Liqui'] = {}

    currency_pairs = strategy_config.currency_pairs
    one_bp_in_pourcent = strategy_config.one_bp_in_pourcent

    logger.info("------------------------------------------------------------------------------")
    logger.info("-------------------------------- PROCESSING ----------------------------------")
    logger.info("------------------------------------------------------------------------------")

    for currency_pair in currency_pairs:
        # Simple example on getting the order book for the currency from 2 exchanges: Gatecoin and Bittrex
        logger.info("Getting the Primary exchange clean orderbook")
        orderbook[currency_pair['Primary_exchange']] = exchange[currency_pair['Primary_exchange']].clean_orderbook(currency_pair['Primary_exchange_currencypair'])
        pprint(orderbook[currency_pair['Primary_exchange']])
        logger.info("Getting the Secondary exchange clean orderbook")
        orderbook[currency_pair['Secondary_exchange']] = exchange[currency_pair['Secondary_exchange']].clean_orderbook(currency_pair['Secondary_exchange_currencypair'])
        pprint(orderbook[currency_pair['Secondary_exchange']])

    quit()
