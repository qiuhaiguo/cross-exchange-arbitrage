import hmac
import hashlib
import logging
import requests
import time
from urllib.parse import urlencode


LIMIT = "LIMIT"
MARKET = "MARKET"

GTC = "GTC"
IOC = "IOC"

#options = {}

class BinanceSpot: 
    def __init__ (self,url,apikey,secretkey):
        self.__url = url
        self.__apikey = apikey
        self.__secretkey = secretkey

    #def set(apiKey, secret):
    #"""Set API key and secret.

    #Must be called before any making any signed API calls.
    #"""
    #options["apiKey"] = apiKey
    #options["secret"] = secret

    def getServerTime(self):
        """Get exchange info."""
        data = self.request("GET", "/api/v1/time")
        return data

    def exchangeInfo(self):
        """Get exchange info."""
        data = self.request("GET", "/api/v1/exchangeInfo")
        return data


    def prices(self):
        """Get latest prices for all symbols."""
        data = self.request("GET", "/api/v1/ticker/allPrices")
        return data

    def get_ticker(self, symbol):
        params = {"symbol": symbol}
        data = self.request("GET", "/api/v3/ticker/bookTicker", params)
        return data


    def tickers(self):
        """Get best price/qty on the order book for all symbols."""
        data = self.request("GET", "/api/v1/ticker/allBookTickers")
        return data


    def depth(self,symbol= '', **kwargs):
        """Get order book.

        Args:
            symbol (str)
            limit (int, optional): Default 100. Must be one of 50, 20, 100, 500, 5,
                200, 10.

        """
        params = {"symbol": symbol}
        params.update(kwargs)
        data = self.request("GET", "/api/v1/depth", params)
        #return {
           # "bids": {px: qty for px, qty, _ in data["bids"]},
           # "asks": {px: qty for px, qty, _ in data["asks"]},
        #}
        return data


    def klines(self,symbol='', interval='', **kwargs):
        """Get kline/candlestick bars for a symbol.

        Klines are uniquely identified by their open time. If startTime and endTime
        are not sent, the most recent klines are returned.

        Args:
            symbol (str)
            interval (str)
            limit (int, optional): Default 500; max 500.
            startTime (int, optional)
            endTime (int, optional)

        """
        params = {"symbol": symbol, "interval": interval}
        params.update(kwargs)
        data = self.request("GET", "/api/v1/klines", params)
        return [{
            "openTime": d[0],
            "open": d[1],
            "high": d[2],
            "low": d[3],
            "close": d[4],
            "volume": d[5],
            "closeTime": d[6],
            "quoteVolume": d[7],
            "numTrades": d[8],
        } for d in data]


    def balances(self):
        """Get current balances for all symbols."""
        params={}
        params['recvWindow'] = 8000
        data = self.signedRequest("GET", "/api/v3/account", params)
        #print(data)
        if 'msg' in data:
            raise ValueError("Error from exchange: {}".format(data['msg']))

        #return {d["asset"]: {
            #"free": d["free"],
            #"locked": d["locked"],
        #} for d in data.get("balances", [])}
        return data


    def order(self,symbol='', side='', quantity='', price='', orderType=LIMIT, timeInForce=GTC,
            test=False, **kwargs):
        """Send in a new order.

        Args:
            symbol (str)
            side (str): BUY or SELL.
            quantity (float, str or decimal)
            price (float, str or decimal)
            orderType (str, optional): LIMIT or MARKET.
            timeInForce (str, optional): GTC or IOC.
            test (bool, optional): Creates and validates a new order but does not
                send it into the matching engine. Returns an empty dict if
                successful.
            newClientOrderId (str, optional): A unique id for the order.
                Automatically generated if not sent.
            stopPrice (float, str or decimal, optional): Used with stop orders.
            icebergQty (float, str or decimal, optional): Used with iceberg orders.

        """
        params = {
            "symbol": symbol,
            "side": side,
            "type": orderType,
            "timeInForce": timeInForce,
            "quantity": quantity,
            "price": price,
        }
        
        params['recvWindow'] = 8000
        
        params.update(kwargs)
        path = "/api/v3/order/test" if test else "/api/v3/order"
        data = self.signedRequest("POST", path, params)
        return data


    def orderStatus(self,symbol='', **kwargs):
        """Check an order's status.

        Args:
            symbol (str)
            orderId (int, optional)
            origClientOrderId (str, optional)
            recvWindow (int, optional)

        """
        params = {"symbol": symbol}
        params.update(kwargs)
        data = self.signedRequest("GET", "/api/v3/order", params)
        return data


    def cancel(self,symbol='', **kwargs):
        """Cancel an active order.

        Args:
            symbol (str)
            orderId (int, optional)
            origClientOrderId (str, optional)
            newClientOrderId (str, optional): Used to uniquely identify this
                cancel. Automatically generated by default.
            recvWindow (int, optional)

        """
        params = {"symbol": symbol}
        params.update(kwargs)
        data = self.signedRequest("DELETE", "/api/v3/order", params)
        return data


    def openOrders(self,symbol='', **kwargs):
        """Get all open orders on a symbol.

        Args:
            symbol (str)
            recvWindow (int, optional)

        """
        params = {"symbol": symbol}
        params.update(kwargs)
        data = self.signedRequest("GET", "/api/v3/openOrders", params)
        return data


    def allOrders(self,symbol='', **kwargs):
        """Get all account orders; active, canceled, or filled.

        If orderId is set, it will get orders >= that orderId. Otherwise most
        recent orders are returned.

        Args:
            symbol (str)
            orderId (int, optional)
            limit (int, optional): Default 500; max 500.
            recvWindow (int, optional)

        """
        params = {"symbol": symbol}
        params.update(kwargs)
        data = self.signedRequest("GET", "/api/v3/allOrders", params)
        return data


    def myTrades(self,symbol='', **kwargs):
        """Get trades for a specific account and symbol.

        Args:
            symbol (str)
            limit (int, optional): Default 500; max 500.
            fromId (int, optional): TradeId to fetch from. Default gets most recent
                trades.
            recvWindow (int, optional)

        """
        params = {"symbol": symbol}
        params.update(kwargs)
        data = self.signedRequest("GET", "/api/v3/myTrades", params)
        return data


    def request(self,method='', path='', params=None):
        resp = requests.request(method, self.__url + path, params=params)
        data = resp.json()
        if "msg" in data:
            logging.error(data['msg'])
        return data


    def signedRequest(self,method='', path='', params=''):
        #if "apiKey" not in options or "secret" not in options:
            #raise ValueError("Api key and secret must be set")

        query = urlencode(sorted(params.items()))
        query += "&timestamp={}".format(int(time.time() * 1000))
        secret = bytes(self.__secretkey.encode("utf-8"))
        signature = hmac.new(secret, query.encode("utf-8"),
                                hashlib.sha256).hexdigest()
        query += "&signature={}".format(signature)
        resp = requests.request(method,
                                self.__url + path + "?" + query,
                                headers={"X-MBX-APIKEY": self.__apikey})

        data = resp.json()
        if "msg" in data:
            logging.error(data['msg'])
        return data


    def formatNumber(x):
        if isinstance(x, float):
            return "{:.8f}".format(x)
        else:
            return str(x)
