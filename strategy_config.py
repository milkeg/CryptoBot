#!/usr/bin/env python
bittrex = {'public': 'PublicKey', 'private': 'PrivateKey'}
gatecoin = {'public': 'PublicKey', 'private': 'PrivateKey'}
liqui = {'public': 'PublicKey', 'private': 'PrivateKey'}

one_bp_in_pourcent = 10000

currency_pairs = []
ETHBTC = {
    'Name': 'ETH/BTC',
    'Base_currency': 'ETH',
    'Quoted_currency': 'BTC',
    'Primary_exchange': 'Gatecoin',
    'Secondary_exchange': 'Bittrex',
    'Secondary_exchange_currencypair': 'BTC-ETH',
    'Primary_exchange_currencypair': 'ETHBTC',
}
currency_pairs.append(ETHBTC)
