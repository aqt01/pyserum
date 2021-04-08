import re
import ast
import base58
import requests
import logging
import json
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Tuple
)
from pyserum.connection import conn
from solana.rpc.types import TxOpts
from pyserum.enums import Side, OrderType
from pyserum.market import Market
from solana.account import Account
from solana.rpc.types import TokenAccountOpts


MARKETS = 'https://raw.githubusercontent.com/project-serum/serum-ts/master/packages/serum/src/markets.json'
TOKEN_MINTS = 'https://raw.githubusercontent.com/project-serum/serum-ts/master/packages/serum/src/token-mints.json'
CC = conn("https://api.mainnet-beta.solana.com/")
CENTRALIZED = False 
EXAMPLE_PAIR = "BTC-USDT"
DEFAULT_FEES = [0.1, 0.1]
TRADING_PAIR_SPLITTER = re.compile(r"^(\w+)(BTC|ETH|BNB|DAI|XRP|USDT|USDC|USDS|TUSD|PAX|TRX|BUSD|NGN|RUB|TRY|EUR|IDRT|ZAR|UAH|GBP|BKRW|BIDR)$")
logging.getLogger("urllib3").setLevel(logging.ERROR)
logging.getLogger("solanaweb3").setLevel(logging.ERROR)


def init_data():
    data = '' 
    with open('keys.json', 'r') as outfile:
        data = json.load(outfile) 
    
    if data['priv_key'] == '':
        data['priv_key'] = str(input("Please enter your {0}:".format(key)))

        with open('keys.json', 'r') as outfile:
            json.dump(data, outfile) 

    return data 

def init_data_serum():
    # for further info. check 
    # https://github.com/kal1er/simpleClient-for-pyserum/blob/1a80a87786a3d9e3ae6828888b7dedd25973ed62/cfApi_solserum.py#L29
    config_data = init_data()

    if config_data["priv_key"][0]=='[': # we evaluate if account is given in list format
        config_data["priv_key"] = ast.literal_eval(config_data["priv_key"])[0:32]
    else:
       config_data["priv_key"] = base58.b58decode(config_data["priv_key"])[:32]

    return config_data


def load_bids(market):
    bids = market.load_bids()
    for bid in bids:
        print("Order id: %d, price: %f, size: %f." % (
              bid.order_id, bid.info.price, bid.info.size))

def load_asks(market):
    asks = market.load_asks()
    for ask in asks:
        print("Order id: %d, price: %f, size: %f." % (
              ask.order_id, ask.info.price, ask.info.size))


def split_trading_pair(trading_pair: str) -> Optional[Tuple[str, str]]:
    try:
        m = TRADING_PAIR_SPLITTER.match(trading_pair)
        return m.group(1), m.group(2)
    # Exceptions are now logged as warnings in trading pair fetcher
    except Exception:
        return None


def convert_from_exchange_trading_pair(exchange_trading_pair: str) -> Optional[str]:
    if split_trading_pair(exchange_trading_pair) is None:
        return None
    # Huobi uses lowercase (btcusdt)
    base_asset, quote_asset = split_trading_pair(exchange_trading_pair)
    return f"{base_asset.upper()}-{quote_asset.upper()}"


def convert_to_exchange_trading_pair(hb_trading_pair: str) -> str:
    # Binance does not split BASEQUOTE (BTCUSDT)
    return hb_trading_pair.replace("/", "-")


def convert_to_exchange_trading_pair_ws(hb_trading_pair: str) -> str:
    # Binance does not split BASEQUOTE (BTCUSDT)
    return hb_trading_pair.replace("-", "/")


def get_market_address(pair: str) -> str:
    try:
        trading_pairs = requests.get(MARKETS).json()
        undeprecated_pairs = list()
        
        if pair == 'USDC/ODOP':
            return '9kheVGeeCSrN4jWte8oPiFaSAQn6WCdRfj6z7GhpqZwG'

        pair = pair.replace('/', '-')

        for pairs in trading_pairs:
            if pairs['deprecated'] == False:
                pairs['name'] = pairs['name'].replace('/', '-')
                if pairs['name'] == pair:
                    print('Found pair')
                    return pairs['address']
        return None

    except Exception:
        print("Error finding trading pair {0}".format(pair))
        return []
        pass

# Should we get an function for get 
def get_quote_address(quote: str):
    try: 
        trading_pairs = requests.get(TOKEN_MINTS).json()
        undeprecated_pairs = list()
        for pairs in trading_pairs:
            if pairs['name'] == quote:
                return pairs['address']
        return 'Not Found'
    except Exception:
        return []
        pass

def load_bids(trading_pair: str, qnt: int):
    if qnt==None:
        qnt = 10

    market_address = get_market_address(trading_pair)
    market = Market.load(CC, market_address)
    bids = market.load_bids()
    bids_pair = list()
    list_price_size = list()
    i=0

    for idx, bid in enumerate(bids):
        list_price_size.append(bid.info.price)
        list_price_size.append(bid.info.size)
        bids_pair.append(list_price_size)
        list_price_size = list()
        i+=1
        if i==qnt:
            break
    return bids_pair

def load_bids_txt(market_address: str, qnt: int):
    if qnt==None:
        qnt = 10

    market = Market.load(CC, market_address)
    bids = market.load_bids()
    bids_text = 'Buy orders:\n'
    i=0

    for bid in bids:
        i+=1
        bids_text += "price: %.2f, size: %.2f\n" % (bid.info.price, bid.info.size)
        if (i==qnt):
            break
    return bids_text

def load_asks(trading_pair: str, qnt: int):
    if qnt==None:
        qnt = 10

    market_address = get_market_address(trading_pair)
    market = Market.load(CC, market_address)
    asks = market.load_asks()
    asks_pair = list()
    list_price_size = list()
    i = 0
    for idx, ask in enumerate(asks):
        list_price_size.append(ask.info.price)
        list_price_size.append(ask.info.size)
        asks_pair.append(list_price_size)
        list_price_size = list()
        
        i+=1
        if i==qnt:
            break

    return asks_pair

def load_asks_txt(market_address: str, qnt: int):
    if qnt==None:
        qnt = 10

    market = Market.load(CC, market_address)
    asks = market.load_asks()
    asks_text = 'Sell orders:\n'

    i=0
    for ask in asks:
        i+=1
        asks_text += "price: %.2f, size: %.2f\n" % (ask.info.price, ask.info.size)
        if (i==qnt):
            break

    return asks_text

def load_fills(trading_pair: str):
    market_address = get_market_address(trading_pair)
    market = Market.load(CC, market_address)
    fills = market.load_fills()
    return fills

def load_snapshot(trading_pair: str):
    bids = load_bids(trading_pair)
    asks = load_asks(trading_pair)
    #bids = bids[len(bids):-2]
    #asks = asks[0:2]

    return  {'name': trading_pair, 'bids': bids, 'asks': asks}

def load_trading_pairs() -> List[str]:
    undeprecated_pairs = list()
    trading_pairs = requests.get(MARKETS).json()
    for pairs in trading_pairs:
        if pairs['deprecated'] == False:
            pair_name = pairs['name'].replace('/', '-')
            undeprecated_pairs.append(pair_name)
    return undeprecated_pairs

def place_order_serum(params: dict) -> str:
    try:
        market_address = get_market_address(params['market'])
        market = Market(CC, market_address)
        if params['side'] == 'buy':
            params['side'] = Side.Buy
        else:
            params['side'] = Side.Sell
        if params['type'] == 'limit':
            params['type'] = OrderType.Limit
        else:
            params['type'] = OrderType.PostOnly

        tx_sig = market.place_order(
            payer=params['wallet_quote'],
            owner=params['payer'],
            side=params['side'],
            order_type=params['type'],
            limit_price=params['price'],
            max_quantity=params['size'],
            opts=TxOpts()
        )
        return tx_sig
    except Exception:
        return None

def get_balance(token: str) -> str:
    try:
        market = Market(CC, "So11111111111111111111111111111111111111112")
        market_quote = market.find_quote_token_accounts_for_owner(owner_address=acc)
        return market_quote
    except Exception:
        return None

