import streamlit as st
import httpx

BANK    = "http://127.0.0.1:8000"
GATEWAY = "http://127.0.0.1:8002"

st.set_page_config(
    page_title="402 Payment Gateway",
    page_icon="💳",
    layout="wide"
)

st.title("💳 402 Payment Gateway")

# ─── Session State ───
if "user" not in st.session_state:
    st.session_state.user = None  # เก็บข้อมูล user ที่ login อยู่


# ─── Sidebar แสดงสถานะ User ───
with st.sidebar:
    st.header("👤 สถานะ")

    if st.session_state.user:
        u = st.session_state.user
        st.success(f"เข้าสู่ระบบแล้ว")
        st.metric("Username", u["username"])
        st.metric("User ID", u["id"])
        st.metric("ยอดเงิน", f"฿{u['balance']:.2f}")

        if st.button("ออกจากระบบ", use_container_width=True):
            st.session_state.user = None
            st.rerun()
    else:
        st.warning("ยังไม่ได้เข้าสู่ระบบ")

    st.divider()
    st.caption("Flow การทำงาน")
    st.code("Client\n  ↓\nGateway :8002\n  ↓\nBank API :8000\n  ↓\nBackend  :8001")


# ─── Tabs หลัก ───
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📝 สมัคร / Login",
    "💰 เติมเงิน",
    "🪙 ซื้อ Token",
    "📋 Token ของฉัน",
    "⭐ Premium Data",
])


# ──────────────────────────────────────────
# TAB 1 : สมัครสมาชิก / Login
# ──────────────────────────────────────────
with tab1:
    col1, col2 = st.columns(2)

    # สมัครสมาชิก
    with col1:
        st.subheader("✦ สมัครสมาชิก")
        st.caption("POST /users/  →  Bank API :8000")

        reg_username = st.text_input("Username", key="reg_user", placeholder="เช่น user_01")
        reg_password = st.text_input("Password (อย่างน้อย 8 ตัว)", type="password", key="reg_pass")
        reg_balance  = st.number_input("ยอดเงินเริ่มต้น (บาท)", min_value=0.0, step=1.0, key="reg_bal")

        if st.button("สร้างบัญชี →", use_container_width=True, key="btn_reg"):
            if not reg_username or not reg_password:
                st.error("กรุณากรอก Username และ Password")
            else:
                try:
                    res = httpx.post(f"{BANK}/users/", json={
                        "username": reg_username,
                        "password": reg_password,
                        "initial_balance": reg_balance,
                    })
                    data = res.json()
                    if res.status_code == 200:
                        st.session_state.user = data
                        st.success(f"✓ สร้างบัญชีสำเร็จ! User ID: {data['id']}")
                        st.json(data)
                    else:
                        st.error(f"✗ {data.get('detail', 'Unknown error')}")
                except httpx.RequestError:
                    st.error("✗ เชื่อมต่อ Bank API ไม่ได้")

    # Login
    with col2:
        st.subheader("◈ เข้าสู่ระบบ")
        st.caption("POST /login/  →  Bank API :8000")

        login_username = st.text_input("Username", key="login_user")
        login_password = st.text_input("Password", type="password", key="login_pass")

        if st.button("เข้าสู่ระบบ →", use_container_width=True, key="btn_login"):
            if not login_username or not login_password:
                st.error("กรุณากรอกข้อมูล")
            else:
                try:
                    res = httpx.post(f"{BANK}/login/", json={
                        "username": login_username,
                        "password": login_password,
                    })
                    data = res.json()
                    if res.status_code == 200:
                        st.session_state.user = data
                        st.success(f"✓ เข้าสู่ระบบสำเร็จ! ยินดีต้อนรับ {data['username']}")
                        st.json(data)
                    else:
                        st.error(f"✗ {data.get('detail', 'Incorrect username or password')}")
                except httpx.RequestError:
                    st.error("✗ เชื่อมต่อ Bank API ไม่ได้")


# ──────────────────────────────────────────
# TAB 2 : เติมเงิน
# ──────────────────────────────────────────
with tab2:
    st.subheader("💰 เติมเงิน")
    st.caption("POST /topup/  →  Bank API :8000")

    if not st.session_state.user:
        st.warning("กรุณาเข้าสู่ระบบก่อน")
    else:
        u = st.session_state.user

        col1, col2, col3 = st.columns(3)
        col1.metric("ยอดเงินปัจจุบัน", f"฿{u['balance']:.2f}")
        col2.metric("User ID", f"#{u['id']}")
        col3.metric("ราคา / Token", "฿0.10")

        st.divider()

        topup_amount = st.number_input("จำนวนเงินที่เติม (บาท)", min_value=0.01, step=1.0, key="topup_amt")

        if st.button("เติมเงิน →", use_container_width=True, key="btn_topup"):
            try:
                res = httpx.post(f"{BANK}/topup/", json={
                    "user_id": u["id"],
                    "amount":  topup_amount,
                })
                data = res.json()
                if res.status_code == 200:
                    st.session_state.user["balance"] = data["balance"]
                    st.success(f"✓ เติมเงิน ฿{topup_amount:.2f} สำเร็จ! ยอดคงเหลือ: ฿{data['balance']:.2f}")
                    st.json(data)
                    st.rerun()
                else:
                    st.error(f"✗ {data.get('detail', 'Unknown error')}")
            except httpx.RequestError:
                st.error("✗ เชื่อมต่อ Bank API ไม่ได้")


# ──────────────────────────────────────────
# TAB 3 : ซื้อ Token
# ──────────────────────────────────────────
with tab3:
    st.subheader("🪙 ซื้อ Token")
    st.caption("POST /purchase/  →  Bank API :8000")

    if not st.session_state.user:
        st.warning("กรุณาเข้าสู่ระบบก่อน")
    else:
        u = st.session_state.user

        qty = st.number_input("จำนวน Token (สูงสุด 100)", min_value=1, max_value=100, value=1, step=1)

        # แสดงราคาที่ต้องจ่าย
        total = qty * 0.10
        st.info(f"ราคารวม: ฿{total:.2f}  |  ยอดเงินปัจจุบัน: ฿{u['balance']:.2f}  |  คงเหลือหลังซื้อ: ฿{u['balance'] - total:.2f}")

        if st.button("ซื้อ Token →", use_container_width=True, key="btn_purchase"):
            try:
                res = httpx.post(f"{BANK}/purchase/", json={
                    "user_id":  u["id"],
                    "quantity": qty,
                })
                data = res.json()
                if res.status_code == 200:
                    st.session_state.user["balance"] = data["remaining_balance"]
                    st.success(f"✓ ซื้อ {data['quantity']} Token สำเร็จ! ยอดคงเหลือ: ฿{data['remaining_balance']:.2f}")

                    st.subheader("Token ที่ได้รับ")
                    for i, token_id in enumerate(data["tokens"], 1):
                        st.code(f"{i:02d}. {token_id}")

                    st.rerun()
                else:
                    st.error(f"✗ {data.get('detail', 'Unknown error')}")
            except httpx.RequestError:
                st.error("✗ เชื่อมต่อ Bank API ไม่ได้")


# ──────────────────────────────────────────
# TAB 4 : Token ของฉัน
# ──────────────────────────────────────────
with tab4:
    st.subheader("📋 Token ของฉัน")
    st.caption("GET /users/{id}/tokens  →  Bank API :8000")

    if not st.session_state.user:
        st.warning("กรุณาเข้าสู่ระบบก่อน")
    else:
        u = st.session_state.user

        col1, col2 = st.columns(2)
        show_unused = col1.toggle("เฉพาะที่ยังไม่ใช้", value=True)

        if col2.button("🔄 โหลด Token", use_container_width=True):
            try:
                res = httpx.get(f"{BANK}/users/{u['id']}/tokens?unused_only={str(show_unused).lower()}")
                data = res.json()

                if res.status_code != 200:
                    st.error(f"✗ {data.get('detail', 'Unknown error')}")
                elif len(data) == 0:
                    st.info("ไม่พบ Token")
                else:
                    st.success(f"พบ {len(data)} Token")
                    for token in data:
                        col_id, col_status, col_copy = st.columns([5, 1, 1])
                        col_id.code(token["token_id"])
                        if token["used"]:
                            col_status.error("USED")
                        else:
                            col_status.success("NEW")
                        # ปุ่ม copy ไปใส่ tab Premium ได้เลย
                        if col_copy.button("ใช้", key=f"use_{token['token_id']}"):
                            st.session_state["selected_token"] = token["token_id"]
                            st.toast(f"คัดลอก Token แล้ว ไปที่ Tab ⭐ Premium Data")

            except httpx.RequestError:
                st.error("✗ เชื่อมต่อ Bank API ไม่ได้")


# ──────────────────────────────────────────
# TAB 5 : Premium Data
# ──────────────────────────────────────────
with tab5:
    st.subheader("⭐ เข้าถึงข้อมูล Premium")
    st.caption("GET /premium-data  →  Gateway :8002  →  Bank :8000 (verify)  →  Backend :8001")

    # แสดง flow
    st.markdown("""
    ```
    Request ของคุณ
         ↓
    Gateway :8002  →  ตรวจสอบ Token กับ Bank :8000
                              ↓ (ผ่าน)
                      ดึงข้อมูลจาก Backend :8001
                              ↓
                      ส่งผลลัพธ์กลับมา
    ```
    """)

    # รับค่า token จาก Tab 4 ถ้ากด "ใช้"
    default_token = st.session_state.get("selected_token", "")

    token_input = st.text_input(
        "Token ID",
        value=default_token,
        placeholder="วาง Token UUID ที่นี่ หรือกด 'ใช้' จาก Tab Token ของฉัน"
    )

    if st.button("ส่ง Request ผ่าน Gateway →", use_container_width=True, key="btn_access"):
        if not token_input.strip():
            st.error("กรุณาใส่ Token ID")
        else:
            with st.spinner("กำลังส่ง Request ผ่าน Gateway..."):
                try:
                    res = httpx.get(
                        f"{GATEWAY}/premium-data",
                        headers={"X-Payment-Token": token_input.strip()},
                    )
                    data = res.json()

                    if res.status_code == 200:
                        st.success("✓ ผ่าน Gateway สำเร็จ! Token ถูกใช้แล้ว")

                        st.divider()
                        st.subheader("📦 ข้อมูล Premium ที่ได้รับ")

                        col1, col2 = st.columns(2)
                        col1.metric("Source", data.get("source", "—"))
                        col2.metric("Process Time", res.headers.get("x-process-time", "—") + "s")

                        st.info(f"📢 {data.get('message', '—')}")
                        st.warning(f"🔑 Secret Code: {data.get('secret_code', '—')}")

                        # เคลียร์ token ที่เลือกไว้
                        st.session_state["selected_token"] = ""

                    elif res.status_code == 402:
                        st.error(f"✗ 402 Payment Required: {data.get('detail', 'Payment Failed')}")
                    else:
                        st.error(f"✗ Error {res.status_code}: {data.get('detail', 'Unknown error')}")

                except httpx.RequestError:
                    st.error("✗ เชื่อมต่อ Gateway ไม่ได้ — ตรวจสอบว่า Server รันอยู่หรือไม่")