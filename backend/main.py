from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
import os
from dotenv import load_dotenv
import json
import yfinance as yf
import requests
import re
# 🔑 Load env variables
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = FastAPI()

# ✅ CORS (React/JS connect)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 📥 Request body
class RequestData(BaseModel):
    query: str


def extract_query_data(query):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": """
Extract structured data from query.

Return ONLY JSON:
{
  "stock_name": "",
  "ticker": "",
  "intent": [],
  "confidence": ""
}

intent can be:
- price
- trend
- analysis
- prediction
- recommendation 
"""
            },
            {
                "role": "user",
                "content": query
            }
        ],
        response_format={"type": "json_object"}
    )

    print(json.loads(response.choices[0].message.content))
    return json.loads(response.choices[0].message.content)
# 🔗 API endpoint
@app.post("/summarize")
def summarize(data: RequestData):
     try:
        query = data.query
        print(query)
        summary = smart_agent(query)

        return summary
    
     except Exception as e:
        return "⚠️ Server is waking up or deploying...Please try again in 1–2 minutes"


# -------------------------
# 🧠 1. DECISION ENGINE
# -------------------------
def decide_realtime(query):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": """
You are a decision engine.

Return ONLY JSON:
{
  "needs_realtime": true/false,
  "type": "general" or "news",
  "stock_name": "",
  "intent": [],
  "confidence": "",
  "query": ""
}

Rules:
- true → if query involves:
  - news
  - why rising/falling
  - current price
  - recent trend
  - future prediction (next 3 months, next year, target)
  - recommendation (suggest stocks, best stocks, top stocks)
  
- false → only if purely general knowledge
- intent can be: price, trend, analysis
- convert query into clean English for search in "query"
"""
            },
            {
                "role": "user",
                "content": query
            }
        ],
        response_format={"type": "json_object"}
    )

    return json.loads(response.choices[0].message.content)


# -------------------------
# 🌐 2. SEARCH (SERPER)
# -------------------------
def search_web(query):
 try:
    url = "https://google.serper.dev/search"

    payload = {"q": query}
    headers = {
        "X-API-KEY": os.getenv("SERPER_API_KEY"),
        "Content-Type": "application/json"
    }

    res = requests.post(url, json=payload, headers=headers)
    data = res.json()
    print(data)
    snippets = [
        item.get("snippet", "")
        for item in data.get("organic", [])
    ]
    
    return " ".join(snippets[:3])
 except Exception as e:
        return e
  


# -------------------------
# 🤖 3. SIMPLE LLM
# -------------------------
def simple_llm_answer(query):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": 
            """
            Return ONLY JSON:

{
  "summary": "",
  "reasons": [],
  "insights": [],
  "recommendation": ""
}

Rules:
- clean bullets
- Always respond in SAME LANGUAGE as user query
- If user query is Hinglish/Hindi → respond in Hinglish
- Never switch language
- Keep it simple and natural but detailed explaination 
- If exact data is not present, DO NOT guess numbers.
Return "data not available".
            """
            },
            {"role": "user", "content": query}
        ],
         response_format={"type": "json_object"}
    )

    return json.loads(response.choices[0].message.content)


# -------------------------
# 🤖 4. LLM WITH DATA
# -------------------------
def llm_with_data(query, data, ticker, data_context={}):
    print(query,ticker,data_context,data)
    if data_context.get('trend'):
        trend = data_context.get('trend')
    if data_context.get('price'):
        price = data_context.get('price')
    system_prompt_llm = """
      Return ONLY JSON:

{
  "summary": "",
  "reasons": [],
  "insights": [],
  "recommendation": ""
}
- Always respond in SAME LANGUAGE as user query
- If user query is Hinglish/Hindi → respond in Hinglish
- Never switch language
- Keep it simple and natural but detailed explaination 
- If exact data is not present, DO NOT guess numbers.
Return "data not available".
- If query contains anything related to futures and options of any markets
then return F&O (Futures & Options) queries jaise ATM price, expiry ya option chain ke liye exact real-time data yahan reliably fetch nahi ho pa raha hai.
Lekin main aapko concept ya strategy samjha sakta hoon agar aap chahein.
"""
    prompt = f"""
User query: {query}

Stock: {ticker}
"""

    if(data): 
     system_prompt_llm += """
Latest Info:
{data}
"""
    elif trend:
     system_prompt_llm +=  f"""History: {trend}"""

   

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt_llm},
            {"role": "user", "content": prompt}
        ],
         response_format={"type": "json_object"}
    )

    return json.loads(response.choices[0].message.content)


# -------------------------
# 📊 5. STOCK DATA
# -------------------------

def get_price(ticker):
    stock = yf.Ticker(ticker.upper() + ".NS")
    print(stock)
    data = stock.history(period="1d")
    if not data.empty:
        return round(data["Close"].iloc[-1], 2)
    return None


def get_trend(ticker):
    stock = yf.Ticker(ticker.upper() + ".NS")
    data = stock.history(period="5y")
    if not data.empty:
        return data["Close"].tail(5).to_list()  # last 5 points
    return None

# -------------------------
# 🚀 6. MAIN AGENT
# -------------------------
def smart_agent(query):
    try:
        print("🧠 Deciding...")

        decision = decide_realtime(query)
        print(decision)
        # 👉 No realtime needed
        if not decision.get("needs_realtime"):
            print("⚡ No realtime needed")
            return simple_llm_answer(query)

        print("🌐 Fetching realtime data...")

        ticker = None
        data_context = {}


        keywords = ["last", "days", "percent", "gira", "increase"]

        query_lower = query.lower()

        # 👉 If not news → fetch stock data
        if decision.get("type") != "news":
            data = None
            print('in general 1')
            stock = decision.get("stock_name")
            print('in general 2')
            
            ticker = stock
            intents = decision.get("intent", [])
            print('in general 3')
            if "price" in intents:
                data_context["price"] = get_price(ticker)
            print('in general 4')
                 # ✅ historical calc
            if any(word in query_lower for word in keywords) or "trend" in intents:
               days = extract_days(query)
               data_context["trend"] = calculate_from_yahoo(ticker,days)
               print(data_context)
        else:
            print("🔎 Searching web...")
            search_query = decision.get("query") or query
            print(decision)
            data = search_web(search_query)
            print(data)
        print("🤖 Generating final answer...")
        print(query,data,ticker,data_context)
        return llm_with_data(query, data, ticker, data_context)

    except Exception as e:
        return {"error": str(e)}

def calculate_from_yahoo(stock_name, days=10):
    print(stock_name,days)
    print('yahooooooooooo')
    try:
        # 🧠 Mapping (important)
        STOCK_MAP = {
        "infosys": "INFY.NS",
        "infy": "INFY.NS",
        "tcs": "TCS.NS",
        "reliance": "RELIANCE.NS",
        "hdfc bank": "HDFCBANK.NS",
        "icici bank": "ICICIBANK.NS",
        "sbi": "SBIN.NS",
        "wipro": "WIPRO.NS",
        "adani enterprises": "ADANIENT.NS",
        "adani ports": "ADANIPORTS.NS",
        "lt": "LT.NS",
        "larsen": "LT.NS",
        "asian paints": "ASIANPAINT.NS",
        "bajaj finance": "BAJFINANCE.NS",
        "kotak bank": "KOTAKBANK.NS"
        }

        ticker = STOCK_MAP.get(stock_name.lower()) 
        print(ticker)
        print('yahooooooooo')
        if not ticker:
         ticker = stock_name.upper() + ".NS"

        # 📊 Fetch historical data
        stock = yf.Ticker(ticker)
        data = stock.history(period=f"{days}d")
        print(data)
        if data.empty or len(data) < 2:
            return {"error": "Not enough data"}

        # 📈 Calculate % change
        start_price = data["Close"].iloc[0]
        end_price = data["Close"].iloc[-1]

        percent_change = ((end_price - start_price) / start_price) * 100

        return {
            "stock": stock_name,
            "days": days,
            "start_price": round(start_price, 2),
            "end_price": round(end_price, 2),
            "percent_change": round(percent_change, 2)
        }

    except Exception as e:
        return {"error": str(e)}

def extract_days(query):
                
                query = query.lower()

                # 🟢 numbers based (days/din)
                match = re.search(r'(\d+)\s*(day|days|din)', query)
                if match:
                    return int(match.group(1))

                # 🟢 weeks / hafta
                match = re.search(r'(\d+)\s*(week|weeks|hafta|hafte)', query)
                if match:
                    return int(match.group(1)) * 5   # approx trading days

                # 🟢 months / mahina
                match = re.search(r'(\d+)\s*(month|months|mahina|mahine)', query)
                if match:
                    return int(match.group(1)) * 22  # approx trading days

                # 🟢 years / saal
                match = re.search(r'(\d+)\s*(year|years|saal)', query)
                if match:
                    return int(match.group(1)) * 252  # approx trading days

                # 🟢 keywords (no number)

                if "today" in query or "aaj" in query:
                    return 1

                if "yesterday" in query or "kal" in query:
                    return 1

                if "week" in query or "hafta" in query:
                    return 5

                if "month" in query or "mahina" in query:
                    return 22

                if "year" in query or "saal" in query:
                    return 252

                # 🟢 fallback
                return 10


 