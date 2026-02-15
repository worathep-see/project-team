from fastapi import FastAPI
import time
import math

app = FastAPI(title="Backend Service", version="1.0.0")

EXPENSIVE_DATA = {"message": "Welcome to Payment Required Project",
                  "secret_code": "Bitcoin Price is up!",
                  "source": "Backend Service"}

def burn_cpu_task():
    val = 0
    # แก้เลขตรงนี้ตามที่ calibrate ได้
    for i in range(50000): 
        val += math.sqrt(i)
    return val

@app.get("/expensive-data")
def get_data():
    _ = burn_cpu_task()
    return EXPENSIVE_DATA

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=81)    