import { useState } from "react";

function StockAnalyzer() {
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  const handleSubmit = async () => {
    if (!input) return;

    setLoading(true);
    setError(null);
    setData(null);

    try {
      const res = await fetch(
        "https://ai-stock-assistant-c6el.onrender.com/summarize",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ query: input }),
        },
      );

      const result = await res.json();
      setData(result);
    } catch {
      setTimeout(() => {
        setError("⚠️ Server is waking up, please try again...");
      }, 1500);
    } finally {
      setLoading(false);
    }
  };

  const isSimple =
    (!data?.reasons || data.reasons.length === 0) &&
    (!data?.insights || data.insights.length === 0);

  return (
    <div className="min-h-[calc(100vh-64px)] bg-gradient-to-br from-blue-50 via-white to-gray-100 p-6">
      {/* 🔥 HERO SECTION */}
      <div className="text-center mb-10 animate-fadeIn">
        <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-500 bg-clip-text text-transparent">
          📊 AI Stock Assistant
        </h1>
        <p className="text-gray-500 mt-2">Smart insights. Better decisions.</p>
      </div>

      {/* 🔥 INPUT CARD */}
      <div className="max-w-3xl mx-auto">
        <div className="flex items-center bg-white rounded-2xl shadow-lg px-4 py-3 border border-gray-200 focus-within:ring-2 focus-within:ring-blue-400 transition">
          {/* Icon */}
          <span className="text-gray-400 text-lg mr-3">🔍</span>

          {/* Input */}
          <input
            type="text"
            placeholder="Ask about any stock... (e.g. TCS lena chahiye kya?)"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            className="flex-1 outline-none text-gray-700 placeholder-gray-400 bg-transparent"
          />

          {/* Button */}
          <button
            onClick={handleSubmit}
            className="ml-3 bg-gradient-to-r from-blue-600 to-blue-500 text-white px-5 py-2 rounded-xl hover:scale-105 active:scale-95 transition-all shadow-md"
          >
            Analyze 🚀
          </button>
        </div>
      </div>

      {/* 🔥 LOADER */}
      {loading && (
        <div className="flex flex-col items-center mt-10 animate-fadeIn">
          <div className="w-10 h-10 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
          <p className="mt-3 text-gray-600 animate-pulse">
            Thinking like a trader 🧠📈...
          </p>
        </div>
      )}

      {/* ERROR */}
      {error && (
        <div className="text-center mt-6 text-red-500 font-medium animate-fadeIn">
          {error}
        </div>
      )}

      {/* 🔥 RESULTS */}
      {data && (
        <div className="max-w-5xl mx-auto mt-12 animate-fadeIn">
          {/* 🔥 SIMPLE MODE (price / basic info) */}
          {isSimple ? (
            <div className="bg-gradient-to-r from-blue-500 to-blue-600 text-white p-8 rounded-3xl shadow-2xl text-center">
              <h2 className="text-xl font-semibold mb-2">📊 Quick Insight</h2>

              <p className="text-2xl font-bold leading-relaxed">
                {data.summary}
              </p>
            </div>
          ) : (
            /* 🔥 ADVANCED MODE (full data) */
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Summary */}
              <div className="bg-gradient-to-r from-blue-50 to-white p-6 rounded-2xl shadow-lg border-l-4 border-blue-500">
                <h2 className="font-bold text-lg mb-2">📊 Summary</h2>
                <p>{data.summary}</p>
              </div>

              {/* Reasons */}
              {data.reasons?.length > 0 && (
                <div className="bg-gray-50 p-5 rounded-2xl shadow-sm border">
                  <h3 className="font-semibold mb-2">📉 Reasons</h3>
                  <ul className="space-y-1">
                    {data.reasons.map((r, i) => (
                      <li key={i}>• {r}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Insights */}
              {data.insights?.length > 0 && (
                <div className="bg-gray-50 p-5 rounded-2xl shadow-sm border">
                  <h3 className="font-semibold mb-2">💡 Insights</h3>
                  <ul className="space-y-1">
                    {data.insights.map((i, idx) => (
                      <li key={idx}>• {i}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Recommendation */}
              {data.recommendation && (
                <div className="bg-blue-100 p-5 rounded-2xl shadow-md border border-blue-200">
                  <h3 className="font-semibold mb-2">🎯 Recommendation</h3>
                  <p>{data.recommendation}</p>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default StockAnalyzer;
