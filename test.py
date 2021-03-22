from binance.BinanceSpotAPI import BinanceSpot
binanceSpot = BinanceSpot("https://api.binance.com", "", "")

b=binanceSpot.exchangeInfo()


class xxx:
    def zero(self, x):
        return x

    def one(self, x):
        return x

    def numbers_to_functions_to_strings(self, argument, n):
        switcher = {
            0: self.zero,
            1: self.one,
            2: lambda: "two",
        }
        # Get the function from switcher dictionary
        func = switcher.get(argument, lambda: "nothing")
        # Execute the function
        return func(n)

x=xxx()
a=x.numbers_to_functions_to_strings(0, 'ttt')
print(a)
