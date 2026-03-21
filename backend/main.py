from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
import os
from dotenv import load_dotenv
import json
import yfinance as yf
import requests
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
def llm_with_data(query, data, ticker, data_context):
    print(query,ticker,data_context)
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
"""
    prompt = f"""
User query: {query}

Stock: {ticker}
Structured Data: {data_context}

Latest Info:
{data}
"""

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

        # 👉 If not news → fetch stock data
        if decision.get("type") != "news":
            stock = decision.get("stock_name")

            ticker = stock
            intents = decision.get("intent", [])

            if "price" in intents:
                data_context["price"] = get_price(ticker)

            if "trend" in intents:
                data_context["trend"] = get_trend(ticker)

        print("🔎 Searching web...")
        search_query = decision.get("query") or query
        print(decision)
        data = search_web(search_query)
        print(data)
        print("🤖 Generating final answer...")

        return llm_with_data(query, data, ticker, data_context)

    except Exception as e:
        return {"error": str(e)}


 