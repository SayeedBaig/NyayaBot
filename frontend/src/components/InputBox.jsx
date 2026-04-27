import { useState } from "react";
import { analyzeProblem } from "../api/nyaybot";

function InputBox({ onResult }) {
  const [text, setText] = useState("");

  const handleSubmit = async () => {
    if (!text) return;

    const data = await analyzeProblem(text);
    onResult(data, text);
  };

  return (
    <div style={{ marginBottom: "20px" }}>
      <textarea
        placeholder="Describe your problem..."
        value={text}
        onChange={(e) => setText(e.target.value)}
        rows="4"
        style={{ width: "100%", padding: "10px" }}
      />

      <button
        onClick={handleSubmit}
        style={{
          marginTop: "10px",
          padding: "10px 20px",
          cursor: "pointer"
        }}
      >
        Analyze
      </button>
    </div>
  );
}

export default InputBox;