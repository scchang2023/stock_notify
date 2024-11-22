import requests
import pandas as pd
import threading
import inspect
from datetime import datetime

# z	當前盤中成交價
# tv	當前盤中盤成交量
# v	累積成交量
# b	揭示買價(從高到低，以_分隔資料)
# g	揭示買量(配合b，以_分隔資料)
# a	揭示賣價(從低到高，以_分隔資料)
# f	揭示賣量(配合a，以_分隔資料)
# o	開盤價格
# h	最高價格
# l	最低價格
# y	昨日收盤價格
# u	漲停價
# w	跌停價
# tlong	資料更新時間（單位：毫秒）
# d	最近交易日期（YYYYMMDD）
# t	最近成交時刻（HH:MI:SS）
# c	股票代號
# n	公司簡稱
# nf	公司全名
alertConditions = [
    {'ex_ch':'tse_t00.tw',
    'thMin':[[-3, False], [-2, False], [-1, False]], 'thMax':[[3, False], [2, False], [1, False]]},
    {'ex_ch':'tse_00878.tw',
    'thMin':[[-3, False], [-2, False], [-1, False]], 'thMax':[[3, False], [2, False], [1, False]]},
    {'ex_ch':'tse_00881.tw',
    'thMin':[[-3, False], [-2, False], [-1, False]], 'thMax':[[3, False], [2, False], [1, False]]},
    {'ex_ch':'tse_00919.tw',
    'thMin':[[-3, False], [-2, False], [-1, False]], 'thMax':[[3, False], [2, False], [1, False]]},
    {'ex_ch':'tse_00940.tw',
    'thMin':[[-3, False], [-2, False], [-1, False]], 'thMax':[[3, False], [2, False], [1, False]]},
    {'ex_ch':'tse_0056.tw',
    'thMin':[[-3, False], [-2, False], [-1, False]], 'thMax':[[3, False], [2, False], [1, False]]},
    {'ex_ch':'tse_2002.tw',
    'thMin':[[-3, False], [-2, False], [-1, False]], 'thMax':[[3, False], [2, False], [1, False]]},
    {'ex_ch':'tse_2330.tw',
    'thMin':[[-3, False], [-2, False], [-1, False]], 'thMax':[[3, False], [2, False], [1, False]]},
    {'ex_ch':'tse_2884.tw',
    'thMin':[[-3, False], [-2, False], [-1, False]], 'thMax':[[3, False], [2, False], [1, False]]},
    {'ex_ch':'tse_2891.tw',
    'thMin':[[-3, False], [-2, False], [-1, False]], 'thMax':[[3, False], [2, False], [1, False]]}
]

def initAlertConditions(cond:dict)->pd.DataFrame:
    print(f"當前函數名稱是：{inspect.currentframe().f_code.co_name}")
    df = pd.DataFrame(alertConditions)
    if df.empty == True:
        return (False, df)
    for i in range(df.shape[0]):
        thMinLen = len(df.iloc[i]['thMin'])
        for j in range(thMinLen):
            df.iloc[i]['thMin'][j][1] = False
        thMaxLen = len(df.iloc[i]['thMax'])
        for j in range(thMaxLen):
            df.iloc[i]['thMax'][j][1] = False
    return (True, df)

def downloadCurStock(condDF:pd.DataFrame):
    # print(f"當前函數名稱是：{inspect.currentframe().f_code.co_name}")
    url = "https://mis.twse.com.tw/stock/api/getStockInfo.jsp?json=1&delay=0&ex_ch="+\
          "|".join(condDF['ex_ch'].values.tolist())    
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        ret = True
    else:
        ret = False
    return (ret, data)

def getCurSysDateTime():
    # 取得目前日期和時間
    now = datetime.now()
    # 格式化日期和時間
    curDate = now.strftime("%Y-%m-%d")  # 格式化日期為 YYYY-MM-DD
    curTime = now.strftime("%H:%M:%S")  # 格式化時間為 HH:MM:SS
    # 取得星期幾 (# 1 是星期一，7 是星期日)
    weekdayNumISO = now.isoweekday()
    # print(f"自己取得日期時間星期幾: {curDate, curTime, weekdayNumISO}")
    return (curDate, curTime, weekdayNumISO)

def isTradeDatetime(stock:dict)->bool:
    # print(f"當前函數名稱是：{inspect.currentframe().f_code.co_name}")
    sysDate = stock['queryTime']['sysDate']
    sysTime = stock['queryTime']['sysTime']
    if 'd' in stock['msgArray'][0]:
        tradeDate = stock['msgArray'][0]['d']
        print("missing 'd' key:", stock)
    else:
        return False
    # print(f"從 twse 取得的系統日期時間 [{sysDate} {sysTime}]")
    date, time, week = getCurSysDateTime()
    if sysDate == tradeDate and sysTime >= "09:00:00" and sysTime <= "13:30:00"\
        and week >= 1 and week <=5:
        return True
    else:
        return False

def checkStockAlert(cond:pd.DataFrame, stock:pd.DataFrame):
    # print(f"當前函數名稱是：{inspect.currentframe().f_code.co_name}")
    stock = stock[["c","y","z"]].copy()
    # 將目前盤中交易價格z欄位中為'-'字元時，以昨收價格取代
    stock['z'] = stock.apply(lambda row: row['y'] if row['z'] == '-' else row['z'], axis=1)
    for i in range(cond.shape[0]):
        z = stock.iloc[i]['z']
        y = stock.iloc[i]['y']
        if z == '-':
            z = y
        diffPrice = float(z)-float(y)
        diffPercent = diffPrice*100/float(y)
        stock.loc[i, 'diffPrice'] = diffPrice
        stock.loc[i, 'diffPercent'] = diffPercent
        stock.loc[i, 'toAlert'] = False
        if diffPercent<=0:
            length = len(cond.iloc[i]['thMin'])
            for j in range(length):
                if diffPercent <= cond.iloc[i]['thMin'][j][0]:
                    if cond.iloc[i]['thMin'][j][1] == True:
                        break
                    stock.loc[i, 'toAlert'] = True
                    cond.iloc[i]['thMin'][j][1] = True
                    break
        else:
            length = len(cond.iloc[i]['thMax'])
            for j in range(length):
                if diffPercent >= cond.iloc[i]['thMax'][j][0]:
                    if cond.iloc[i]['thMax'][j][1] == True:
                        break
                    stock.loc[i, 'toAlert'] = True
                    cond.iloc[i]['thMax'][j][1] = True
                    break
    return (cond, stock)

def sendLineNotify(msg:str)->requests.Response:
    url = 'https://notify-api.line.me/api/notify'
    # 個人測試
    # token = 'VGZhESCin4DcjD6MPmSiD1rj5yd8YrriQN88HrZEIKy'
    # FISS
    token = 'yqB6couCMQlCtBDJpJb2nEw8yRepyeo8SWjQZJDDsqD'
    headers = {
        'Authorization': 'Bearer ' + token, # 設定權杖
    }
    params = {
        'message': msg # 設定要發送的訊息
    }
    return requests.post(url, headers=headers, params=params) # 使用 post 方法

def sendStockMsg2LineNotify(df:pd.DataFrame):
    print(f"當前函數名稱是：{inspect.currentframe().f_code.co_name}")
    df.loc[:, 'z'] = df['z'].astype(float)
    # print(df)
    # 只保留 toAlert 為 True 的列
    df = df[df['toAlert'] == True]
    # 將有小數的元素，保留至小數點以下2位
    df = df.round(2)
    # 刪除 y 及 toAlert 的欄位
    df = df.drop(columns=['y', 'toAlert'])
    df['diffPrice'] = df['diffPrice'].apply(lambda x: f'漲{x}點' if x >= 0 else f'跌{-x}點')
    df['diffPercent'] = df['diffPercent'].apply(lambda x: f'{x}%' if x >= 0 else f'{-x}%')
    # 更改欄位名稱
    df = df.rename(columns={'c': '股票代號', 'z': '成交', 'diffPrice': '漲跌', 'diffPercent': '幅度'})
    # 將型態 dataframe 轉成型態 string
    msg = df.to_string(index=False, justify='right')
    if df.empty == False:
        print(msg)
        sendLineNotify("\n"+msg)

def sendCondMsg2LineNotify(df:pd.DataFrame):
    print(f"當前函數名稱是：{inspect.currentframe().f_code.co_name}")
    df['ex_ch'] = df['ex_ch'].str.replace('tse_', '').str.replace('.tw', '')  
    def flatten_and_remove_booleans(lst):
        return [value for sublist in lst for value in sublist if not isinstance(value, bool)]
    df['thMin'] = df['thMin'].apply(flatten_and_remove_booleans)
    df['thMax'] = df['thMax'].apply(flatten_and_remove_booleans)
    msg = df.to_string(index=True, justify='right')
    print(msg)
    return sendLineNotify("\n警示條件設定\n"+msg)

def downloadStockTmr(curCondDF):
    # print(f"當前函數名稱是：{inspect.currentframe().f_code.co_name}")
    ret, curStock = downloadCurStock(curCondDF)
    if ret == False:
        print("Failed to downloadCurStock")
        return
    if isTradeDatetime(curStock) == False:
        print("非股市交易時間")
    else:
        curStockMsgArrayDF = pd.DataFrame(curStock['msgArray'])
        condDF, stockDF = checkStockAlert(curCondDF, curStockMsgArrayDF)
        sendStockMsg2LineNotify(stockDF)
        # sendCondMsg2LineNotify(condDF)
    t = threading.Timer(30, downloadStockTmr, args=(curCondDF,))
    t.start()

def main():
    ret, curCondDF = initAlertConditions(alertConditions)
    if ret == False:
        print("Failed to initAlertConditions")
        return
    downloadStockTmr(curCondDF)

if __name__ == "__main__":
    main()
