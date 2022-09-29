import colorama
import requests
import hashlib
import ctypes
import base64
import hmac
import json
import time
import sys

colorama.init(autoreset = True)

class Withdraw:

    def __init__(self, address, withdraw_amount, access_key, passphrase, secret):
        
        self.total = 0

        self.address = address

        self.withdraw_amount = withdraw_amount

        self.access_key = access_key

        self.passphrase = passphrase

        self.secret = secret

        self.balance_url = "https://api.exchange.coinbase.com/accounts"

        self.withdraw_url = "https://api.exchange.coinbase.com/withdrawals/crypto"


    def timestamp_and_signature(self, method, api_secret, request_path, body):

        hmac_key = base64.b64decode(api_secret)
    
        timestamp = str(time.time())
    
        message = timestamp + method + request_path + body
    
        message = message.encode('ascii')
    
        signature = hmac.new(
            hmac_key,
            message,
            hashlib.sha256,
        )
        signature_b64 = base64.b64encode(
        signature.digest()
        ).decode('utf-8')
        return timestamp, signature_b64


    def get_btc_price(self):

        response = requests.get('https://api.coinbase.com/v2/exchange-rates?currency=BTC')

        return int(float(response.text.split("MUSD\":\"")[1].split('"')[0].strip()))


    def get_total_amount(self):
        
        stamp, sig = self.timestamp_and_signature("GET", self.secret, "/accounts", "")

        r = requests.get(url = self.balance_url, headers = {

                "CB-ACCESS-KEY": self.access_key,

                "CB-ACCESS-PASSPHRASE": self.passphrase,

                "CB-ACCESS-SIGN": sig,

                "CB-ACCESS-TIMESTAMP": stamp
                
                })
        

        if "balance" in r.text:

            return r.text.split('"currency":"BTC","balance":"')[1].split('"')[0]

        else:

            print(r.content)

            sys.exit(1)

        
        



    def get_balance(self):

        btc_price_usd = self.get_btc_price()

        btc_balance = self.get_total_amount()

        return btc_price_usd, btc_balance


    def show_title(self):

        balance = int(self.get_total_amount())

        while 1:

            ctypes.windll.kernel32.SetConsoleTitleW(f"Total Withdrawn: {self.total:,} | Time Remaining: {balance / self.withdraw_amount} seconds ")

            time.sleep(30)

    def withdraw(self, real_time_price):

        stamp, sig = self.timestamp_and_signature("POST", self.secret, "/withdrawals/crypto", json.dumps({

                    "amount": round(self.withdraw_amount / real_time_price, 8),

                    "currency": "BTC",

                    "crypto_address": self.address

                }))

        r = requests.post(url = self.withdraw_url, headers = {

                "cb-access-key": self.access_key,

                "cb-access-passphrase": self.passphrase,

                "cb-access-sign": sig,

                "cb-access-timestamp": stamp


                }, json = {

                    "amount": round(self.withdraw_amount / real_time_price, 8),

                    "currency": "BTC",

                    "crypto_address": self.address

                })

        return r.status_code, r.text


    def attempt_withdraw(self):
        
        real_time_price = self.get_btc_price()

        counter = 0

        while 1:
                
            status, resp = self.withdraw(real_time_price)

            if status == 200:

                counter += 1

                print(f"{colorama.Fore.GREEN}[{counter}] Successfully Withdrew: ${self.withdraw_amount} from account.")

                self.total += self.withdraw_amount

                time.sleep(30)


            elif "Insufficient funds" in resp:

                print(f"{colorama.Fore.LIGHTBLUE_EX}Checking final balance...")

                final_balance = float(self.get_total_amount())

                if final_balance >= 0.00042:

                    print(f"{colorama.Fore.LIGHTBLUE_EX}Withdrawing final amount... [{final_balance}]")
                    
                    status, resp = self.withdraw(real_time_price)

                    if status == 200:

                        print(f"{colorama.Fore.LIGHTBLUE_EX}Withdrew final amount. Exiting")
                    
                    sys.exit(0)


                else:

                    print(f"{colorama.Fore.LIGHTRED_EX}Balance is either $0 or too small to withdraw. Exiting.")

                    sys.exit(0)



                print(f"{colorama.Fore.RED} Successfully withdrew all of the money from the account. Exiting.")

                sys.exit(1)

                




def main():

    print(f"{colorama.Fore.GREEN}Address > ", end = "")

    address = input("")


    print(f"{colorama.Fore.GREEN}Withdraw each time (USD) > ", end = "")

    withdraw_amount = int(input(""))


    print(f"{colorama.Fore.GREEN}Passphrase > ", end = "")

    passphrase = input("")


    print(f"{colorama.Fore.GREEN}Secret Key > ", end = "")

    secret = input("")


    print(f"{colorama.Fore.GREEN}Access Key > ", end = "")
    
    access_key = input("")


    withdraw = Withdraw(address, withdraw_amount, access_key, passphrase, secret)

    usd_trade_price, balance_btc = withdraw.get_balance()

    print(f"{colorama.Fore.LIGHTBLUE_EX}Total Available Balance: USD: ${round(float(balance_btc) * usd_trade_price):,} BTC: {round(float(balance_btc), 8)}")

    withdraw.attempt_withdraw()

if __name__ == "__main__":

    main()