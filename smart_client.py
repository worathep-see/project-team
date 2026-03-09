from locust import HttpUser, task, between
import uuid

BANK_API_URL = "http://143.198.85.26:8000"
GATEWAY_API_URL = "http://188.166.214.193:8080"

# ---- ค่าที่ปรับได้ ----
INITIAL_TOPUP = 50.0      # เติมเงินตอน start (เท่าเดิมตามรูปเล่ม)
INITIAL_BUY = 50          # ซื้อ token ตอน start (เท่าเดิมตามรูปเล่ม)
REFILL_THRESHOLD = 10     # [แก้ไข #1] ซื้อ token เพิ่มทันทีถ้าเหลือน้อยกว่านี้
REFILL_QUANTITY = 50      # [แก้ไข #1] ซื้อทีละเท่าไหร่ตอน refill
# ----------------------


class SmartClient(HttpUser):
    wait_time = between(1, 2)
    host = GATEWAY_API_URL

    def on_start(self):
        self.user_id = None
        self.tokens = []
        self.prepare_bank_account()

    def prepare_bank_account(self):
        try:
            username = f"user_{str(uuid.uuid4())[0:8]}"
            response_register = self.client.post(
                f"{BANK_API_URL}/users/",
                json={
                    "username": username,
                    "password": "password123",
                    "initial_balance": 0.0,
                },
                name="/users/ [Register @Bank]",
            )
            if response_register.status_code == 200:
                self.user_id = response_register.json()["id"]
                self.top_up(amount=INITIAL_TOPUP)
                # [แก้ไข #2] เพิ่ม buy_token() ตอน on_start (รูปเล่มหายไป)
                self.buy_token(quantity=INITIAL_BUY)
            else:
                print(f"Register failed: {response_register.text}")

        except Exception as e:
            print(f"Bank Connection Error: {e}")

    def top_up(self, amount):
        if not self.user_id:
            return
        self.client.post(
            f"{BANK_API_URL}/topup/",
            json={"user_id": self.user_id, "amount": amount},
            name="/topup/ [Auto-Refill]",
        )

    def buy_token(self, quantity=REFILL_QUANTITY):
        if not self.user_id:
            return
        try:
            response_buy = self.client.post(
                f"{BANK_API_URL}/purchase/",
                json={
                    "user_id": self.user_id,
                    "quantity": quantity,
                },
                name="/purchase/",
            )

            if response_buy.status_code == 200:
                token_data = response_buy.json()
                if "tokens" in token_data:
                    self.tokens.extend(token_data["tokens"])

            elif (
                response_buy.status_code == 400
                and "balance" in response_buy.text.lower()
            ):
                self.top_up(amount=50.0)
                retry_buy = self.client.post(
                    f"{BANK_API_URL}/purchase/",
                    json={
                        "user_id": self.user_id,
                        "quantity": quantity,
                    },
                    name="/purchase/ (Retry)",
                )
                if retry_buy.status_code == 200:
                    token_data = retry_buy.json()
                    if "tokens" in token_data:
                        self.tokens.extend(token_data["tokens"])

        except Exception as e:
            print(f"Purchase Error: {e}")

    @task
    def access_service_with_payment(self):
        if not self.user_id:
            return

        # [แก้ไข #1] Refill ล่วงหน้าถ้า token เหลือน้อย ป้องกันช่วง token ว่าง
        if len(self.tokens) < REFILL_THRESHOLD:
            self.buy_token(quantity=REFILL_QUANTITY)

        # [แก้ไข #3] ถ้าไม่มี token เลย → skip แทนการส่ง request เปล่า (ไม่นับ fail)
        if not self.tokens:
            return

        headers = {"X-Payment-Token": self.tokens[0]}

        with self.client.get(
            "/premium-data", headers=headers, catch_response=True
        ) as response:

            if response.status_code == 200:
                response.success()
                # [แก้ไข #4] pop หลัง success เท่านั้น ไม่ pop ก่อนรู้ผล
                self.tokens.pop(0)

            elif response.status_code == 402:
                response.failure("402 Payment Required")
                # [แก้ไข #4] pop token ที่ invalid ออก
                self.tokens.pop(0)
                self.buy_token()

                if self.tokens:
                    retry_headers = {"X-Payment-Token": self.tokens[0]}
                    with self.client.get(
                        "/premium-data",
                        headers=retry_headers,
                        catch_response=True,
                        name="/premium-data (Retry)",
                    ) as retry_response:
                        if retry_response.status_code == 200:
                            retry_response.success()
                            self.tokens.pop(0)
                        else:
                            retry_response.failure(
                                f"Retry Failed: {retry_response.text}"
                            )

            else:
                response.failure(f"Unexpected Status: {response.status_code}")