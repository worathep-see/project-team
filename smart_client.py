from locust import HttpUser, task, between
import uuid
import os
import sys

BANK_API_URL = "http://143.198.85.26:8000"
GATEWAY_API_URL = "http://188.166.214.193:8080"

class SmartClient(HttpUser):
    wait_time = between(1, 2)

    host = GATEWAY_API_URL

    def on_start(self):

        # เริ่มต้นผู้ใช้แต่ละคน
        self.user_id = None
        self.tokens = []
        self.prepare_bank_account()

    def prepare_bank_account(self):
        try:
            # สมัครสมาชิก
            username = f"user_{str(uuid.uuid4())[0:8]}"
            response_register = self.client.post(
                f"{BANK_API_URL}/users/", json={
                "username": username,
                "password": "password123",
                "initial_balance": 0.0
            }, name ="/users/ [Register @Bank]")

            if response_register.status_code == 200:
                self.user_id = response_register.json()['id']

                self.top_up(amount=50.0)
            else:
                print(f"Register failed: {response_register.text}")

        except Exception as e:
            print(f"Bank Connection Error: {e}")
    
    def top_up(self, amount):
        if not self.user_id:
            return
        
        self.client.post(
            f"{BANK_API_URL}/topup/", json={"user_id": self.user_id, "amount": amount},
            name = "/topup/ [Auto-Refill]"
        )
    
    @task
    def access_service_with_payment(self):
        
        if not self.user_id:
            return
        
        headers = {}
        if self.tokens:
            headers = {"X-Payment-Token": self.tokens[0]}
        
        with self.client.get("/premium-data", headers=headers, catch_response=True) as response:

            if response.status_code == 200:
                response.success()
                if self.tokens: 
                    self.tokens.pop(0)

            elif response.status_code == 402:
                response.success()
            
                if self.tokens:
                    self.tokens.pop(0)
                
                self.buy_token()
                
                if self.tokens:
                    retry_headers = {"X-Payment-Token": self.tokens[0]}
                    with self.client.get("/premium-data", headers=retry_headers, catch_response=True, 
                                         name="/premium-data (Retry)") as retry_response:
                        if retry_response.status_code == 200:
                            retry_response.success()
                            if self.tokens:
                                self.tokens.pop(0)
                            else:
                                retry_response.failure(f"Retry Failed: {retry_response.text}")
            
            else:
                response.failure(f"Unexpected Status: {response.status_code}")
    
    def buy_token(self):
        if not self.user_id:
            return
        
        quantity_to_buy = 50
        
        try:
            response_buy = self.client.post(
                f"{BANK_API_URL}/purchase/", json={
                "user_id": self.user_id,
                "quantity": quantity_to_buy},
                name ="/purchase/"    
            )

            if response_buy.status_code == 200:
                token_data = response_buy.json()
                if 'tokens' in token_data:
                    self.tokens.extend(token_data['tokens'])
            
            elif response_buy.status_code == 400 and "balance" in response_buy.text.lower():
                self.top_up(amount=50.0)

                retry_buy = self.client.post(
                    f"{BANK_API_URL}/purchase/", json={
                    "user_id": self.user_id,
                    "quantity": quantity_to_buy},
                    name="/purchase/ (Retry)"
                )
                if retry_buy.status_code == 200:
                    token_data = retry_buy.json()
                    if 'tokens' in token_data:
                        self.tokens.extend(token_data['tokens'])

        except Exception as e:
            print(f"Purchase Error: {e}")