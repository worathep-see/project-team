from fastapi import FastAPI, HTTPException, Header, Request, status
import httpx
import time

# --- ตั้งค่า URL ของ Bank และ Backend ตรงนี้ ---
BANK_API_URL = "http://143.198.85.26:8000"      # Mock Bank
BACKEND_API_URL = "http://143.198.85.26:8001"   # Backend Service
# ------------------------------------------------
# วิธีรัน: uvicorn gateway:app --host 188.166.214.193 --port 8080

app = FastAPI(title="Gateway", version="1.0.0")


async def verify_payment_token(token: str):
    # คุยกับบริการธนาคารเพื่อตรวจสอบ token
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{BANK_API_URL}/verify/",
                json={"token_id": token},
                timeout=5.0)

            if response.status_code != 200:
                return False, "Bank Connection Error"

            result = response.json()
            return result.get("valid"), result.get("message")

        except httpx.TimeoutException:
            return False, "Bank Timeout"
        except httpx.RequestError:
            return False, "Bank Unreachable"


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    # สำหรับจับเวลาการประมวลผลคำขอ
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


@app.get("/")
def home():
    return {"message": "Welcome to 402 Gateway!"}


@app.get("/premium-data")
async def get_premium_data(x_payment_token: str = Header(None, alias="X-Payment-Token")):

    if not x_payment_token:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Missing Payment Token. Please purchase at Bank")

    is_valid, message = await verify_payment_token(x_payment_token)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Payment Failed: {message}")

    async with httpx.AsyncClient() as client:
        try:
            backend_response = await client.get(
                f"{BACKEND_API_URL}/expensive-data", timeout=10.0)
            return backend_response.json()
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="Backend Service Unavailable")