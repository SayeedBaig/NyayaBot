import React from "react";

const MessageBubble = ({ sender, text, loading = false }) => {
  const isUser = sender === "user";

  return (
    <div className={`message-row ${isUser ? "user" : "bot"}`}>
      <div className={`message-bubble ${isUser ? "user" : "bot"}`}>
        <span>{text}</span>
        {loading && (
          <span className="typing-dots" aria-label="Thinking">
            <span />
            <span />
            <span />
          </span>
        )}
      </div>
    </div>
  );
};

export default MessageBubble;
