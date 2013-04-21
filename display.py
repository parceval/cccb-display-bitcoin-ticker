'this script displays current mtgox eur, usd rates and the latest trades on the ccc berlin club display.'

from socket import *
import struct
import json
import urllib2
from time import sleep
import datetime
import threading

address = ('172.23.42.29', 2342)
client_socket = socket(AF_INET, SOCK_DGRAM)

TICKER = {'USD': 'http://data.mtgox.com/api/2/BTCUSD/money/trades/fetch',
          'EUR': 'http://data.mtgox.com/api/2/BTCEUR/money/trades/fetch'
          }

RATES = [ ('EUR', 'http://data.mtgox.com/api/2/BTCEUR/money/ticker'),
          ('USD', 'http://data.mtgox.com/api/2/BTCUSD/money/ticker'),
          ]

XSIZE = 56
YSIZE = 20
SLEEP_TICKER = 0.15
RATES_POLL_INTERVAL = 10.0
RATES_WINDOW_WIDTH = 25

def show_text(x,y,text):
    data = struct.pack("!hhhhh%ds" % len(text),3,x,y,len(text),1,text)
    client_socket.sendto(data, address)

def display_text(text):
    padded=""
    for line_number, line in enumerate(text.splitlines()):
        padded=padded + line
        padded = padded + ' ' * (RATES_WINDOW_WIDTH - len(line))

    data = struct.pack("!hhhhh%ds" % len(padded),3,0,3,RATES_WINDOW_WIDTH,line_number,str(padded))
    client_socket.sendto(data, address)

def clear_screen():
    data = struct.pack("!hhhhh",2,0,0,0,0)
    client_socket.sendto(data, address)

def fetch_rates(url):
    f = urllib2.urlopen(url)
    resp = json.load(f)
    rates = {'avg': float( resp['data']['avg']['value'] ),
             'buy': float( resp['data']['buy']['value'] ),
             'sell': float( resp['data']['sell']['value'] ),
                 'low': float( resp['data']['low']['value'] ),
                 'high': float( resp['data']['high']['value'] )
                 }
    return rates

def format_currency(currency, rates, old_rates):
    def trend(key):
        if key not in old_rates:
            return ' '
        if rates[key] < old_rates[key]: # -
            return chr(0x19)
        elif rates[key] > old_rates[key]: # +
            return chr(0x18)
        else:
            return ' '

    return '''mtgox  BUY   %9.5f%s
  %s  SELL  %9.5f%s
       AVG   %9.5f%s
       LOW   %9.5f%s
       HIGH  %9.5f%s



''' % (rates['buy'],trend('buy'),
       currency,
       rates['sell'], trend('sell'),
       rates['avg'], trend('avg'),
       rates['low'], trend('low'),
       rates['high'], trend('high'),
       )

def fetch_trades(currency):
    f = urllib2.urlopen(TICKER[currency])
    resp = json.load(f)
    trades = ""

    for trade in resp['data']:
        trades+= " %s (%s %s)," % (trade['amount'], trade['price'], currency)

    return str(" lastest trades " + trades)

def update_ticker():
    infos =  " " * XSIZE + fetch_trades('EUR')
    pos = 0
    while True:
        text = infos[pos:pos+XSIZE]
        show_text(0,YSIZE-1, text)
        sleep(SLEEP_TICKER)
        pos+=1
        if pos == len(infos):
            infos = fetch_trades()
            pos=0

def update_header():
    while True:
        show_text(0,0, 'Bitcoin Information %s' % datetime.datetime.now().strftime("%a %d.%m.%Y %H:%M:%S") )
        sleep(0.5)

def start_thread(fn):
    t = threading.Thread(target=fn)
    t.daemon = True
    t.start()

if __name__ == '__main__':
    last_rates = dict()

    clear_screen()
    start_thread(update_header)
    start_thread(update_ticker)

    while True:
        last_text = text = ''

        for currency, url in RATES:
            rates = fetch_rates(url)
            currency_text = format_currency(currency, rates, last_rates.get(currency,dict()))
            last_rates[currency] = rates
            text = text + currency_text

        #only update display if changes happend
        if text != last_text:
            display_text(text)

        last_text = text
        sleep(RATES_POLL_INTERVAL)
