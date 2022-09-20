import sqlite3
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import os
import funcs
from typing import List
import uvicorn
import asyncio

app = FastAPI()

html = """
<!DOCTYPE html>
<html>
    <head>
        <title>WalletTracker</title>
    </head>
    <body>
        <h1>Wallet Tracker</h1>
        <form action="" onsubmit="sendMessage(event)">
            <label>Your wallet</label>
            <input type="text" id="messageText1" autocomplete="off"/><br><br>
            <label>Wallet to subscribe</label>
            <input type="text" id="messageText2" autocomplete="off"/><br><br>
            <label1>Coin</label1>
            <input type="text" id="messageText3" autocomplete="off"/><br><br>
            <button>Send</button>
        </form>
        <ul id='messages'>
        </ul>
        <script>
            var ws = new WebSocket("ws://localhost:8000/ws");
            ws.onmessage = function(event) {
                var messages = document.getElementById('messages')
                var message = document.createElement('li')
                var content = document.createTextNode(event.data)
                message.appendChild(content)
                messages.appendChild(message)
            };
            function sendMessage(event) {
                var input1 = document.getElementById("messageText1")
                var input2 = document.getElementById("messageText2")
                var input3 = document.getElementById("messageText3")
                ws.send(input1.value+" "+input2.value+" "+input3.value)
                input1.value = ''
                input2.value = ''
                input3.value = ''
                event.preventDefault()
            }
        </script>
    </body>
</html>
"""


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_messages(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def send_personal_updates(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)


manager = ConnectionManager()


@app.get("/")
async def get():
    return HTMLResponse(html)


d = {}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            user_wallet, addr, coin = funcs.reform_getting_data(data)
            print(user_wallet, addr, coin)
            d[user_wallet] = websocket
            print(d)
            funcs.add_user_to_db(user_wallet)
            balance = funcs.get_balance_ETH(addr)
            funcs.add_user_sub(user_wallet, addr, coin, balance)
            response = funcs.response_form(coin, addr, balance)
            print(response)
            await manager.send_personal_messages(response, websocket)
            while True:
                send_info = funcs.update_balances(user_wallet)
                if send_info != 'error' and send_info != None:
                    # await manager.send_personal_messages("Updated balances", websocket)
                    for msg in send_info:
                        await manager.send_personal_messages(msg, websocket)
                    await asyncio.sleep(120)
    except WebSocketDisconnect:
        k = funcs.get_key(d, websocket)
        del d[k]
        manager.disconnect(websocket)


@app.get('/show_subs/{user_wallet}')
async def get_subs(user_wallet):
    con = sqlite3.connect('users.db')
    cur = con.cursor()
    try:
        sql_select_query = "SELECT * FROM " + funcs.quote_identifier(user_wallet)
        cur.execute(sql_select_query)
        recs = cur.fetchall()
        data = []
        for row in recs:
            data.append(funcs.response_form(row[1], row[0], row[2]))
        return data
    except:
        return ('You havn`t got any subscribes')


# 1Q1s8gGKB1hAbUVc4UTyedLHH9dSs99X9W btc
# 0xeBec795c9c8bBD61FFc14A6662944748F299cAcf eth


if __name__ == '__main__':
    if not os.path.isfile('users.db'):
        file = open('users.db', 'w')
        file.close()

    uvicorn.run('main:app', port=8000, log_level='info')
