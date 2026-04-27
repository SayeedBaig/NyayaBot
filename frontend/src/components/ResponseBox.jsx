function ResponseBox({ category, response }) {
  if (!response) return null;

  return (
    <div
      style={{
        border: "1px solid #ccc",
        padding: "15px",
        borderRadius: "8px",
        marginBottom: "20px"
      }}
    >
      <h3 style={{ color: "blue" }}>
        Category: {category}
      </h3>

      <p style={{ marginTop: "10px" }}>
        {response}
      </p>
    </div>
  );
}

export default ResponseBox;