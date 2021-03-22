#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Created by bu on 2018-01-17
"""
from __future__ import unicode_literals
import time
import hashlib
import json as complex_json
#import urllib3
#from urllib3.exceptions import InsecureRequestWarning

import requests

#urllib3.disable_warnings(InsecureRequestWarning)
#http = urllib3.PoolManager(timeout=urllib3.Timeout(connect=1, read=2))

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


class CoinEX(object):
    __headers = {
        'Content-Type': 'application/json; charset=utf-8',
        'Accept': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36'
    }

    def __init__(self, apikey, seckey, headers={}):
        self.access_id = apikey      
        self.secret_key = seckey
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
        token = hashlib.md5(str_params.encode('utf8')).hexdigest().upper()
        return token

    def set_authorization(self, params):
        params['access_id'] = self.access_id
        params['tonce'] = int(time.time()*1000)
        self.headers['AUTHORIZATION'] = self.get_sign(params, self.secret_key)

    def request(self, method, url, params={}, data='', json={}):
        method = method.upper()
        if method in ['GET', 'DELETE']:
            self.set_authorization(params)
            #print(params)
            #result = http.request(method, url, fields=params, headers=self.headers)
            result = requests.request(method, url, params=params, headers=self.headers)
        else:
            if data:
                json.update(complex_json.loads(data))
            self.set_authorization(json)
            #params = complex_json.dumps(json).encode('utf-8')
            #print(params)
            #result = http.request(method, url, body=encoded_data, headers=self.headers)
            result = requests.request(method, url, headers=self.headers, json=json)
        return result

    #-----------------------------------
    def get_depth(self, symbol, depth):
        params = {
            'market': symbol,
            'limit': depth,
            'merge': 0
        }
        response = self.request('GET', '{url}/v1/market/depth'.format(url=self.url), params=params)
        if response.status_code == 200:
            try:
                result = response.json()
                return result
            except:
                return ""
        else:
            print("coinex get depth received error data!")
            return response.status_code

        #json_string = response.data
        #return complex_json.loads(json_string)

    def buy_limit(self, symbol, amount, price):
        data = {
                "amount": amount,
                "price": price,
                "type": "buy",
                "market": symbol
            }
        response = self.request(
                'POST',
                '{url}/v1/order/limit'.format(url=self.url),
                json=data,
        )
        if response.status_code == 200:
            try:
                result = response.json()
                return result
            except:
                return ""
        else:
            print("coinex buy limit error!")
            return response.status_code
        

    def sell_limit(self, symbol, amount, price):
        data = {
                "amount": amount,
                "price": price,
                "type": "sell",
                "market": symbol
            }
        response = self.request(
                'POST',
                '{url}/v1/order/limit'.format(url=self.url),
                json=data,
        )
        if response.status_code == 200:
            try:
                result = response.json()
                return result
            except:
                return ""
        else:
            print("coinex sell limit error!")
            return response.status_code

    def get_account(self):
        response = self.request('GET', '{url}/v1/balance/'.format(url=self.url))
        if response.status_code == 200:
            try:
                result = response.json()
                return result
            except:
                return ""
        else:
            print("coinex get balance error!")
            return response.status_code

        #json_string = response.data
        #return complex_json.loads(json_string)

    def getTicker(self, symbol):
        params = {
            'market': symbol,
        }
        response = self.request('GET', '{url}/v1/market/ticker'.format(url=self.url), params=params)
        if response.status_code == 200:
            try:
                result = response.json()
                return result
            except:
                return ""
        else:
            print("coinex get depth received error data!")
            return response.status_code

    def order_status(self, orderid, symbol):
        params = {
            "id": orderid,
            "market": symbol,
        }
        #print(market)

        response = self.request('GET', '{url}/v1/order/status'.format(url=self.url), params=params)
        if response.status_code == 200:
            try:
                result = response.json()
                return result
            except:
                return ""
        else:
            print("coinex get order status error!")
            return response.status_code
        #return(response.data)


    def cancel_order(self, orderid, symbol):
        params = {
            "id": orderid,
            "market": symbol,
        }
        #print(market)

        response = self.request('DELETE', '{url}/v1/order/pending'.format(url=self.url), params=params)
        if response.status_code == 200:
            try:
                result = response.json()
                return result
            except:
                return ""
        else:
            print("coinex cancel order error!")
            return response.status_code
        #return(response.data)
        


    #------------------------------------------------------------


    

    def mining_difficulty(self):
        response = self.request('GET', '{url}/v1/order/mining/difficulty'.format(url=self.url))
        json_string = response.data
        return complex_json.loads(json_string)

    def order_pending(self, market_type):
        params = {
            'market': market_type
        }
        response = self.request(
                'GET',
                '{url}/v1/order/pending'.format(url=self.url),
                params=params
        )
        print(response.content)


    def order_finished(self, market_type, page, limit):
        params = {
            'market': market_type,
            'page': page,
            'limit': limit
        }
        response = self.request(
                'GET',
                '{url}/v1/order/finished'.format(url=self.url),
                params=params
        )
        print(response.status)


    
  
    def put_market(self, trade_paire,trade_type,quantities):
        data = {
                "amount": quantities,
                "type": trade_type,
                "market": trade_paire
            }

        response = self.request(
                'POST',
                '{url}/v1/order/market'.format(url=self.url),
                json=data,
        )
        return(response.data)

    

#---------------------------------------------------------------------

