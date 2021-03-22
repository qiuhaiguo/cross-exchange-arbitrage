import websocket
import time
import sys
import json
import hashlib
import zlib
import base64

#---use Rest for trade-----------------
from okex.OkcoinSpotAPI import OKCoinSpot
from okex.OkcoinFutureAPI import OKCoinFuture
from huobi.HuobiSpotAPI import HuobiSpot

import datetime

#go_trade = 1
EOShuobi = 526
EOSokex = 3
#EOSsum=529
BTChuobi = 0.12820
BTCokex = 1.06895
#BTCsum=1.19715    1,18255
        
class TradeStrategy:

    def __init__(self, comm_okex, comm_huobi):
        self.commOKEX = comm_okex
        self.commHUOBI = comm_huobi
        self.go_trade = 1
        self.total_gain = 0
        self.last_trade_amount = 0
        self.price_precision = 8
        self.trade_limit = 5      # number of trades
        self.max_trade_amount = 10  # EOS amount in each trade
        self.trade_amount_factor = 0.3
        self.amount_precision = 2
        self.EOShuobi = EOShuobi
        self.EOSokex = EOSokex
        self.BTChuobi = BTChuobi
        self.BTCokex = BTCokex
        
    def RiskControl(self, ok_res, huobi_res):
        print("risk contolling!")
        if(ok_res.find("true")<0):
            self.go_trade=0
            print("stop trade due to OKEX order error!")
        if(huobi_res.find("'ok'")<0):
            self.go_trade=0
            print("stop trade due to HUOBI order error!")
        

    def strategy(self, okex_result, huobi_result, ok_spot, huobi_spot, trade_flagOKEX, trade_flagHUOBI, symbol_okex, symbol_huobi, fout):    
        #print("do strategy here!")        
                
        huobi_ask_price_1 = float(huobi_result['tick']['asks'][0][0])
        huobi_ask_amount_1 = float(huobi_result['tick']['asks'][0][1])
        huobi_bid_price_1 = float(huobi_result['tick']['bids'][0][0])
        huobi_bid_amount_1 = float(huobi_result['tick']['bids'][0][1])    
                
        okex_ask_price_1  = float(okex_result['data']['asks'][4][0])
        okex_ask_amount_1  = float(okex_result['data']['asks'][4][1])
        okex_bid_price_1  = float(okex_result['data']['bids'][0][0])
        okex_bid_amount_1  = float(okex_result['data']['bids'][0][1])
          
        price_diff_h2o =  huobi_bid_price_1 - okex_ask_price_1   
        price_diff_o2h =  okex_bid_price_1 - huobi_ask_price_1

        #print(okex_ask_amount_1)

        # strategy 1: huobi sell, okex buy           
        if (price_diff_h2o > 0):
            amount = round( min(huobi_bid_amount_1, okex_ask_amount_1), self.amount_precision)  # trade quantity
            gain = huobi_bid_price_1*amount - okex_ask_price_1*amount
            commission = self.commHUOBI * huobi_bid_price_1*amount + self.commOKEX * okex_ask_price_1*amount
            net_gain = gain - commission
            #print("1: net gain: %.8f,  amount: %f" % (net_gain, amount))
                    
            if (net_gain > 0):  

                #-------------------caution!!!!! real trade--------------------------
                if(trade_flagOKEX==1 and trade_flagHUOBI==1 and self.go_trade>0):
                    #trade_strategy_01(ok_spot, huobi_spot, okex_ask_price_1, huobi_bid_price_1, amount)

                    if(amount>self.max_trade_amount):
                        amount=self.max_trade_amount

                    if(net_gain<0.0001):
                        amount= max(amount  * self.trade_amount_factor, 0.1)
                        #print("reduce amount")

                    amount = round(amount, self.amount_precision)
                        
                    price=round(huobi_bid_price_1*0.9996, self.price_precision)
                    print(okex_ask_price_1)
                    
                    resOKEX = ok_spot.trade(symbol_okex,'buy',okex_ask_price_1*1.0005, amount)
                    resHUOBI = huobi_spot.sendOrder(str(amount),'', symbol_huobi, 'sell-limit', str(price))

                    gain = huobi_bid_price_1*0.9997*amount - okex_ask_price_1*1.0003*amount
                    commission = self.commHUOBI * huobi_bid_price_1*0.9997*amount + self.commOKEX * okex_ask_price_1*1.0003*amount
                    net_gain = gain - commission
                    self.total_gain = self.total_gain + net_gain

                    print("启动交易！火币卖出价： %.8f， OK买入价: %.8f,  数量: %.8f, 交易净赚: %.8f, 总获利: %.8f\n okex: %s\n huobi: %s\n" 
                      % (huobi_bid_price_1*0.9996, okex_ask_price_1*1.0003, amount, net_gain, self.total_gain, resOKEX, resHUOBI))

                    fout.write("启动交易！火币卖出价： %.8f， OK买入价: %.8f,  数量: %.8f, 交易净赚: %.8f, 总获利: %.8f\n okex: %s\n huobi: %s\n" 
                      % (huobi_bid_price_1*0.9996, okex_ask_price_1*1.0003, amount, net_gain, self.total_gain, resOKEX, resHUOBI))
                    
                    self.go_trade=self.go_trade+1                    
                    self.EOSokex = self.EOSokex + amount
                    self.EOShuobi = self.EOShuobi - amount
                    if(self.EOShuobi<self.max_trade_amount):
                        self.go_trade=0
                    # need to check btc, too
                    
                    if(self.go_trade>self.trade_limit):
                        self.go_trade=0
                        print("not enough balance")

                    #self.RiskControl(resOKEX, resHUOBI)
                #--------------------------------------------------------------------
               
        # strategy 2: huobi buy, okex sell
        if (price_diff_o2h > 0):
            amount = min(huobi_ask_amount_1, okex_bid_amount_1)  # trade quantity
            gain = okex_bid_price_1*amount - huobi_ask_price_1*amount
            commission = self.commHUOBI*huobi_ask_price_1*amount + self.commOKEX*okex_bid_price_1*amount
            net_gain = gain - commission
                    
            if (net_gain > 0):

                #----------------caution!!! real trade--------------------------------------
                if(trade_flagOKEX==1 and trade_flagHUOBI==1 and self.go_trade>0):
                    #trade_strategy_02(ok_spot, huobi_spot, okex_bid_price_1, huobi_ask_price_1, amount)

                    if(amount>self.max_trade_amount):
                        amount=self.max_trade_amount

                    if(net_gain<0.0001):
                        amount=max(amount  * self.trade_amount_factor, 0.1)
                        #print("reduce amount")

                    amount = round(amount, self.amount_precision)
                        
                    price=round(huobi_ask_price_1*1.0003, self.price_precision)
                    #print(price)
                    
                    resOKEX = ok_spot.trade(symbol_okex,'sell',okex_bid_price_1*0.9996, amount)
                    resHUOBI = huobi_spot.sendOrder(str(amount),'', symbol_huobi, 'buy-limit', str(price))
                    
                    gain = huobi_ask_price_1*1.0002*amount - okex_bid_price_1*0.9997*amount
                    commission = self.commHUOBI * huobi_ask_price_1*1.0002*amount + self.commOKEX * okex_bid_price_1*0.9997*amount
                    net_gain = gain - commission
                    self.total_gain = self.total_gain + net_gain
                    
                    print("启动交易！火币买入价： %.8f， OK卖出价: %.8f, 数量: %.8f, 交易净赚: %.8f, 总获利: %.8f\n okex: %s\n huobi: %s\n"
                      % (huobi_ask_price_1*1.0003, okex_bid_price_1*0.9996, amount, net_gain, self.total_gain, resOKEX, resHUOBI))
                    
                    fout.write("启动交易！火币买入价： %.8f， OK卖出价: %.8f, 数量: %.8f, 交易净赚: %.8f, 总获利: %.8f\n okex: %s\n huobi: %s\n"
                      % (huobi_ask_price_1*1.0003, okex_bid_price_1*0.9996, amount, net_gain, self.total_gain, resOKEX, resHUOBI))
                    
                    self.go_trade=self.go_trade+1

                    self.EOSokex = self.EOSokex - amount
                    self.EOShuobi = self.EOShuobi + amount
                    if(self.EOSokex<self.max_trade_amount):
                        self.go_trade=0
                        print("not enough balance")
                    # need to check btc, too
                        
                    if(self.go_trade>self.trade_limit):
                        self.go_trade=0

                    #self.RiskControl(resOKEX, resHUOBI)
                #----------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------
