from locust import HttpUser, task, between

class BackendUser(HttpUser):
    wait_time = between(0.5, 1.5)   
    host = "http://127.0.0.1:8080"  

    @task
    def health_check(self):
        self.client.get("/premium-data")
