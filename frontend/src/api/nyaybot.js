const BASE_URL = "http://127.0.0.1:8000";

// 🔹 Analyze problem
export async function analyzeProblem(text) {
  const response = await fetch(`${BASE_URL}/analyze`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ text })
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
  a.download = "complaint.docx";
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(url);
}
