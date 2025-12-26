import streamlit as st
from openai import OpenAI, OpenAIError
import json
import os
import datetime
from dotenv import load_dotenv
os.path.exists(".env.example")
load_dotenv(".env.example")


st.set_page_config(page_title=" هوش مصنوعی شایان پاسخگویی به مشتریان ", layout="wide")
API_KEY = os.getenv("AVALAI_API_KEY")
BASE_URL = os.getenv("AVALAI_BASE_URL", "https://api.avalai.ir/v1")

PRODUCTS = [
    {"id": 1, "name": "Laptop dell", "category": "Electronics", "price": 450, "stock": 5, "description": "Budget-friendly laptop, 8GB RAM, 256GB SSD."},
    {"id": 2, "name": "iphone 17", "category": "Electronics", "price": 999, "stock": 12, "description": "Latest flagship smartphone with best-in-class camera."},
    {"id": 3, "name": "ErgoChair V2", "category": "Furniture", "price": 150, "stock": 0, "description": "Ergonomic office chair with lumbar support. (Out of Stock)"},
    {"id": 4, "name": "Gaming Mouse G1", "category": "Accessories", "price": 45, "stock": 20, "description": "High precision RGB gaming mouse."},
    {"id": 5, "name": "Smart Coffee Maker", "category": "Home Appliances", "price": 120, "stock": 8, "description": "WiFi enabled coffee maker with timer."}
]

FAQS = """
س: فروشگاه چه زمانی باز است؟
ج: ما از شنبه تا چهارشنبه از ساعت ۹ صبح تا ۶ عصر و پنجشنبه‌ها تا ساعت ۱ ظهر پاسخگو هستیم.

س: چگونه می‌توانم محصولی را مرجوع کنم؟
ج: شما می‌توانید هر محصولی را تا ۷ روز پس از خرید (ضمانت بازگشت) اگر در شرایط اولیه باشد مرجوع کنید. با support@store.com تماس بگیرید.

س: آیا ارسال به شهرستان دارید؟
ج: بله، ما به تمام نقاط ایران ارسال داریم. هزینه ارسال با پست پیشتاز محاسبه می‌شود.

س: چه روش‌های پرداختی را می‌پذیرید؟
ج: ما تمام کارت‌های بانکی عضو شتاب را می‌پذیریم.
س:نام فروشگاه چیست؟
نام فروشگاه ما شایان است
س:آدرس فروشگاه کجاست؟
ادرس فروشگاه ما واقع در تهران خیابان انقلاب -پلاک 32
"""

def save_order(order_data):
    file_path = "orders.json"
    
    order_data["timestamp"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    existing_orders = []
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                existing_orders = json.load(f)
        except json.JSONDecodeError:
            pass

    existing_orders.append(order_data)

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(existing_orders, f, indent=4, ensure_ascii=False)
    
    return True

def get_system_prompt():
    products_json = json.dumps(PRODUCTS, indent=2)
    
    prompt = f"""
    You are an intelligent and helpful Customer Service Assistant for an online store.
    
    ### YOUR KNOWLEDGE BASE:
    
    1. **Product List (JSON):**
    {products_json}
    
    2. **Frequently Asked Questions (FAQ):**
    {FAQS}
    
    ### YOUR TASKS:
    1. **Answer Questions:** Use the Knowledge Base to answer user queries about products (price, stock, description) and FAQs.
    2. **Check Availability:** If a user asks for a product, check the 'stock'. If stock is 0, apologize and say it's unavailable.
    3. **Order Placement (CRITICAL):**
       - If a user wants to buy something, you MUST collect exactly these 4 pieces of information:
         1. **Name**
         2. **Email**
         3. **Phone Number**
         4. **Product Name**
       - Ask clarifying questions if any info is missing.
       - Do not assume information. Ask the user.
       - **Action Trigger:** ONCE you have ALL 4 pieces of information, confirm the details with the user.
       - AFTER the user confirms the details are correct, output the order data in a strict JSON format prefixed by "SAVE_ORDER_TRIGGER:".
    
    ### OUTPUT FORMAT FOR SAVING ORDER:
    When the order is finalized, your last line of response MUST be exactly like this (replace values with actual data):
    
    SAVE_ORDER_TRIGGER: {{"name": "John Doe", "email": "john@example.com", "phone": "1234567890", "product": "Laptop X1000"}}
    
    ### TONE:
    Professional, friendly, and concise.
    """
    return prompt
st.markdown("""
<style>
    .stApp {
        direction: rtl;
        text-align: right;
    }
    .stChatInput {
        direction: rtl;
    }
    p, h1, h2, h3 {
        text-align: right;
    }
</style>
""", unsafe_allow_html=True)

st.title(" هوش مصنوعی شایان پاسخگویی به مشتریان")
st.markdown("Powered by **LLM (Aval AI)** | RAG Enabled")

with st.sidebar:
    st.header("مدیریت")
    
    if st.button("پاک کردن تاریخچه"):
        st.session_state.messages = []
        st.rerun()

    st.divider()
    st.write("### دیباگ: سفارش‌های ثبت شده")
    if os.path.exists("orders.json"):
        with open("orders.json", "r", encoding="utf-8") as f:
            st.json(json.load(f))
    else:
        st.text("هنوز سفارشی ثبت نشده است.")

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "سلام! چطور می‌توانم به شما کمک کنم؟ من می‌توانم درباره محصولات راهنمایی‌تان کنم یا سفارش شما را ثبت کنم."}]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        clean_content = message["content"].split("SAVE_ORDER_TRIGGER:")[0]
        st.markdown(clean_content)

if prompt := st.chat_input("پیام خود را اینجا بنویسید..."):
    
    if not API_KEY:
        st.error("خطا: کلید API در کد برنامه تعریف نشده است. لطفاً متغیر API_KEY را در سورس کد مقداردهی کنید.")
        st.stop()

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        try:
            client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
            
            messages_payload = [{"role": "system", "content": get_system_prompt()}]
            
            messages_payload.extend(st.session_state.messages[-10:])

            completion = client.chat.completions.create(
                model="gemini-2.5-flash-preview-09-2025", 
                messages=messages_payload,
                temperature=0.7
            )
            
            response_text = completion.choices[0].message.content
            
            if "SAVE_ORDER_TRIGGER:" in response_text:
                parts = response_text.split("SAVE_ORDER_TRIGGER:")
                visible_text = parts[0].strip()
                json_part = parts[1].strip()
                
                try:
                    order_json = json.loads(json_part)
                    save_order(order_json)
                    success_message = "\n\n✅ **پیام سیستم:** سفارش شما با موفقیت در سیستم ثبت شد!"
                    full_response = visible_text + success_message
                except json.JSONDecodeError:
                    full_response = visible_text + "\n\n خطا: امکان پردازش خودکار اطلاعات سفارش وجود ندارد."
            else:
                full_response = response_text

            message_placeholder.markdown(full_response)
            
            st.session_state.messages.append({"role": "assistant", "content": full_response})

        except OpenAIError as e:
            error_str = str(e)
            if "quota_exceeded" in error_str or "429" in error_str:
                st.error(" **اعتبار تمام شده**: اعتبار کلید API شما به پایان رسیده است.")
                st.markdown("[بررسی اعتبار و صورت‌حساب در Aval AI](https://ava.al/billing)")
            else:
                st.error(f"⚠️ خطای API هوش مصنوعی: {e}")
        
        except Exception as e:
            st.error(f" خطای غیرمنتظره: {e}")