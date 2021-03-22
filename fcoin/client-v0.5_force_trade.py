# -*- coding: utf-8 -*-
from fcoin3 import Fcoin
from websocket import create_connection
import time
import sys
import datetime
import _thread
import gzip


fcoin = Fcoin()
ApiKey=''
SecretKey=''
#ApiKey='d6737fdb557a406f86d394ed59e1deee'
#SecretKey='e8387b34c2c84f00b1c052812e0d1188'

#------------------modify these parameters if you changed the coin type--------------
precision            = 6                      # price decimal
quantPrecision       = 2                      # quantity decimal
buy_sell_quantities_base = 5                  # amount for each trading
quantityFactor = 1                            # the more stable the price, the more quantity for trading.  Normally set to 2. If do not use it, set to 1.
trade_paire          = "ftusdt"
oscillation1         = 0.0002                 # aceptable price oscillation
oscillation2         = oscillation1*2         # aceptable price oscillation
oscillation3         = oscillation1*4         # aceptable price oscillation
reTrade_loss         = 0.0002                 # basic acceptable loss rate, for zero benifit.
force_trade_lost     = oscillation3           # accept more loss when force trade is needed.
modifier_buy         = 1.00003                # higher price to buy
modifier_sell        = 0.99997                # lower price to sell
#------------------------------------------------------------------------------------

#total_count = 5     # maximum number of trades

# trade status
cnt_filled = 0    # number of trade succeed
cnt_failed = 0    # number of trade failed
cnt_total = 0     # total number of trade
successRate = 0   # rate of the successful tradings
total_loss = 0
current_cnt = 0


previous_price = 0
price_step = []
order_list = []



maxLoss = 0    # the loss due to force trading

url_ft = "wss://api.fcoin.com/v2/ws"
ft_send = """{"cmd":"sub","args":["depth.L20."""+trade_paire+""""],"id":"1"}"""
trade_flag=1
ft_depth=""

fcoin.auth(ApiKey, SecretKey)

'''
print("============")
result = fcoin.cancel_order("6TfBZ-eORp4_2nO5ar6z000gLLvuWzTTmL1OzOy9OYg=")
print("============")
res=str(result)
print(res)
if(res=='None'):
    print("result is none!")
time.sleep(5)
'''

#order_buy  = fcoin.buy(trade_paire, 1, 0.01)
#print(order_buy)
#time.sleep(0.5)
#buy_order_status  = fcoin.get_order(order_buy['data'])
#print(buy_order_status)
#time.sleep(0.5)
#result = fcoin.cancel_order(order_buy['data'])
#print(result)
#time.sleep(100)

#-----------------------------------------------

def ft_init(tradstr):
    while(1):
        try:
            wsFT = create_connection(url_ft)
            break
        except:
            print('Fcoin connect ws error,retry...')
            time.sleep(1)
    print('FT connection succeed!')
    wsFT.send(tradstr)
    return wsFT


ws_ft = ft_init(ft_send)       


def get_depth_ft():
    global ws_ft
    global trade_flag
    while True:
        try:
            result = ws_ft.recv()
        except:
            print("connection problem FT!")
            ws_ft = ft_init(ft_send)
            time.sleep(1)
            trade_flag=0
            continue

        if result.find("hello") > 0:            
            continue            
        elif result.find('bids')>0:
            trade_flag=1
            return eval(result)
        else:
            continue

def ft_ticker():
    while True:
        global ft_depth
        ft_depth = get_depth_ft()
        print(ft_depth)

def strategy(depth):
    global trade_flag
    global current_cnt
    global price_step
    global order_list
    global cnt_filled
    global cnt_failed
    global cnt_total
    global successRate
    global buy_sell_quantities_base
    global total_loss

    priceBID = depth['bids'][0]
    priceASK = depth['asks'][0]

    # buy++, sell--, for easy trading
    midPrice = (priceBID+priceASK)/2
    midPrice_buy = round(midPrice*modifier_buy, precision)
    midPrice_sell = round(midPrice*modifier_sell, precision) 
    
    if len(price_step) <= 30 :
        time.sleep(0.1)
        price_step.append(midPrice)
        return
    else :
        price_step.pop(0)
        price_step.append(midPrice)

    diff= max(abs((max(price_step)-price_step[30])/price_step[30]),abs((min(price_step)-price_step[30])/price_step[30]))
    print("\n **********diff is %f*********", diff)
    if trade_flag and diff < oscillation3:

        print("--------------------new order started %d---------------------" %(cnt_total+1))

        # modify the quantities according to the price oscillation
        if diff<oscillation1:
            buy_sell_quantities = buy_sell_quantities_base*quantityFactor*quantityFactor
        elif diff<oscillation2:
            buy_sell_quantities = buy_sell_quantities_base*quantityFactor
        else:
            buy_sell_quantities = buy_sell_quantities_base

        # ascending trend, buy first
        if  price_step[10] < price_step[30] and price_step[20] < price_step[30]:  # use two points to judge the trend
            print ("increasing! Buy first!")
            print ("start buy")            
            order_buy  = fcoin.buy(trade_paire, midPrice_buy, buy_sell_quantities)            
            print(order_buy)
            #order_list.append(order_buy['data'])
            print ("start sell")     
            order_sell = fcoin.sell(trade_paire, midPrice_sell, buy_sell_quantities)
            print(order_sell)
            #order_list.append(order_sell['data'])
            print("buy: %.6f, sell: %.6f" % (midPrice_buy, midPrice_sell))

        # descending or other trends, sell first
        elif price_step[10] > price_step[30] and price_step[20] > price_step[30]:
            print ("decreasing! sell first!")
            print ("start sell")     
            order_sell = fcoin.sell(trade_paire, midPrice_sell, buy_sell_quantities)
            print(order_sell)
            #order_list.append(order_sell['data'])
            print ("start buy")     
            order_buy  = fcoin.buy(trade_paire, midPrice_buy, buy_sell_quantities)
            print(order_buy)
            #order_list.append(order_buy['data'])
            print("sell: %.6f, buy: %.6f" % (midPrice_sell, midPrice_buy))

        # for other situations, todo
        else :
            print ("start buy")     
            order_buy  = fcoin.buy(trade_paire, midPrice_buy, buy_sell_quantities)
            print(order_buy)
            #order_list.append(order_buy['data'])
            print ("start sell")     
            order_sell = fcoin.sell(trade_paire, midPrice_sell, buy_sell_quantities)
            print(order_sell)
            #order_list.append(order_sell['data'])
            print("buy: %.6f, sell: %.6f" % (midPrice_buy, midPrice_sell))

        # avoid exceeding the requesting time limit
        time.sleep(0.1)   #3

        # check buy-sell request, make sure that the buy-sell request is received by the server
        #------------------------------------------------------------------------------------------------
        midPrice_rebuy = round(midPrice_buy*(1+reTrade_loss),precision)
        midPrice_resell = round(midPrice_sell*(1-reTrade_loss),precision)
        while 1:
            if( str(order_buy)=='None' and str(order_sell)=='None' ):
                print ("reTrade: buy")     
                order_buy  = fcoin.buy(trade_paire, midPrice_rebuy, buy_sell_quantities)
                print(order_buy)
                print ("reTrade: sell")    
                order_sell = fcoin.sell(trade_paire, midPrice_resell, buy_sell_quantities)
                print(order_sell)
                time.sleep(2)  #3

            elif( str(order_buy)=='None' ):
                print ("reTrade: buy")      
                order_buy  = fcoin.buy(trade_paire, midPrice_rebuy, buy_sell_quantities)
                print(order_buy)
                time.sleep(1)  #2

            elif( str(order_sell)=='None' ):
                print ("reTrade: sell")     
                order_sell = fcoin.sell(trade_paire, midPrice_resell, buy_sell_quantities)
                print(order_sell)
                time.sleep(1)  #2

            else:
                break                
         #------------------------------------------------------------------------------------------------       

        while 1:
            buy_order_status  = fcoin.get_order(order_buy['data'])
            if(str(buy_order_status)=='None'):
                print("Re-get buy order status!")
                time.sleep(1)
                continue
            else:
                print(buy_order_status['data']['state'])
                time.sleep(1)
                break
        #print(buy_order_status)
        #time.sleep(0.1)

        while 1:
            sell_order_status = fcoin.get_order(order_sell['data'])
            if(str(sell_order_status)=='None'):
                print("Re-get sell order status!")
                time.sleep(1)
                continue
            else:
                print(sell_order_status['data']['state'])
                time.sleep(1)
                break
            
        #print(sell_order_status['data']['state'])
        #print(sell_order_status)
        #time.sleep(0.1)

        cnt_total += 1     
        
        ###############################################################
        # if two order all filled
        if (buy_order_status['data']['state'] == "filled" and sell_order_status['data']['state']== "filled"):
            cnt_filled += 1
            print("-------filled ok-------")
        ###############################################################
            
        #########################################################################
        # if buy order not filled, cancel the order and set next iteration to buy
        else :
            if buy_order_status['data']['state']== "submitted" or buy_order_status['data']['state']== "partial_filled" :                
                print("cancel buy order")
                cancelResult = fcoin.cancel_order(order_buy['data'])                
                print (cancelResult)
                cancelResult=str(cancelResult)
                time.sleep(1)

                # cancel request succeed
                if(cancelResult!='None'):
                    # **********************check the order status and apply a forced trading**********************
                    while 1:
                        print ("===waiting for order status===")
                        while 1:
                            buy_order_status  = fcoin.get_order(order_buy['data'])
                            if(str(buy_order_status)=='None'):
                                print("Re-get buy order status!")
                                time.sleep(1)
                                continue
                            else:
                                print(buy_order_status['data']['state'])
                                time.sleep(1)
                                break
                            
                        #time.sleep(1)
                        
                        if buy_order_status['data']['state']== "filled" :
                            print ("===order filled===")
                            cnt_filled += 1
                            break
                        
                        elif buy_order_status['data']['state']== "canceled" or buy_order_status['data']['state']== "partial_canceled" :                            
                            print("-------------buy order cancelled! re-buy!!---------")
                            buy_quantities = buy_sell_quantities - float(buy_order_status['data']['filled_amount'])
                            lossRate = force_trade_lost

                            #better idea is to use market trade, not limit trade
                            while 1:
                                buy_order = fcoin.buy(trade_paire, round(midPrice_buy*(1+lossRate),precision), round(buy_quantities,quantPrecision))
                                if (str(buy_order)!='None'):
                                    break
                                else:
                                    print("-------------buy order cancelled! re-buy!!---------")
                                    time.sleep(1)

                            total_loss += (lossRate/2)   # average loss percentage
                    
                            #print ("force buy, price is %f,  loss rate: %.6f" %(round(midPrice_buy*(1+lossRate),precision), lossRate))
                            cnt_failed += 1
                            break
                        
                        else:
                            continue
                    # ********************************************************************************************
                    print("----------------------")
                    
                else:
                    print("wrong cancel request!")
                    cnt_filled += 1
                    print("----------------------") 
                
                
            #######################################################################
            # if sell order not filled, cancel the order and set next iteration to sell
            if sell_order_status['data']['state']== "submitted" or sell_order_status['data']['state']== "partial_filled" :                
                print("cancel sell order")
                cancelResult = fcoin.cancel_order(order_sell['data'])               
                print (cancelResult)
                cancelResult=str(cancelResult)
                time.sleep(1)

                 # cancel request succeed
                if(cancelResult!='None'):
                    # **********************check the order status and apply a forced trading**********************
                    while 1:
                        print ("===waiting for order status===")
                        while 1:
                            sell_order_status  = fcoin.get_order(order_sell['data'])
                            if(str(sell_order_status)=='None'):
                                print("Re-get sell order status!")
                                time.sleep(1)
                                continue
                            else:
                                print(sell_order_status['data']['state'])
                                time.sleep(1)
                                break
                            
                        #time.sleep(1)
                        
                        if sell_order_status['data']['state']== "filled" :
                            print ("===order filled===")
                            cnt_filled += 1
                            break
                        
                        elif sell_order_status['data']['state']== "canceled" or sell_order_status['data']['state']== "partial_canceled" :                            
                            print("---------sell order cancelled! re-sell!!---------")
                            sell_quantities = buy_sell_quantities - float(sell_order_status['data']['filled_amount'])
                            lossRate = force_trade_lost

                            #better idea is to use market trade, not limit trade
                            while 1:
                                sell_order = fcoin.sell(trade_paire, round(midPrice_sell*(1-lossRate),precision), round(sell_quantities,quantPrecision))
                                if (str(sell_order)!='None'):
                                    break
                                else:
                                    print("-------------sell order cancelled! re-sell!!---------")
                                    time.sleep(1)


                            total_loss += (lossRate/2)    # average loss percentage
                    
                            print ("force buy, price is %f,  loss rate: %.6f" %(round(midPrice_sell*(1-lossRate),precision), lossRate))
                            cnt_failed += 1
                            break
                        
                        else:
                            continue
                    # ********************************************************************************************
                    print("----------------------")
                    
                else:
                    print("wrong cancel request!")
                    cnt_filled += 1
                    print("----------------------") 
                    
                
            ######################################################################
        
        
        successRate = cnt_filled/cnt_total
        print( "*** ratio of successful tradings: %f,  total loss: %f, total loss in percentage: %f" % (successRate, total_loss, total_loss*1000*(1-successRate)) )

        time.sleep(2)

    else:
        time.sleep(1)
        
    '''    
    if diff > 0.00025:
        for i in range (0,len(order_list)) :
            if i < 5:
                order_id = order_list[0]
                order_list.pop(0)
                fcoin.cancel_order(order_id)
                time.sleep(1)
    '''      
    return
#-----------------------------------------------------------------------------------
try:
    _thread.start_new_thread( ft_ticker, ())
    
except:
   print ("Error: 无法启动线程")
   sys.exit(0)
#----------------------------------------------------------------------------------
while 1:
    try : 
        
        if(trade_flag and ft_depth!=""):   
            strategy(ft_depth)
        
    except :
        print("######################################################Eception#########################################################")
        time.sleep(1)


