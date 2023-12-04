import threading
import time
from binance.client import Client
from config import api

api_key = api.key.get_secret_value()
api_secret = api.secret.get_secret_value()

binance = Client(api_key=api_key, api_secret=api_secret)


class StoppableThread(threading.Thread):
    def __init__(self, *args, **kwargs):
        super(StoppableThread, self).__init__(*args, **kwargs)
        self._stop_event = threading.Event()

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()


threads_dict = {}


class FuturesObj:
    def __init__(self):

        self.symbol = None
        self.leverage = None
        self.value_usd = None
        self.make_long = None
        self.close_long = None
        self.make_short = None
        self.close_short = None

        self.precision = None

    def read_console(self):
        self.symbol = input('Trading pair: ')
        self.leverage = int(input('Leverage: '))
        self.value_usd = int(input('Value usdt: '))
        self.make_long = int(input('Long order price: '))
        self.close_long = int(input('Long order stop-loss: '))
        self.make_short = int(input('Short order price: '))
        self.close_short = int(input('Short order stop-loss: '))

    def read_csv(self, df, number):
        self.symbol = df['Pair'].iloc[number]
        self.leverage = df['Leverage'].iloc[number]
        self.value_usd = df['Value'].iloc[number]
        self.make_long = df['Long_order'].iloc[number]
        self.close_long = df['Long_stop'].iloc[number]
        self.make_short = df['Short_price'].iloc[number]
        self.close_short = df['Short_stop'].iloc[number]

    def __str__(self):
        return (
            f'Trading pair: {self.symbol} \n'
            f'Leverage: {self.leverage} \n'
            f'Value usdt: {self.value_usd} \n'
            f'Long order price: {self.make_long} \n'
            f'Long order stop-loss: {self.close_long} \n'
            f'Short order price: {self.make_short} \n'
            f'Short order stop-loss: {self.close_short} \n'
                )


def get_precision(symbol: str) -> int:
    exchange_info = binance.futures_exchange_info()
    precision = None

    for symbol_info in exchange_info['symbols']:
        if symbol_info['symbol'] == symbol:
            precision = symbol_info['quantityPrecision']

    return int(precision)


def open_position(futures_obj: FuturesObj, price: float, side: tuple[str, str]):
    # Get quantity
    if futures_obj.precision != 0:
        quantity = round((futures_obj.value_usd / price * futures_obj.leverage), futures_obj.precision)
    else:
        quantity = int(futures_obj.value_usd / price * futures_obj.leverage)

    # Open position
    binance.futures_create_order(symbol=futures_obj.symbol,
                                 side=side[0],
                                 type='MARKET',
                                 quantity=quantity)

    position = 'long' if side[0] == 'BUY' else 'short'
    print(f'Open {position} {futures_obj.symbol}')

    # Stop loss
    close_price = futures_obj.close_long if side[0] == 'BUY' else futures_obj.close_short
    binance.futures_create_order(symbol=futures_obj.symbol,
                                 side=side[1],
                                 type='STOP_MARKET',
                                 stopPrice=close_price,
                                 closePosition=True)


def change_position_settings(futures_obj: FuturesObj):
    futures_obj.precision = get_precision(futures_obj.symbol)

    # Change leverage
    binance.futures_change_leverage(symbol=futures_obj.symbol, leverage=futures_obj.leverage)

    # Change margin_type
    position_margin = get_position(futures_obj)['marginType']
    if position_margin != 'cross':
        binance.futures_change_margin_type(symbol=futures_obj.symbol, marginType='CROSSED')


def get_position(futures_obj: FuturesObj):
    positions = binance.futures_position_information()
    for position in positions:
        if position['symbol'] == futures_obj.symbol:
            return position


def check_position(futures_obj: FuturesObj):
    while not threads_dict[futures_obj.symbol].stopped():
        position = get_position(futures_obj)
        if float(position['entryPrice']) <= 0:
            print(f'{futures_obj.symbol} close position')
            check_balance(futures_obj)

        time.sleep(5)


def check_balance(futures_obj: FuturesObj):
    change_position_settings(futures_obj)

    while not threads_dict[futures_obj.symbol].stopped():
        ticker = binance.get_symbol_ticker(symbol=futures_obj.symbol)
        price = float(ticker['price'])

        if price >= futures_obj.make_long:
            open_position(futures_obj, price, ('BUY', 'SELL'))
            time.sleep(5)
            check_position(futures_obj)

        if price <= futures_obj.make_short:
            open_position(futures_obj, price, ('SELL', 'BUY'))
            time.sleep(5)
            check_position(futures_obj)

        time.sleep(0.1)
