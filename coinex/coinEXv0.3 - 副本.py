#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Created by bu on 2018-01-17
"""
from __future__ import unicode_literals
import time
import hashlib
import json as complex_json
import urllib3
from urllib3.exceptions import InsecureRequestWarning

urllib3.disable_warnings(InsecureRequestWarning)
http = urllib3.PoolManager(timeout=urllib3.Timeout(connect=1, read=2))

#-----------------trade parameters-----------------
trade_pair = 'BTCUSDT'
amount = 0.04
price_precision = 2
amount_precision = 6
buy_modifier = 1.0001
sell_modifier = 0.9999
time_to_record_balance_account = '22'
oscillation3 = 0.0004
price_step = []
untrade_id = []
comission_cost = 0  # by xiao
CP_price = 100
#-------------------------------------------------


class RequestClient(object):
    __headers = {
        'Content-Type': 'application/json; charset=utf-8',
        'Accept': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36'
    }

    def __init__(self, headers={}):
        self.access_id = '3320BC86A9444FB9A83103A429B4F259'      # replace
        self.secret_key = 'F1ACD4CBBA494913AB6D44D672B270DEE773EEE8CCA59CB4'     # replace
        self.url = 'https://api.coinex.com'
        self.headers = self.__headers
        self.headers.update(headers)

    @staticmethod
    def get_sign(params, secret_key):
        sort_params = sorted(params)
        data = []
        for item in sort_params:
            data.append(item + '=' + str(params[item]))
        str_params = "{0}&secret_key={1}".format('&'.join(data), secret_key)
        #str_params.encode('utf-8')
        token = hashlib.md5(str_params).hexdigest().upper()
        return token

    def set_authorization(self, params):
        params['access_id'] = self.access_id
        params['tonce'] = int(time.time()*1000)
        self.headers['AUTHORIZATION'] = self.get_sign(params, self.secret_key)

    def request(self, method, url, params={}, data='', json={}):
        method = method.upper()
        if method in ['GET', 'DELETE']:
            self.set_authorization(params)
            result = http.request(method, url, fields=params, headers=self.headers)
        else:
            if data:
                json.update(complex_json.loads(data))
            self.set_authorization(json)
            encoded_data = complex_json.dumps(json).encode('utf-8')
            result = http.request(method, url, body=encoded_data, headers=self.headers)
        return result

request_client = RequestClient()

def get_depth():
    global request_client
    params = {
        'market': trade_pair,
        'limit': 5,
        'merge': 0
    }
    print('start!')
    response = request_client.request('GET', '{url}/v1/market/depth'.format(url=request_client.url), params=params)
    print('end!')
    json_string = response.data
    return complex_json.loads(json_string)

# by xiao
def get_depth_CP():
    global request_client
    params = {
        'market': 'CPUSDT',
        'limit': 5,
        'merge': 0
    }
    response = request_client.request('GET', '{url}/v1/market/depth'.format(url=request_client.url), params=params)
    json_string = response.data
    return complex_json.loads(json_string)

def get_account():
    global request_client
    response = request_client.request('GET', '{url}/v1/balance/'.format(url=request_client.url))
    json_string = response.data
    return complex_json.loads(json_string)

def mining_difficulty():
    global request_client
    response = request_client.request('GET', '{url}/v1/order/mining/difficulty'.format(url=request_client.url))
    json_string = response.data
    return complex_json.loads(json_string)

def order_pending(market_type):
    global request_client
    params = {
        'market': market_type
    }
    response = request_client.request(
            'GET',
            '{url}/v1/order/pending'.format(url=request_client.url),
            params=params
    )
    print(response.content)


def order_finished(market_type, page, limit):
    global request_client
    params = {
        'market': market_type,
        'page': page,
        'limit': limit
    }
    response = request_client.request(
            'GET',
            '{url}/v1/order/finished'.format(url=request_client.url),
            params=params
    )
    print(response.status)


def buy_limit(amount, price):
    global request_client
    data = {
            "amount": amount,
            "price": price,
            "type": "buy",
            "market": trade_pair
        }

    response = request_client.request(
            'POST',
            '{url}/v1/order/limit'.format(url=request_client.url),
            json=data,
    )
    json_string = response.data
    return complex_json.loads(json_string)
    #return response.data

def sell_limit(amount, price):
    global request_client
    data = {
            "amount": amount,
            "price": price,
            "type": "sell",
            "market": trade_pair
        }

    response = request_client.request(
            'POST',
            '{url}/v1/order/limit'.format(url=request_client.url),
            json=data,
    )
    json_string = response.data
    return complex_json.loads(json_string)
'''
def put_market(quantities):
    global request_client
    data = {
            "amount": quantities,
            "type": "sell",
            "market": "CETUSDT"
        }

    response = request_client.request(
            'POST',
            '{url}/v1/order/market'.format(url=request_client.url),
            json=data,
    )
    return(response.content)
'''
def put_market(trade_paire,trade_type,quantities):
    global request_client
    data = {
            "amount": quantities,
            "type": trade_type,
            "market": trade_paire
        }

    response = request_client.request(
            'POST',
            '{url}/v1/order/market'.format(url=request_client.url),
            json=data,
    )
    return(response.data)

def cancel_order(id, market):
    global request_client
    data = {
        "id": id,
        "market": market,
    }
    print(market)

    response = request_client.request(
            'DELETE',
            '{url}/v1/order/pending'.format(url=request_client.url),
            params=data,
    )
    return(response.data)


def getMidPrice():
    res = get_depth()
    pricebid = float(res['data']['bids'][0][0])
    priceask = float(res['data']['asks'][0][0])
    print(pricebid, priceask)
    return (pricebid+priceask)/2

# by xiao
def getCPPrice():
    res = get_depth_CP()
    pricebid = float(res['data']['bids'][0][0])
    priceask = float(res['data']['asks'][0][0])
    print(pricebid, priceask)
    return (pricebid+priceask)/2

'''
def getAvailableCetAndSell():
    res = get_account()
    if res != 'None':
        sellQuantities = float(res['data']['CET']['available'])
        if sellQuantities > 10:
            print("sell CET")
            order_sell = put_market(str(sellQuantities))
            print(order_sell)
'''
def getAvailableCetAndSell():
    res = get_account()
    if res != 'None':
        sellQuantities = float(res['data']['CET']['available'])

        # by xiao
        difficulty = 493
        result = mining_difficulty()
        if result != 'None':
            difficulty = float(result['data']['difficulty'])            
        sellQuantities = min(sellQuantities, difficulty)
        
        if sellQuantities > 10:
            print("sell CET")
            order_sell = put_market("CETUSDT","sell",str(sellQuantities))
            print(order_sell)
#---------------------------------------------------------------------
#res = mining_difficulty()
#print(res)


while 1:
    try:

        print(get_depth())

        ##### check for available CET and sell CET in market price for each hour
        current_time = time.strftime('%Y-%m-%d:%H-%M-%S',time.localtime(time.time()))
        current_hour = time.strftime('%H',time.localtime(time.time()))
        #print(current_hour)
        if current_hour!= time_to_record_balance_account:
            print("check and sell CET")
            getAvailableCetAndSell()
            time_to_record_balance_account=current_hour
            comission_cost = 0  # by xiao

        ########## checke diffculty and mined situation#############
        res = mining_difficulty()
        if res != 'None':
            difficulty = float(res['data']['difficulty'])
            prediction = float(res['data']['prediction'])
            print ("Mining difficulty is %f and already mined is %f"%(difficulty,prediction))

            # by xiao
            try:
                CP_price = getCPPrice()
            except:
                print("get cp price error!")
                
            if prediction > 0.8*difficulty or comission_cost/CP_price > 0.95*difficulty:  # by xiao
                continue
            
        #######################
        midPrice = getMidPrice()
        buyPrice = round(midPrice*buy_modifier, price_precision)
        sellPrice = round(midPrice*sell_modifier, price_precision)       
        print("trade buy-sell price: %f, %f" %(buyPrice, sellPrice))

        if len(price_step) <= 30 :
            time.sleep(1)
            price_step.append(midPrice)
            continue
        else :
            price_step.pop(0)
            price_step.append(midPrice)
       

        diff= max(abs((max(price_step)-price_step[30])/price_step[30]),abs((min(price_step)-price_step[30])/price_step[30]))
        print("**********diff is %f*********", diff)
        
        if diff < oscillation3:
            #### CHECK BALANCE, GET AVAILABLE BTC AND USDT
            
            res = get_account()
            if res != 'None':
                SELLQuantitiesBTC = float(res['data']['BTC']['available'])
                BUYQuantitiesUSDT = float(res['data']['USDT']['available'])
                amount_min = min (SELLQuantitiesBTC,BUYQuantitiesUSDT/buyPrice)
                print ("usd has %f and bitcoin has %f"%(BUYQuantitiesUSDT,SELLQuantitiesBTC))
                ####### balance account ########
                if BUYQuantitiesUSDT > 2*SELLQuantitiesBTC*midPrice:
                    print("BALANCE ACCOUNT BUY BITCOIN")
                    buy_quantities = round(float(BUYQuantitiesUSDT)/4/midPrice,amount_precision)
                    order_buy = buy_limit(str(buy_quantities), str(buyPrice))
                    untrade_id.append(order_buy['data']['id'])
                    continue
                    #print(order_sell)
                if 2*BUYQuantitiesUSDT < SELLQuantitiesBTC*midPrice:
                    print("BALANCE ACCOUNT SELL BITCOIN")
                    sell_quantities = round(float(SELLQuantitiesBTC)/4,amount_precision)
                    order_sell = put_market("BTCUSDT","sell",str(sell_quantities))
                    continue
                if amount_min<amount:
                    print("reduce trading amount")
                    amount = round(0.8*amount_min,amount_precision)
            
            order_buy = buy_limit(str(amount), str(buyPrice))
            order_sell = sell_limit(str(amount), str(sellPrice))
            print("buy id is %d"%order_buy['data']['id'])
            print("sell id is %d"%order_sell['data']['id'])
            time.sleep(2)
            
            if order_buy['data']['status'] != "done":
                print ("append untraded buy oder")
                untrade_id.append(order_buy['data']['id'])
            else:
                comission_cost = comission_cost + buyPrice*amount*0.001   # by xiao
                
            if order_sell['data']['status'] != "done":
                print ("append untraded sell oder")
                untrade_id.append(order_sell['data']['id'])
            else:
                comission_cost = comission_cost + sellPrice*amount*0.001   # by xiao
            
            #print(order_sell)
            time.sleep(2)
        else:
            time.sleep(3)
            size= len(untrade_id)
            for i in range(0,size):
                cancel_order(untrade_id[0],trade_pair)
                untrade_id.pop(0)
                time.sleep(1)


            

    except:
        print("########error!#############")
        time.sleep(2)
