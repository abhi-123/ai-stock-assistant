import { useState } from "react";

function App() {
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  const handleSubmit = async () => {
    if (!input) return;

    setLoading(true);
    setError(null);
    setData(null);
    console.log(input)
    try {
      const res = await fetch("http://localhost:8001/summarize", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ query: input }),
      });

      const result = await res.json();
      setData(result);
    } catch (e) {
      setTimeout(() => {
        setError("⚠️ Server is waking up, please try again...");
      }, 1500);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 p-6">
      
      {/* Heading */}
      <h1 className="text-3xl font-bold text-center mb-6">
        📊 AI Stock Assistant
      </h1>

      {/* Input Card */}
      <div className="max-w-xl mx-auto bg-white p-5 rounded-xl shadow-md">
        <input
          type="text"
          placeholder="Ask anything... (e.g. TCS lena chahiye kya?)"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          className="w-full p-3 border rounded-lg outline-none focus:ring-2 focus:ring-blue-400"
        />

        <button
          onClick={handleSubmit}
          className="mt-4 w-full bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 transition"
        >
          Analyze 🚀
        </button>
      </div>

      {/* Loader */}
      {loading && (
        <div className="text-center mt-6 text-gray-600">
          ⏳ Analyzing and summarizing your content...
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="text-center mt-6 text-red-500">
          {error}
        </div>
      )}

      {/* Result */}
      {data && (
        <div className="max-w-xl mx-auto mt-6 space-y-4">

          {/* Summary */}
          <div className="bg-white p-4 rounded-xl shadow">
  <h2 className="font-bold text-lg">📊 Summary</h2>
  <p>{data.summary}</p>

  {data.reasons?.length > 0 && <h3 className="mt-3 font-semibold">📉 Reasons</h3>}
  <ul>
    {(data.reasons || []).map((r, i) => (
      <li key={i}>• {r}</li>
    ))}
  </ul>

  { data.insights.length > 0 && <h3 className="mt-3 font-semibold">💡 Insights</h3>}
  <ul>
    {(data.insights || []).map((i, idx) => (
      <li key={idx}>• {i}</li>
    ))}
  </ul>

  { data.recommendation !== '' && <h3 className="mt-3 font-semibold">🎯 Recommendation</h3>}
  <p>{data.recommendation}</p>
</div>

        </div>
      )}
    </div>
  );
}

export default App;