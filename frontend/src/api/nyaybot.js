const BASE_URL = "http://127.0.0.1:8000";

// 🔹 Analyze problem
export async function analyzeProblem(text, sessionId = "", language = "en") {
  const response = await fetch(`${BASE_URL}/analyze`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ text, session_id: sessionId, language })
  });

  return await response.json();
}

export async function requestNextQuestion(sessionId = "") {
  const response = await fetch(`${BASE_URL}/analyze`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ text: "", session_id: sessionId, request_next_question: true })
  });

  return await response.json();
}

export async function generateLegalReport(sessionId = "", city = "") {
  const response = await fetch(`${BASE_URL}/generate-report`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ session_id: sessionId, city })
  });

  return await response.json();
}

// 🔹 Generate document
export async function generateDocument(data) {
  const response = await fetch(`${BASE_URL}/generate-document`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(data)
  });

  if (!response.ok) {
    throw new Error("Unable to generate document");
  }

  const blob = await response.blob();

  // Trigger download
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "legalease-ai-report.pdf";
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(url);
}
