import React from "react";

const LocationCard = ({ name, address, phone, hours }) => {
  return (
    <div className="location-card">
      <h4>{name}</h4>
      <p>{address}</p>
      <p>Phone: {phone}</p>
      <p>Hours: {hours}</p>
    </div>
  );
};

export default LocationCard;
