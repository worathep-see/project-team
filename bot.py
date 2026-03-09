from locust import HttpUser, task, between

# Scenario A (Baseline): ชี้ตรงไปที่ Backend โดยไม่ผ่าน Gateway
# TARGET_URL = "http://143.198.85.26:8001"

# Scenario B (With Gateway): ชี้ผ่าน Gateway
TARGET_URL = "http://188.166.214.193:8080"

class AttackerBot(HttpUser):
    wait_time = between(0.5, 1.5)
    host = TARGET_URL

    @task
    def flood_attack(self):
        self.client.get("/premium-data")