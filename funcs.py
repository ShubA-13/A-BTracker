import json
import requests
import sqlite3
import codecs
from main import ConnectionManager

manager = ConnectionManager()


def get_balance_BTC(addr):
    url = "https://blockchain.info/balance?active=" + addr
    response = requests.get(url)
    info = response.json()
    balance = info[addr]["final_balance"]
    return balance


def response_form(coin, addr, balance):
    response = {
        "message": "subscribe",
        "data": [
            {
                "Name": coin,
                "Address": addr,
                "Balance": balance
            }
        ]
    }
    return json.dumps(response)


def updated_balances(coin, addr, balance):
    response = {
        "message": "balance update",
        "data": [
            {
                "Name": coin,
                "Address": addr,
                "Balance": balance
            }
        ]
    }
    return json.dumps(response)


def reform_getting_data(data):
    user_wallet = data.split(' ')[0]
    wallet_to_sub = data.split(' ')[1]
    coin = data.split(' ')[2]
    return user_wallet, wallet_to_sub, coin


def add_user_to_db(user_wallet):
    con = sqlite3.connect('users.db')
    cur = con.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS USERS(addresses);""")
    con.commit()
    if check_user_in_db(user_wallet) == 1:
        cur.execute("INSERT INTO USERS VALUES(?)", (user_wallet,))
        con.commit()


def check_user_in_db(user_wallet):
    flag = 0
    con = sqlite3.connect('users.db')
    cur = con.cursor()
    user = cur.execute("""SELECT * FROM USERS WHERE addresses=?""", (user_wallet,))
    if user.fetchone() is None:
        flag = 1
    return flag


def add_user_sub(user_wallet, addr, coin, balance):
    con = sqlite3.connect('users.db')
    cur = con.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS " + quote_identifier(user_wallet) + " (addresses, coin, balance);")
    con.commit()
    if check_same_users_subs(user_wallet, addr) == 1:
        cur.execute("INSERT INTO " + quote_identifier(user_wallet) + " VALUES(?, ?, ?);", (addr, coin, balance))
        con.commit()


def check_same_users_subs(user_wallet, addr):
    flag = 0
    con = sqlite3.connect('users.db')
    cur = con.cursor()
    address = cur.execute("SELECT * FROM " + quote_identifier(user_wallet) + " WHERE addresses=?", (addr,))
    if address.fetchone() is None:
        flag = 1
    return flag


def quote_identifier(s, errors="strict"):
    encodable = s.encode("utf-8", errors).decode("utf-8")

    nul_index = encodable.find("\x00")

    if nul_index >= 0:
        error = UnicodeEncodeError("NUL-terminated utf-8", encodable,
                                   nul_index, nul_index + 1, "NUL not allowed")
        error_handler = codecs.lookup_error(errors)
        replacement, _ = error_handler(error)
        encodable = encodable.replace("\x00", replacement)

    return "\"" + encodable.replace("\"", "\"\"") + "\""


def get_balance_ETH(addr):
    ETH = 10 ** 18
    url = f"https://api.etherscan.io/api?module=account&action=balance&address={addr}&tag=latest&apikey=YourApiKeyToken"
    response = requests.get(url)
    info = response.json()
    balance = (int(info['result']) / ETH)
    return balance


global new_data
flag_changes = 0


def update_balances(user_wallet):
    con = sqlite3.connect('users.db')
    cur = con.cursor()
    try:
        addresses_eth = cur.execute("SELECT * FROM " + quote_identifier(user_wallet) + " WHERE coin=?", ("ETH",))
        info = addresses_eth.fetchall()
        new_info = []
        for row in info:
            new_balance = get_balance_ETH(row[0])
            if row[2] != new_balance:
                cur.execute("UPDATE " + quote_identifier(user_wallet) + " SET balance=? WHERE addresses=?",
                            (new_balance, row[0]))
                con.commit()
                new_info.append(updated_balances(row[1], row[0], new_balance))
                print("updated balance", updated_balances(row[1], row[0], new_balance))
        flag_changes = signal(new_info)
        if flag_changes == 1:
            return new_info
    except:
        return ('error')
    con.close()


def signal(new_info):
    flag = 0
    if len(new_info) > 0:
        flag = 1
    return flag


def up_reggister(coin: str):
    return coin.upper()


def show_all_subs(user_wallet):
    new_info = update_balances(user_wallet)
    con = sqlite3.connect('users.db')
    cur = con.cursor()
    recs = cur.execute("SELECT * FROM " + quote_identifier(user_wallet))
    subs = recs.fetchall()
    all_subs = []
    for sub in subs:
        all_subs.append(response_form_subs(sub[1], sub[0], sub[2]))
    print(all_subs)
    return all_subs


def response_form_subs(coin, addr, balance):
    response = {
        "message": "your subscription",
        "data": [
            {
                "Name": coin,
                "Address": addr,
                "Balance": balance
            }
        ]
    }
    return json.dumps(response)
