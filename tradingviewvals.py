from tradingview_ta import TA_Handler, Interval
import asyncio
import threading

handler = TA_Handler()
handler.set_interval_as(Interval.INTERVAL_1_WEEK)
handler.set_exchange_as_crypto_or_stock("NASDAQ")
handler.set_screener_as_stock("america")

async def getValue(symbol):
    handler.set_symbol_as(symbol)
    vals = handler.get_analysis().summary
    buy, sell, neutral = vals['BUY'], vals['SELL'], vals['NEUTRAL']
    return((buy-sell)-(neutral//5))

Symbols = []
with open('Symbols.txt', 'r') as Sy:
    Symbols = list(Sy.read().split(','))


def SymbolVals():
    SymbolsAndValues = []
    for symbol in Symbols:
        try:
            SymbolsAndValues.append([symbol, asyncio.run(getValue(symbol))])
        except:
            pass
    SymbolsAndValues.sort(key=lambda x:x[1], reverse = True)
    return SymbolsAndValues




