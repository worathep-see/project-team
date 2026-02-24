from locust import HttpUser, task, between

class BackendUser(HttpUser):
    wait_time = between(0.5, 1.5)   
    host = "http://188.166.214.193:8080"  

    @task
    def health_check(self):
        self.client.get("/premium-data")