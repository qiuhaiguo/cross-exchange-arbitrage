import json
import time

class TradeStrategy:

    def __init__(self, okexSpot, huobiSpot, binanceSpot, fcoinSpot, coinexSpot, symbol):
        self.header = "header"
        self.counter = 0
        self.failed_counter = 0
        self.total_gain = 0        
        self.write_file = False

        self.price_precision = 2
        self.Qty_precision = 2        

        self.okex = okexSpot
        self.huobi = huobiSpot
        self.binance = binanceSpot
        self.fcoin = fcoinSpot
        self.coinex = coinexSpot

        self.symbol = symbol
        self.symbol_okex       = symbol+"_usdt"
        self.symbol_huobi      = symbol+"usdt"
        self.symbol_binance    = symbol.upper()+"USDT"
        self.symbol_fcoin      = symbol+"usdt"
        self.symbol_coinex     = symbol+"usdt"

        #--------account information-----------
        #initial account info
        self.is_init = True
        self.okexInit = [0, 0]
        self.huobiInit = [0, 0]
        self.binanceInit = [0, 0]
        self.fcoinInit = [0, 0]
        self.coinexInit = [0, 0]
        self.coinInit = 0
        self.usdtInit = 0
        
        #current account infor. all accounts are assumed to have 1000 EOS and 5000 usdt
        #initCapital = [0, 0]
        self.acc_okex = [0, 0]
        self.acc_huobi = [0, 0]
        self.acc_binance = [0, 0]
        self.acc_fcoin = [0, 0]
        self.acc_coinex = [0, 0]
        self.coinNow = 0
        self.usdtNow = 0
        self.usdtLast = 0

        #交易利润相关参数
        #*******************************************************************
        self.lastQty = 0
        self.maxQty = 0.01   # maximum buy/sell quantity
        self.minimumQty = 0.001
        self.goTrade = True
        self.tradeLimit = 10   #每次运行程序限制搬砖总次数。测试用
        self.priceDiff = 0.00261   #达到千分之2.5的价差，启动搬砖
        self.buyFactor = 1.002    #让利砸单
        self.sellFactor = 0.998  #让利砸单
        self.rebuyFactor = 1.01
        self.resellFactor = 0.99
        self.waitingTime = 1      #下单之后等待交易时间
        #*******************************************************************

    #第一次获取账户信息   
    def getAccountInfoFirst(self):
        okexInfo = json.loads(self.okex.userinfo())
        huobiInfo = self.huobi.getBalance()
        binanceInfo = self.binance.balances()
        fcoinInfo = self.fcoin.get_balance()
        coinexInfo = self.coinex.get_account()
        
        #OKEX
        #print("okex usdt: ", okexInfo['info']['funds']['free']['usdt'])
        #print("okex "+self.symbol+": ", okexInfo['info']['funds']['free'][self.symbol])
        self.okexInit = [float(okexInfo['info']['funds']['free'][self.symbol]),
                         float(okexInfo['info']['funds']['free']['usdt'])]

        #HUOBI
        balance = huobiInfo['data']['list']
        for i in range(0, len(balance)):
            if balance[i]['currency']=='usdt' and balance[i]['type']=='trade':
                #print("huobi usdt: ", balance[i]['balance'])
                self.huobiInit[1] = float(balance[i]['balance'])
            if balance[i]['currency']==self.symbol and balance[i]['type']=='trade':
                #print("huobi "+self.symbol+": ", balance[i]['balance'])
                self.huobiInit[0] = float(balance[i]['balance'])        
        

        #Binance
        balance = binanceInfo['balances']
        for i in range(0, len(balance)):
            if balance[i]['asset']=='USDT':
                #print("binance usdt: ", balance[i]['free'])
                self.binanceInit[1] = float(balance[i]['free'])
            if balance[i]['asset']==self.symbol.upper():
                #print("binance "+self.symbol+": ", balance[i]['free'])
                self.binanceInit[0] = float(balance[i]['free'])

        #Fcoin
        balance = fcoinInfo['data']
        for i in range(0, len(balance)):
            if balance[i]['currency']=='usdt':
                #print("fcoin usdt: ", balance[i]['available'])
                self.fcoinInit[1] = float(balance[i]['available'])
            if balance[i]['currency']==self.symbol:
                #print("fcoin "+self.symbol+": ", balance[i]['available'])
                self.fcoinInit[0] = float(balance[i]['available'])

        #Coinex
        #print(coinexInfo)
        balance = coinexInfo['data']        
        self.coinexInit[1] = float(balance['USDT']['available'])
        self.coinexInit[0] = float(balance[self.symbol.upper()]['available'])

        print("okex, huobi, binance, fcoin, coinex\n",
              self.okexInit, self.huobiInit, self.binanceInit, self.fcoinInit, self.coinexInit)
        self.acc_okex = self.okexInit
        self.acc_huobi = self.huobiInit
        self.acc_binance = self.binanceInit
        self.acc_fcoin = self.fcoinInit
        self.acc_coinex = self.coinexInit

        self.coinInit = self.acc_okex[0]+self.acc_huobi[0]+self.acc_binance[0]+self.acc_fcoin[0]+self.acc_coinex[0]
        self.usdtInit = self.acc_okex[1]+self.acc_huobi[1]+self.acc_binance[1]+self.acc_fcoin[1]+self.acc_coinex[1]
        self.coinNow = self.coinInit
        self.usdtNow = self.usdtInit
        self.usdtLast = self.usdtNow

        print(self.symbol.upper()+", USDT: ", self.coinInit, self.usdtInit)

    #获取当前所有交易所的账户信息   
    def getAccountInfo(self):
        print("===========update account info===================")
        okexInfo = json.loads(self.okex.userinfo())
        huobiInfo = self.huobi.getBalance()
        #binanceInfo = self.binance.balances()
        fcoinInfo = self.fcoin.get_balance()
        coinexInfo = self.coinex.get_account()

        #OKEX
        #print("okex usdt: ", okexInfo['info']['funds']['free']['usdt'])
        #print("okex "+self.symbol+": ", okexInfo['info']['funds']['free'][self.symbol])
        self.acc_okex = [float(okexInfo['info']['funds']['free'][self.symbol]),
                         float(okexInfo['info']['funds']['free']['usdt'])]

        #HUOBI
        balance = huobiInfo['data']['list']
        for i in range(0, len(balance)):
            if balance[i]['currency']=='usdt' and balance[i]['type']=='trade':
                #print("huobi usdt: ", balance[i]['balance'])
                self.acc_huobi[1] = float(balance[i]['balance'])
            if balance[i]['currency']==self.symbol and balance[i]['type']=='trade':
                #print("huobi "+self.symbol+": ", balance[i]['balance'])
                self.acc_huobi[0] = float(balance[i]['balance'])        
        

        #Binance
        '''
        balance = binanceInfo['balances']
        for i in range(0, len(balance)):
            if balance[i]['asset']=='USDT':
                #print("binance usdt: ", balance[i]['free'])
                self.acc_binance[1] = float(balance[i]['free'])
            if balance[i]['asset']==self.symbol.upper():
                #print("binance "+self.symbol+": ", balance[i]['free'])
                self.acc_binance[0] = float(balance[i]['free'])
        '''

        #Fcoin
        balance = fcoinInfo['data']
        for i in range(0, len(balance)):
            if balance[i]['currency']=='usdt':
                #print("fcoin usdt: ", balance[i]['available'])
                self.acc_fcoin[1] = float(balance[i]['available'])
            if balance[i]['currency']==self.symbol:
                #print("fcoin "+self.symbol+": ", balance[i]['available'])
                self.acc_fcoin[0] = float(balance[i]['available'])

        #Coinex
        #print(coinexInfo)
        balance = coinexInfo['data']        
        self.acc_coinex[1] = float(balance['USDT']['available'])
        self.acc_coinex[0] = float(balance[self.symbol.upper()]['available'])

        self.coinNow = self.acc_okex[0]+self.acc_huobi[0]+self.acc_binance[0]+self.acc_fcoin[0]+self.acc_coinex[0]
        self.usdtNow = self.acc_okex[1]+self.acc_huobi[1]+self.acc_binance[1]+self.acc_fcoin[1]+self.acc_coinex[1]

        print(self.symbol.upper()+", USDT: ", self.coinNow, self.usdtNow)
        print("coin lost: %.4f, usdt gain: %.4f" %(self.coinNow-self.coinInit, self.usdtNow-self.usdtInit))
        print('\n')



    #**************************************************策略部分**********************************************
    #----flag: 1-buy, 2-sell---------------
    #----由于使用了各类点卡，手续费不会直接作用在交易币种上。所以可以不考虑手续费对币种数量的影响
    #********************************************************************************************************

    #***************多交易所下单函数*********************
    #---------------OKEX------------------
    def trade_okex(self, price, qty, flag):
        symbol_okex = self.symbol + "_usdt"
        if flag==1:
            print("**********buy coin at OKEX!")
            self.acc_okex[0]+=qty
            self.acc_okex[1]-=(price*qty)

            #-----下单买----
            if self.goTrade:
                #print("real trade")
                orderInfo = self.okex.trade(self.symbol_okex,'buy', price, qty)
                orderInfo = json.loads(orderInfo)
                #print(orderInfo)
                if 'error_code' in orderInfo.keys():
                    return [orderInfo['error_code'], 0]      #error code, order ID
                else:
                    return [0, orderInfo['order_id']]

        elif flag==2:
            print("**********sell coin at OKEX!")
            self.acc_okex[0]-=qty
            self.acc_okex[1]+=(price*qty)
            
            #-----下单卖-----
            if self.goTrade:
                #print("real trade")
                orderInfo = self.okex.trade(self.symbol_okex,'sell',price, qty)
                orderInfo = json.loads(orderInfo)
                #print(type(orderInfo))
                if 'error_code' in orderInfo.keys():
                    return [orderInfo['error_code'], 0]      #error code, order ID
                else:
                    return [0, orderInfo['order_id']]

        else:
            print("下单错误okex")
            return [0, 0]

        return [0, 0]

    #---------------HUOBI------------------
    def trade_huobi(self, price, qty, flag):
        if flag==1:
            print("**********buy coin at HUOBI!")            
            self.acc_huobi[0] += qty
            self.acc_huobi[1] -= (price*qty)

            #-----下单买-------
            if self.goTrade:
                #print("real trade")
                orderInfo = self.huobi.sendOrder(str(qty),'', self.symbol_huobi, 'buy-limit', str(price))
                if 'err-code' in orderInfo.keys():
                    return [orderInfo['err-code'], 0]      #error code, order ID
                else:
                    return [0, orderInfo['data']]

        elif flag==2:
            print("**********sell coin at HUOBI!")
            self.acc_huobi[0]-=qty
            self.acc_huobi[1]+=(price*qty)

            #-----下单卖------
            if self.goTrade:
                #print("real trade")
                orderInfo = self.huobi.sendOrder(str(qty),'', self.symbol_huobi, 'sell-limit', str(price))
                if 'err-code' in orderInfo.keys():
                    return [orderInfo['err-code'], 0]      #error code, order ID
                else:
                    return [0, orderInfo['data']]

        else:
            print("下单错误huobi")
            return [0, 0]

        return [0, 0]

    #---------------BINANCE------------------
    def trade_binance(self, price, qty, flag):
        if flag==1:
            print("**********buy coin at BINANCE!")
            self.acc_binance[0]+=qty
            self.acc_binance[1]-=(price*qty)

            #-----下单买-------
            if self.goTrade:
                #print("real trade")
                orderInfo = self.binance.order(self.symbol_binance, 'BUY', qty, price, 'LIMIT')
                if 'code' in orderInfo.keys():
                    return [orderInfo['code'], 0]      #error code, order ID
                else:
                    return [0, orderInfo['orderId']]

        elif flag==2:
            print("**********sell coin at BINANCE!")
            self.acc_binance[0]-=qty
            self.acc_binance[1]+=(price*qty)

            #-----下单卖-------
            if self.goTrade:
                #print("real trade")
                orderInfo = self.binance.order(self.symbol_binance, 'SELL', qty, price, 'LIMIT')
                if 'code' in orderInfo.keys():
                    return [orderInfo['code'], 0]      #error code, order ID
                else:
                    return [0, orderInfo['orderId']]

        else:
            print("下单错误binance")
            return [0, 0]

        return [0, 0]

    #---------------FCOIN------------------
    def trade_fcoin(self, price, qty, flag):
        if flag==1:
            print("**********buy coin at FCOIN!")
            self.acc_fcoin[0]+=qty
            self.acc_fcoin[1]-=(price*qty)            
            
            #-----下单买-----
            if self.goTrade:
                #print("real trade")
                orderInfo = self.fcoin.buy(self.symbol_fcoin, price, qty)
                if orderInfo['status']!=0:
                    return [orderInfo['status'], 0]      #error code, order ID
                else:
                    return [0, orderInfo['data']]

        elif flag==2:
            print("**********sell coin at FCOIN!")
            self.acc_fcoin[0]-=qty
            self.acc_fcoin[1]+=(price*qty)

            #-----下单卖-----
            if self.goTrade:
                #print("real trade")
                orderInfo = self.fcoin.sell(self.symbol_fcoin, price, qty)
                if orderInfo['status']!=0:
                    return [orderInfo['status'], 0]      #error code, order ID
                else:
                    return [0, orderInfo['data']]
            
        else:
            print("下单错误fcoin")
            return [0, 0]

        return [0, 0]

    #---------------COINEX------------------
    def trade_coinex(self, price, qty, flag):
        if flag==1:
            print("**********buy coin at COINEX!")
            self.acc_coinex[0]+=qty
            self.acc_coinex[1]-=(price*qty)

            #-----下单买-----
            if self.goTrade:
                #print("real trade")
                orderInfo = self.coinex.buy_limit(self.symbol_coinex, str(qty), str(price))               
                if orderInfo['code']!=0:
                    return [orderInfo['code'], 0]      #error code, order ID
                else:
                    return [0, orderInfo['data']['id']]
        
        elif flag==2:
            print("**********sell coin at COINEX!")
            self.acc_coinex[0]-=qty
            self.acc_coinex[1]+=(price*qty)

            #-----下单卖-----
            if self.goTrade:
                #print("real trade")
                orderInfo = self.coinex.sell_limit(self.symbol_coinex, str(qty), str(price))               
                if orderInfo['code']!=0:
                    return [orderInfo['code'], 0]      #error code, order ID
                else:
                    return [0, orderInfo['data']['id']]
            
        else:
            print("下单错误coinex")
            return [0, 0]

        return [0, 0]

    

    #***************多交易所查单，撤单函数**********************
    #先只考虑未成交的情况。部分成交的单子暂时放任不管
    #-----------OKEX--------------
    def checkOrder_okex(self, orderID):
        orderInfo = self.okex.orderinfo(self.symbol_okex, orderID)
        orderInfo = json.loads(orderInfo)
        orderStatus = orderInfo['orders'][0]['status']
        reTrade = False

        if orderStatus==0: #未成交，撤单，返回对应信号
            self.okex.cancelOrder('eos_usdt', orderID)
            while 1:                
                time.sleep(self.waitingTime)
                orderInfo = self.okex.orderinfo(self.symbol_okex, orderID)
                orderInfo = json.loads(orderInfo)
                orderStatus = orderInfo['orders'][0]['status']
                if orderStatus == -1 or orderStatus == 3:
                    reTrade = True
                    return reTrade
                elif orderStatus == 2 or orderStatus == 1:
                    reTrade = False
                    return reTrade
                else:
                    print("waiting for recheck order status OKEX")
                    continue
        else:
            return reTrade


    #-----------HUOBI-------------
    def checkOrder_huobi(self, orderID):
        orderInfo = self.huobi.orderInfo(orderID)
        orderStatus = orderInfo['data']['state']
        reTrade = False

        if orderStatus=='submitted': #未成交，撤单，返回对应信号
            self.huobi.cancelOrder(orderID)
            while 1:                
                time.sleep(self.waitingTime)
                orderInfo = self.huobi.orderInfo(orderID)
                orderStatus = orderInfo['data']['state']

                if orderStatus == 'canceled' or orderStatus=='partial-canceled':
                    reTrade = True
                    return reTrade
                elif orderStatus == 'filled' or orderStatus == 'partial-filled':
                    reTrade = False
                    return reTrade
                else:
                    print("waiting for recheck order status HUOBI")
                    continue
        else:
            return reTrade

    #-----------BINANCE-------------
    def checkOrder_binance(self, orderID):
        orderInfo = self.binance.orderStatus(self.symbol_binance, orderId=orderID)
        orderStatus = orderInfo['status']
        reTrade = False

        if orderStatus=='NEW': #未成交，撤单，返回对应信号
            self.binance.cancel(self.symbol_binance, orderId=orderID)
            while 1:                
                time.sleep(self.waitingTime)
                orderInfo = self.binance.orderStatus(self.symbol_binance, orderId=orderID)
                orderStatus = orderInfo['status']
                
                if orderStatus=='CANCELED' or orderStatus=='PENDING_CANCEL' or orderStatus=='REJECTED' or orderStatus=='EXPIRED':
                    reTrade = True
                    return reTrade
                elif orderStatus=='FILLED' or orderStatus=='PARTIALLY_FILLED':
                    reTrade = False
                    return reTrade
                else:
                    print("waiting for recheck order status BINANCE")
                    continue
        else:
            return reTrade

    #-----------FCOIN-------------
    def checkOrder_fcoin(self, orderID):
        orderInfo = self.fcoin.get_order(orderID)
        orderStatus = orderInfo['data']['state']
        reTrade = False

        if orderStatus=='submitted': #未成交，撤单，返回对应信号
            self.fcoin.cancel_order(orderID)
            while 1:                
                time.sleep(self.waitingTime)
                orderInfo = self.fcoin.get_order(orderID)
                orderStatus = orderInfo['data']['state']

                if orderStatus=='canceled' or orderStatus=='partial_canceled' or orderStatus=='pending_cancel':
                    reTrade = True
                    return reTrade
                elif orderStatus=='filled' or orderStatus=='partial_filled':
                    reTrade = False
                    return reTrade
                else:
                    print("waiting for recheck order status FCOIN")
                    continue
        else:
            return reTrade

    #-----------COINEX-------------
    def checkOrder_coinex(self, orderID):
        orderInfo = self.coinex.order_status(orderID, self.symbol_coinex)
        orderStatus = orderInfo['data']['status']
        reTrade = False
        #print(orderStatus)

        if orderStatus=='not_deal': #未成交，撤单，返回对应信号
            orderInfo = self.coinex.cancel_order(orderID, self.symbol_coinex)
            orderStatus = orderInfo['data']['status']
            if orderStatus=='cancel':
                reTrade = True
                return reTrade
            elif orderStatus == 'part_deal' or orderStatus=='done':
                reTrade=False
                return reTrade
            else:
                print("no correct status COINEX", orderStatus)
                return reTrade
        else:
            return reTrade

    #*********************************************
    #核心交易策略函数，包含下单，检查以及补单策略
    #*********************************************
    def start_trade(self, AskExchange, BidExchange, priceASK, priceBID, qty):
        switcher = {
            "okex": self.trade_okex,
            "huobi": self.trade_huobi,
            "binance": self.trade_binance,
            "fcoin": self.trade_fcoin,
            "coinex": self.trade_coinex,
        }
        
        #获取正确的交易数据，获取对应交易所下单函数        
        func_buy = switcher.get(AskExchange, lambda: "nothing")
        func_sell = switcher.get(BidExchange, lambda: "nothing")
        # Execute the function
        buy_price = round(priceASK*self.buyFactor, self.price_precision)
        sell_price = round(priceBID*self.sellFactor, self.price_precision)
        quantity = round(qty, self.Qty_precision)

        #涨跌势判断
        
        #下买卖单
        if AskExchange=='coinex':
            [error_code_buy, orderID_buy] = func_buy(buy_price, quantity, 1)      #以priceASK买入，priceBID卖出
            [error_code_sell, orderID_sell] = func_sell(sell_price, quantity, 2)    #可以使用两个线程来同时下单
        else:            
            [error_code_sell, orderID_sell] = func_sell(sell_price, quantity, 2)    #可以使用两个线程来同时下单
            [error_code_buy, orderID_buy] = func_buy(buy_price, quantity, 1)      #以priceASK买入，priceBID卖出

        failed = 0

        if self.goTrade:
            #检查买卖单是否成功发送
            #若某一个下单有误，重新下单并进入下一阶段。若两者有误，结束。两者无误，进入下一阶段
            if error_code_buy!=0 and error_code_sell!=0:
                failed = 1
                return failed
            elif error_code_buy!=0:   #下单信息错误，尝试再次下单，若不成功，则不重复下单
                print("----resend buy order!----")
                buy_price = round(priceASK*self.rebuyFactor, self.price_precision)
                [error_code_buy, orderID_buy] = func_buy(buy_price, quantity, 1)
                if error_code_buy!=0:
                    failed = 1
                    return failed
            elif error_code_sell!=0:
                print("----resend sell order!----")
                sell_price = round(priceBID*self.resellFactor, self.price_precision)
                [error_code_sell, orderID_sell] = func_sell(sell_price, quantity, 2)
                if error_code_sell!=0:
                    failed = 1
                    return failed
            

            #检查买卖单是否成交
            #若两者均不成交，撤单，返回。两者均成交，返回。一单成交一单不成交，撤单，进入下一阶段。
            time.sleep(self.waitingTime)
            switcher_check = {
                "okex": self.checkOrder_okex,
                "huobi": self.checkOrder_huobi,
                "binance": self.checkOrder_binance,
                "fcoin": self.checkOrder_fcoin,
                "coinex": self.checkOrder_coinex,
            }
            
            #检查下单情况，根据需求撤单        
            func_checkBuy = switcher_check.get(AskExchange, lambda: "nothing")
            func_checkSell = switcher_check.get(BidExchange, lambda: "nothing")
            # Execute the function
            print("check order!", orderID_buy, orderID_sell)
            is_cancelled_buy = func_checkBuy(orderID_buy)
            print("check order!")
            is_cancelled_sell = func_checkSell(orderID_sell)
            print("check order finished!", is_cancelled_buy, is_cancelled_sell)

            #补单
            #针对未成交的单子，砸单补单。        
            if is_cancelled_sell:
                print("----Resell!----")
                sell_price = round(priceBID*self.resellFactor, self.price_precision)
                [error_code_sell, orderID_sell] = func_sell(sell_price, quantity, 2)
                failed = 1

            if is_cancelled_buy:
                print("----Rebuy!----")
                buy_price = round(priceASK*self.rebuyFactor, self.price_precision)
                [error_code_buy, orderID_buy] = func_buy(buy_price, quantity, 1)
                failed = 1

            #结束
            print("finished")
            
        return failed

    #---------------------------------------------------------------------------------------------------------
        

    def checkPrice(self, infoAsk, infoBid): 
        #print("do strategy here!")

        temp = sorted(infoAsk.items(), key=lambda item:item[1][0])
        minASK = temp[0]
        temp = sorted(infoBid.items(), key=lambda item:item[1][0])
        maxBID = temp[-1]

        #---------------获取最优交易所数据-----------------
        #symbol = huobi_result
        #server_time =
        #local_time = 
        
        exchangeASK = minASK[0]
        priceASK = float(minASK[1][0])
        amountASK = float(minASK[1][1])
        commASK = float(minASK[1][2])
        timeASK = int(minASK[1][3])

        exchangeBID = maxBID[0]
        priceBID = float(maxBID[1][0])
        amountBID = float(maxBID[1][1])
        commBID = float(maxBID[1][2])
        timeBID = int(maxBID[1][3])

        #-----------------------------------------------
        diff = (priceBID-priceASK)/priceBID
        #print(diff)
        gain=0

        amount = min(amountASK, amountBID)
        #if exchangeASK=='binance' or exchangeBID=='binance':     #币安最麻烦，下单量不小于10usdt
        if amount*priceBID<12 and self.goTrade:
            #print("amount: ", amount)
            return
        
        isrepeat=0
        if abs(self.lastQty - amount)<self.minimumQty and self.goTrade==False:    # 避免重复统计
            isrepeat=1

        self.lastQty = amount
        amount = min(amount, self.maxQty)

        if self.counter>=self.tradeLimit and self.goTrade:            
            self.goTrade = False

        #-------------价差超过阈值，则开始下单逻辑----------------------
        if(diff>self.priceDiff):
            self.counter+=1
            print("==============%d==============" %(self.counter))
            print("repeat: ", isrepeat)
            gain=0

            #----------计算利润理论值----------------
            if(diff>self.priceDiff and isrepeat==0):
                gain = (priceBID-priceASK)*amount - priceBID*amount*commBID - priceASK*amount*commASK
            if gain>0 and self.goTrade==False:
                self.total_gain += gain
                #x=1

            #*********************检查账户，下单操作*****************************************************************
            #检查本地账户数量，确定是否够
            '''
            res = self.checkAccount()   # 0-not enough
            if res==0:
                print("##########insufficient account balance!##########")
                return
            '''
            
            if isrepeat==0:
                print("------------start real trade!----------")
                failed = self.start_trade(exchangeASK, exchangeBID, priceASK, priceBID, amount)
                print("failed: ", failed)
                self.failed_counter += failed

                if self.goTrade:
                    self.getAccountInfo()
                    gain = self.usdtNow - self.usdtLast - priceBID*amount*commBID - priceASK*amount*commASK
                    self.total_gain += gain
                    self.usdtLast = self.usdtNow
                else:
                    print("************real trade stops!**************")
            #********************************************************************************************************

            #---------同步账户----------------
            #读取所有交易所账户信息，更新本地账户信息

            print("下单失败率: %.2f%%" %(float(self.failed_counter)/float(self.counter)*100.0) )            
            print("存在差价: %f" %(diff))
            print("ask/bid exchange: ", exchangeASK, exchangeBID)
            print("ask/bid price: ", priceASK, priceBID)
            print("Qty: ", amount)
            print("this round gain: ", gain)
            print("total gain: ", self.total_gain)
            print("------account info--------")
            print("okex %s %.2f, USDT: %.2f" %(self.symbol, self.acc_okex[0], self.acc_okex[1]))
            print("huobi %s %.2f, USDT: %.2f" %(self.symbol, self.acc_huobi[0], self.acc_huobi[1]))
            print("binance %s %.2f, USDT: %.2f" %(self.symbol, self.acc_binance[0], self.acc_binance[1]))
            print("fcoin %s %.2f, USDT: %.2f" %(self.symbol, self.acc_fcoin[0], self.acc_fcoin[1]))
            print("coinex %s %.2f, USDT: %.2f" %(self.symbol, self.acc_coinex[0], self.acc_coinex[1]))
            print(self.symbol.upper()+", USDT: ", self.coinNow, self.usdtNow)
            print("\n")
            #---------------------------------------------------

            if self.write_file:
                fout = open("banzhuan.txt","a")
                #本地时刻  交易所bid    bid价  服务器时刻   交易所ask    ask价   服务器时刻   交易数量  价差  当前交易单盈利     总盈利    账户余额 (okex, huobi, binance, fcoin, coinex)
                fout.write("%d %s %.4f %d %s %.4f %d %.4f %.4f %.4f %.4f %.2f %.2f %.2f %.2f %.2f %.2f %.2f %.2f %.2f %.2f\n"
                           %(0, exchangeBID, priceBID, timeBID, exchangeASK, priceASK, timeASK, amount, diff, gain, self.total_gain,
                             self.acc_okex[0], self.acc_okex[1], self.acc_huobi[0], self.acc_huobi[1],
                             self.acc_binance[0], self.acc_binance[1], self.acc_fcoin[0], self.acc_fcoin[1],
                             self.acc_coinex[0], self.acc_coinex[1]))
                fout.close()

            #print("write finished")

        #---------------------------------------------------------------------------------------------------
