import React from "react";

const LanguageSelector = ({ selected, setSelected }) => {
  return (
    <select
      value={selected}
      onChange={(e) => setSelected(e.target.value)}
      className="language-select"
      aria-label="Response language"
    >
      <option value="en">English</option>
      <option value="hi">Hindi</option>
      <option value="kn">Kannada</option>
      <option value="ta">Tamil</option>
    </select>
  );
};

export default LanguageSelector;
