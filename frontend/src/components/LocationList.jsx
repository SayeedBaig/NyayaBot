function LocationList({ locations }) {
  if (!locations || locations.length === 0) return null;

  return (
    <div style={{ marginBottom: "20px" }}>
      <h3>Nearby Legal Offices</h3>

      {locations.map((loc, index) => (
        <div
          key={index}
          style={{
            border: "1px solid #ddd",
            padding: "10px",
            borderRadius: "6px",
            marginTop: "10px"
          }}
        >
          <strong>{loc.name}</strong>
          <p>{loc.address}</p>
          <p>📞 {loc.phone}</p>
          <p>🕒 {loc.hours}</p>
        </div>
      ))}
    </div>
  );
}

export default LocationList;