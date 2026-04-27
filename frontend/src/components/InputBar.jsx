import React from "react";

const InputBar = ({ value, onChange, onSend, disabled = false, error = "" }) => {
  const handleSend = () => {
    if (!value.trim() || disabled) return;
    onSend(value);
  };

  return (
    <div className="input-area">
      <div className="input-bar">
        <input
          className="message-input"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder="Describe your problem..."
          disabled={disabled}
          onKeyDown={(e) => {
            if (e.key === "Enter") handleSend();
          }}
        />
        <button className="send-button" onClick={handleSend} disabled={disabled}>
          {disabled ? "Analyzing..." : "Send"}
        </button>
      </div>
      {error && <p className="input-error">{error}</p>}
    </div>
  );
};

export default InputBar;
