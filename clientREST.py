import time
import sys
import datetime
import _thread
import gzip
import json

import ast

from okex.OkcoinSpotAPI import OKCoinSpot
from huobi.HuobiSpotAPI import HuobiSpot
from binance.BinanceSpotAPI import BinanceSpot
from fcoin.fcoin3 import Fcoin
from coinex.coinexAPI import CoinEX

from RestStrategy import TradeStrategy

#----------global settings------------------------------------------------------------------------------

#API Keys
okex_api = '451a9a79-f8fb-40d0-8dd6-be40386dbc49'
okex_sec = ''

huobi_api = '3f6941de-62c0c3df-ad6a007e-891aa'
huobi_sec = ''

binance_api = '5V0ukSTGOkUysSHTg9zaQKOhEp8xAW68QTrIFhjjVdwYWNcyEIgN8OSD5HVUAiDD'
binance_sec = ''

fcoin_api = 'd4b70187808e4722b2047d50ad503a47'
fcoin_sec = ''

coinex_api = 'FE571485FA0943C1B0E1B766F9EA8652'
coinex_sec = ''

#-----------OKEX, HUOBI, BINANCE, FCOIN------------------
symbol = "bch"

symbol_okex       = symbol+"_usdt"
symbol_huobi      = symbol+"usdt"
symbol_binance    = symbol.upper()+"USDT"
symbol_fcoin      = symbol+"usdt"
symbol_coinex     = symbol+"usdt"


commOKEX = 0.002*0.2         # 2折购买点卡
commHUOBI = 0.002*0.3        # 3折购买点卡
commBINANCE = 0.001*0.75     # 使用bnb，享受75折
commFCOIN = 0.0001           # fcoin免手续费
commCOINEX = 0.001*0.5       # 使用cet抵扣50%手续费

okexSpot = OKCoinSpot("www.okex.com",okex_api,okex_sec)
huobiSpot  = HuobiSpot()
binanceSpot = BinanceSpot("https://api.binance.com", binance_api, binance_sec)
fcoinSpot = Fcoin('https://api.fcoin.com/v2/', fcoin_api, fcoin_sec)

coinex = CoinEX(coinex_api, coinex_sec)

ticker_okex = ""
ticker_huobi = ""
ticker_binance = ""
ticker_fcoin = ""
ticker_coinex = ""

trade_flag_okex = 0
trade_flag_huobi = 0
trade_flag_binance = 0
trade_flag_fcoin = 0
trade_flag_coinex = 0

emergency_stop = 0
#----------------------------------------------------------------------
info_ask={}
info_bid={}
refresh_period = 1000                  #refresh the data buffer in ms
global_ts = int(time.time()*1000)
last_time = 0
mystrategy = TradeStrategy(okexSpot, huobiSpot, binanceSpot, fcoinSpot, coinex, symbol)

mystrategy.getAccountInfoFirst()

#-------------test-------------------
#coinexTicker=coinex.getTicker('bchusdt')

#print(coinex.get_account())

#ts = binanceSpot.getServerTime()
#ts_local = int(time.time()*1000)
#print(coinexTicker['data']['date'], ts_local, int(coinexTicker['data']['date']) - ts_local)
#print(coinex.buy_limit('bchusdrt', '0.01', '400'))

#orderInfo = fcoinSpot.sell('eosusdt', 5.01, 0.1)
#print(orderInfo)
#print("test finished!")
#a = okexSpot.trade('bch_usdts','buy', 400, 0.01)
#b=json.loads(a)
#print(b['error_code'])
'''
orderInfo = coinex.buy_limit('eosusdt', str(0.1), str(1))     
#orderInfo = json.loads(orderInfo)
print(orderInfo)
orderID = orderInfo['data']['id']
orderInfo = coinex.order_status(orderID, 'eosusdt')
print(orderInfo)
#orderInfo = json.loads(orderInfo)
status = orderInfo['data']['status']
if status=='not_deal':
    print(coinex.cancel_order(orderID, 'eosusdt'))
                
time.sleep(10)
'''
#-----------------------------get ticker, multiple threads----------------------------------------------------
#---------OKEX-----------
def OKEXticker():
    global ticker_okex
    global trade_flag_okex
    while 1:
        try:
            ticker_okex = okexSpot.depth(symbol_okex, 1)
            if('asks' in ticker_okex.keys()):
                trade_flag_okex = 1
            else:
                trade_flag_okex=0
        except:
            trade_flag_okex=0
            print("get okex ticker error!")
            continue
        time.sleep(0.07)
            
#---------HUOBI-----------
def HUOBIticker():
    global ticker_huobi
    global trade_flag_huobi
    while 1:
        try:
            ticker_huobi = huobiSpot.getTicker(symbol_huobi)
            if(ticker_huobi['status']=='ok'):
                trade_flag_huobi = 1
            else:
                trade_flag_huobi=0
        except:
            trade_flag_huobi=0
            print("get huobi ticker error!")
            continue
        time.sleep(0.051)

#---------BINANCE-----------
def BINANCEticker():
    global ticker_binance
    global trade_flag_binance
    while 1:
        try:
            ticker_binance = binanceSpot.get_ticker(symbol_binance)
            if('bidQty' in ticker_binance.keys()):
                trade_flag_binance = 1
            else:
                trade_flag_binance=0
        except:
            trade_flag_binance=0
            print("get binance ticker error!")
            continue
        time.sleep(0.03)

#---------FCOIN-----------
def FCOINticker():
    global ticker_fcoin
    global trade_flag_fcoin
    while 1:
        try:
            ticker_fcoin = fcoinSpot.get_market_ticker(symbol_fcoin)
            if(ticker_fcoin['status']==0):
                trade_flag_fcoin = 1
            else:
                trade_flag_fcoin=0
        except:
            trade_flag_fcoin=0
            print("get fcoin ticker error!")
            continue
        time.sleep(0.025)

#---------COINEX-----------
def COINEXticker():
    global ticker_coinex
    global trade_flag_coinex
    while 1:
        try:
            ticker_coinex = coinex.get_depth(symbol_coinex, 5)
            if(ticker_coinex['message']=='OK'):
                trade_flag_coinex = 1
            else:
                trade_flag_coinex=0
        except:
            trade_flag_coinex=0
            print("get coinex ticker error!")
            continue
        time.sleep(0.05)


#------行情数据缓存每500ms清除一次----------------------
def getAllTicker():
    global info_ask
    global info_bid
    global global_ts
    while 1:
        #每隔一段时间刷新data buffer
        ts=int(time.time()*1000)         #time stamp in ms
        if ts-global_ts>refresh_period:
            #print("clear data buffer!")
            info_ask={}
            info_bid={}
            global_ts=ts

        #----OKEX-----------            
        if trade_flag_okex==1:
            okex_ask_price_1  = float(ticker_okex['asks'][0][0])
            okex_ask_amount_1  = float(ticker_okex['asks'][0][1])
            okex_bid_price_1  = float(ticker_okex['bids'][0][0])
            okex_bid_amount_1  = float(ticker_okex['bids'][0][1])
            tsOkex=0
            info_ask['okex'] = [okex_ask_price_1,okex_ask_amount_1, commOKEX, tsOkex]
            info_bid['okex'] = [okex_bid_price_1,okex_bid_amount_1, commOKEX, tsOkex]

        #----HUOBI-----------
        if trade_flag_huobi==1:
            huobi_ask_price_1 = float(ticker_huobi['tick']['ask'][0])
            huobi_ask_amount_1 = float(ticker_huobi['tick']['ask'][1])
            huobi_bid_price_1 = float(ticker_huobi['tick']['bid'][0])
            huobi_bid_amount_1 = float(ticker_huobi['tick']['bid'][1])
            tsHuobi = int(ticker_huobi['ts'])
            info_ask['huobi'] = [huobi_ask_price_1,huobi_ask_amount_1, commHUOBI, tsHuobi]
            info_bid['huobi'] = [huobi_bid_price_1,huobi_bid_amount_1, commHUOBI, tsHuobi]

        #----BINANCE-----------
        if trade_flag_binance==1:
            binance_ask_price_1  = float(ticker_binance['askPrice'])
            binance_ask_amount_1  = float(ticker_binance['askQty'])
            binance_bid_price_1  = float(ticker_binance['bidPrice'])
            binance_bid_amount_1  = float(ticker_binance['bidQty'])
            tsBinance = 0
            info_ask['binance'] = [binance_ask_price_1,binance_ask_amount_1, commBINANCE, tsBinance]
            info_bid['binance'] = [binance_bid_price_1,binance_bid_amount_1, commBINANCE, tsBinance]
            

        #----FCOIN-----------
        if trade_flag_fcoin==1:
            fcoin_ask_price_1  = float(ticker_fcoin['data']['ticker'][4])
            fcoin_ask_amount_1  = float(ticker_fcoin['data']['ticker'][5])
            fcoin_bid_price_1  = float(ticker_fcoin['data']['ticker'][2])
            fcoin_bid_amount_1  = float(ticker_fcoin['data']['ticker'][3])
            tsFcoin = int(ticker_fcoin['data']['seq'])
            info_ask['fcoin'] = [fcoin_ask_price_1,fcoin_ask_amount_1, commFCOIN, tsFcoin]
            info_bid['fcoin'] = [fcoin_bid_price_1,fcoin_bid_amount_1, commFCOIN, tsFcoin]

        #----COINEX-----------
        if trade_flag_coinex==1:
            coinex_ask_price_1  = float(ticker_coinex['data']['asks'][0][0])
            coinex_ask_amount_1  = float(ticker_coinex['data']['asks'][0][1])
            coinex_bid_price_1  = float(ticker_coinex['data']['bids'][0][0])
            coinex_bid_amount_1  = float(ticker_coinex['data']['bids'][0][1])
            tsCoinex = 0
            info_ask['coinex'] = [coinex_ask_price_1,coinex_ask_amount_1, commCOINEX, tsCoinex]
            info_bid['coinex'] = [coinex_bid_price_1,coinex_bid_amount_1, commCOINEX, tsCoinex]
            
    

#-----------------------------------------------------------------------------------------
try:
    _thread.start_new_thread( OKEXticker, ())
    _thread.start_new_thread( HUOBIticker, ())
    #_thread.start_new_thread( BINANCEticker, ())
    _thread.start_new_thread( FCOINticker, ())
    _thread.start_new_thread( COINEXticker, ())
    _thread.start_new_thread( getAllTicker, ())
    
except:
   print ("Error: 无法启动线程")
   sys.exit(0)

#current_time = time.strftime('%Y-%m-%d:%H-%M-%S',time.localtime(time.time()))
#current_hour = time.strftime('%H',time.localtime(time.time()))

print("========waiting=============")
time.sleep(2)

while 1:
    x=1    
    try:
        if len(info_ask)>1 and len(info_bid)>1:
            mystrategy.checkPrice(info_ask, info_bid)
            #print("loop!")
            
            #if time.time()-last_time > 10:
                #mystrategy.getAccountInfo()
                #last_time = time.time()
                
        else:
            print("data buffer not enough!")
            time.sleep(1)
            continue
    except:
        print("##########error!############")
        continue

    #time.sleep(2)

   
