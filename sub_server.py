import websockets
import asyncio
import funcs

PORT = 5000

print("Started server and its listening on Port " + str(PORT))

connected = {}


async def echo(websocket):
    print("A client just connected")
    connected[websocket] = None
    while True:
        try:
            message = await websocket.recv()
            print("Received message from client: " + message)
            user_wallet, addr, coin_g = funcs.reform_getting_data(message)
            connected[websocket] = user_wallet
            print(connected)
            if len(addr) != 0:
                funcs.add_user_to_db(user_wallet)
                coin = funcs.up_reggister(coin_g)
                balance = funcs.get_balance_ETH(addr)
                response = funcs.response_form(coin, addr, balance)
                funcs.add_user_sub(user_wallet, addr, coin, balance)
                if funcs.check_same_users_subs(user_wallet, addr) == 1:
                    await websocket.send("You have subscribed to: " + response)
                else:
                    await websocket.send("You have already subscribed to: " + response)

                while True:
                    send_info = funcs.update_balances(user_wallet)
                    if send_info != 'error' and send_info != None:
                        for msg in send_info:
                            await websocket.send(msg)
                        await asyncio.sleep(120)
            else:
                subs = funcs.show_all_subs(user_wallet)
                await websocket.send(subs)


        except websockets.ConnectionClosed:
            print(f"A client {connected[websocket]} just disconnected")
            del connected[websocket]
            print(connected)


async def main():
    async with websockets.serve(echo, "localhost", PORT):
        await asyncio.Future()


asyncio.run(main())
