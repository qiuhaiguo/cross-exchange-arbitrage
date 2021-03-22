from websocket import create_connection
import time
import sys
import datetime
import _thread
import gzip

import ast

from okex.OkcoinSpotAPI import OKCoinSpot
from huobi.HuobiSpotAPI import HuobiSpot
from TradeStrategies import TradeStrategy

#----------global settings----------------

#total_gain = 0
#last_trade_amount = 0
comm_rate_huobi = 0.0025 * 1.0
comm_rate_okex = 0.0025 * 1.0

price_precision = 8   # 价格小数点之后的位数。不同的币是不一样的，这里先手动设置。

url_huobi = "wss://api.huobipro.com/ws"
api_key_huobi='a481f120-f5e012a3-902878c4-85123'
secret_key_huobi = "05956fb9-080261d2-51d2795b-0bf5d"


url_okex = "wss://real.okex.com:10441/websocket"      #if okcoin.cn  change url wss://real.okcoin.cn:10440/websocket/okcoinapi
api_key_okex='4f35c1c2-ea57-49b5-ac9d-2e7e133273ca'
secret_key_okex = "14CC4C180B4030FF142D6A5F6E2C650E"

symbol_huobi = "eosbtc"
symbol_okex = "eos_btc"
huobi_send = """{"sub": "market."""+symbol_huobi+""".depth.step0", "id": "smilley"}"""
okex_send = "{'event':'addChannel','channel':'ok_sub_spot_"+symbol_okex+"_depth_5'}"

okcoinSpot = OKCoinSpot("www.okex.com",api_key_okex,secret_key_okex)
huobiSpot  = HuobiSpot()
mystrategy = TradeStrategy(comm_rate_okex, comm_rate_huobi)
okex_depth=""
huobi_depth=""


#-----------trade------------------
trade_flag_okex = 0
trade_flag_huobi = 0
emergency_stop = 0
#----------------------------------------------------------------------
def huobi_init(tradstr):
    while(1):
        try:
            wsHuobi = create_connection(url_huobi)
            break
        except:
            print('huobi connect ws error,retry...')
            time.sleep(1)
    print('huobi connection succeed!')
    wsHuobi.send(tradstr)
    return wsHuobi

def okex_init(tradstr):
    while(1):
        try:
            print(url_okex)
            wsOkex = create_connection(url_okex)
            break
        except:
            print('okex connect ws error,retry...')
            time.sleep(1)
    print('okex connection succeed!')
    wsOkex.send(tradstr);
    return wsOkex

ws_okex = okex_init(okex_send)
ws_huobi = huobi_init(huobi_send)

def get_depth_okex():
    global ws_okex
    global trade_flag_okex
    while True:
        try:
            result = ws_okex.recv()
        except:
            print("connection failed okex!!")
            ws_okex = okex_init(okex_send)
            time.sleep(1)
            trade_flag_okex=0
            continue
        
        if(result.find('true')>0):       # result is a string, the handshake signal contains 'true', which cannot be converted to dict type
            continue
        elif result.find('data')>0:
            result = eval(result[1:-1])
            trade_flag_okex=1
            return result
        else:
            continue
        

def get_depth_huobi():
    global ws_huobi
    global trade_flag_huobi
    while True:
        try:
            result = ws_huobi.recv()
        except:
            print("connection problem huobi!")
            ws_huobi = huobi_init(huobi_send)
            time.sleep(1)
            trade_flag_huobi=0
            continue

        result=gzip.decompress(result).decode('utf-8')        
        if result[:7] == '{"ping"':
            ts=result[8:21]
            pong='{"pong":'+ts+'}'
            ws_huobi.send(pong)
            #print(result)
            continue            
        elif result.find('tick')>0:
            trade_flag_huobi=1
            return eval(result)
        else:
            continue
            
def okex_ticker():
    while True:
        global okex_depth
        okex_depth = get_depth_okex()
        #print("okex depth: ")
        #print(okex_depth['data']['bids'][0][0])
        #print('\n')
        #time.sleep(1)

def huobi_ticker():
    while True:
        global huobi_depth
        huobi_depth = get_depth_huobi()
        #print("huobi depth: ")
        #print(huobi_depth['tick']['asks'][0][1])
        #print('\n')

#---------------------------------------------------------------------------------------------------


try:
    _thread.start_new_thread( huobi_ticker, ())
    _thread.start_new_thread( okex_ticker, ())
    #_thread.start_new_thread( strategy, (okex_depth, huobi_depth,))
    
except:
   print ("Error: 无法启动线程")
   sys.exit(0)


print("start")
fout = open("log.txt","a")

#amount=0.1
#price=0.001
#print (huobiSpot.sendOrder(str(amount),'', symbol_huobi, 'buy-limit', str(price)))
#print (okcoinSpot.trade(symbol_okex,'buy', price, amount))
#print(huobiSpot.getBalance())
#print(okcoinSpot.userinfo())
print(okcoinSpot.orderinfo("eos_btc",-1))
#print (huobiSpot.sendOrder('0.1','', 'eosbtc', 'buy-limit', '0.0006'))
#print (okcoinSpot.trade("eos_btc",'buy',0.00190, 500))
#print(huobiSpot.cancelOrder('3837161091'))
#print(okcoinSpot.cancelOrder("eos_btc", 327419081))

'''
#print(huobiSpot.getAccounts())
print (huobiSpot.sendOrder('0.1','', 'eosbtc', 'buy-limit', '0.0006'))


result = okcoinSpot.trade("eos_btc",'buy',0.0006, 0.1)


#res_info=okcoinSpot.userinfo()

orderID = result['order_id']
print(orderID)
#sleep(3)
#result = cancelOrder("eos_usdt", orderID)
#print(result)
'''
try:
    while 1:
        if(huobi_depth!="" and okex_depth!=""):
            #print(huobi_depth)
            #print(okex_depth)
            #mystrategy.strategy(okex_depth, huobi_depth, okcoinSpot, huobiSpot, trade_flag_okex, trade_flag_huobi, symbol_okex, symbol_huobi, fout)
            x=1
except:
    fout.close()
    sys.exit(0)

'''    
if __name__ == "__main__":
    ws_okex = okex_init(okex_send)
    ws_huobi = huobi_init(huobi_send)

    print('connection succeed!')
    huobi_ticker(ws_huobi)


'''

