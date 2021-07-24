from tradingview_ta import *
import asyncio
import threading
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from gspread_formatting import *
from math import ceil
import string
from datetime import datetime
import time as td
import pytz

letters = string.ascii_uppercase

chars = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v',
         'w', 'x', 'y', 'z']

scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets',
         "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]

creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)

client = gspread.authorize(creds)

sheet = client.open("stocks").sheet1

def getValue(vals):
    buy, sell, neutral = vals['BUY'], vals['SELL'], vals['NEUTRAL']
    return ((buy - sell) - (neutral // 5))


Symbols = []
with open('Symbols.txt', 'r') as Sy:
    Symbols = list(Sy.read().split(','))

for s in range(len(Symbols)):
    Symbols[s] = "NASDAQ:"+Symbols[s]
def returnAnalysis(symbols):
    analysis = get_multiple_analysis(screener="america", interval=Interval.INTERVAL_1_WEEK, symbols=symbols)
    symbolsKV = []
    for k, v in analysis.items():
        symbolsKV.append((k, getValue(v.summary), v.indicators["close"]))
    symbolsKV.sort(key=lambda x: x[1], reverse=True)
    return symbolsKV

def SymbolVals():
    SymbolsAndValues = []
    for symbol in Symbols:
        try:
            SymbolsAndValues.append([symbol, asyncio.run(getValue(symbol))])
        except:
            pass
    SymbolsAndValues.sort(key=lambda x: x[1], reverse=True)
    return SymbolsAndValues

# pprint(data)

# sheet.update("a1", "Test Date")

# format_cell_range(sheet, 'A1:J1', fmt)
# set_column_width(sheet, "D", 20)

# .cell(row, col).value outputs string
# .row_values(num) & .col_values(num) outputs list of strings


def find_row_end(end_num):
    set_num = ceil(end_num/26)
    location = end_num - ((set_num - 1) * 26)
    letter = letters[location-1]
    return set_num, letter

def is_empty(location, typ):
    if typ == "CEL":
        val = sheet.cell(location[0], location[1]).value
        if val == '' or val == None:
            return True
        else:
            return False
    elif typ == "COL":
        val = sheet.col_values(location)
        if not val:
            return True
        else:
            return False
    elif typ == "ROW":
        val = sheet.row_values(location)
        if not val:
            return True
        else:
            return False
    else:
        return "You entered a type that was invalid, please enter type as either \"CELL\", \"COL\", or \"ROW\"."


def update_col(col, content):
    final_list = []
    end_point = len(content) + 1
    update_range = "{0}1:{0}{1}".format(col, end_point)
    for i in content:
        single_list = [i]
        final_list.append(single_list)
    sheet.update(update_range, final_list)

def update_row(row, content):
    end_point = len(content) + 1
    end_num, end_letter = find_row_end(end_point-1)
    set_letter = letters[end_num - 2]
    update_range = "A{1}:{2}{0}{1}".format(end_letter, row, set_letter)
    if sheet.col_count >= len(content):
        sheet.update(update_range, [content])
    else:
        add_amount = len(content) - sheet.col_count
        sheet.add_cols(add_amount)


def setup_input():
    row = 1
    col = 1
    while not is_empty((row, col), "CEL"):
        col += 1
    sheet.update_cell(row, col, "Current Row:")
    sheet.update_cell(row, col+1, 2)


def input_data(data):
    storage_col = sheet.find("Current Row:").col + 1
    cr = int(sheet.cell(1, storage_col).value)
    while not is_empty(cr, "ROW"):
        cr1 = cr + 1
        sheet.update_cell(1, storage_col, cr1)
        cr = int(sheet.cell(1, storage_col).value)
    update_row(cr, data)
    sheet.update_cell(1,storage_col,int(sheet.cell(1, storage_col).value) + 1)

# cols (int) – Number of new columns to add
setattr(sheet, "setup", setup_input)
setattr(sheet, "input_data", input_data)
setattr(sheet, "update_row", update_row)


utc_now = pytz.utc.localize(datetime.utcnow())
mst_now = utc_now.astimezone(pytz.timezone("America/Denver"))
timeV = str(mst_now.time())[0:5]
input = []
date = str(mst_now.date())
input.append(str(date) + " " + timeV)

def test1(KV):
    if not is_empty((2,3), "CEL"):
        sellAmmount = float(sheet.cell(2,3).value)
        sellSymb = sheet.cell(2,2).value
        sKV = returnAnalysis([sellSymb])
        newBal = sellAmmount*sKV[0][2]
        sheet.update_cell(2, 4, newBal)
    maxKV = KV[0]
    maxSymb = maxKV[0]
    maxVal = maxKV[2]
    curBal = int(sheet.cell(2,4).value)
    ammount = curBal/maxVal
    sheet.update_cell(2, 2, maxSymb)
    sheet.update_cell(2, 3, ammount)

def test2(KV):
    if not is_empty((3,3), "CEL"):
        sellAmmount = list(map(float, sheet.cell(3, 3).value[1:-1].replace(" ", "").split(",")))
        sellSymb = sheet.cell(3, 2).value[1:-1].replace(" ", "").replace("'", "").split(",")
        sKV = returnAnalysis(sellSymb)
        newBal = 0
        for i in range(len(sKV)):
            newBal += sellAmmount[i]*sKV[i][2]
        sheet.update_cell(3, 4, newBal)
    threeSymb = [KV[0][0], KV[1][0], KV[2][0]]
    threeScr = [KV[0][1], KV[1][1], KV[2][1]]
    threeVal = [KV[0][2], KV[1][2], KV[2][2]]
    curBal = float(sheet.cell(3,4).value)
    sum3 = sum(threeScr)
    weightBal = [threeScr[0]/sum3*curBal, threeScr[1]/sum3*curBal, threeScr[2]/sum3*curBal]
    amountList = []
    for i in range(len(threeVal)):
        amountList.append(weightBal[i]/threeVal[i])
    sheet.update_cell(3, 2, str(threeSymb))
    sheet.update_cell(3, 3, str(amountList))

kv = returnAnalysis(Symbols)
test1(kv)
test2(kv)