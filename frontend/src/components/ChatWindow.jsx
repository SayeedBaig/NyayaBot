import React, { useEffect, useRef } from "react";
import MessageBubble from "./MessageButton";

const ChatWindow = ({ messages, starterSuggestions, onStarterClick, disabled = false }) => {
  const chatRef = useRef(null);

  useEffect(() => {
    chatRef.current?.scrollTo({
      top: chatRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages]);

  return (
    <div className="chat-window">
      <div className="chat-scroll" ref={chatRef}>
        {messages.length === 0 ? (
          <div className="empty-chat">
            <p className="section-kicker">Start here</p>
            <h3>Get Free Legal Guidance in Seconds</h3>
            <p>Know your rights, take action, and generate legal documents instantly</p>
            <div className="starter-suggestions" aria-label="Starter suggestions">
              {starterSuggestions.map((suggestion) => (
                <button
                  className="starter-card"
                  key={suggestion}
                  onClick={() => onStarterClick(suggestion)}
                  disabled={disabled}
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((msg) => (
            <MessageBubble
              key={msg.id}
              sender={msg.sender}
              text={msg.text}
              loading={msg.loading}
            />
          ))
        )}
      </div>
    </div>
  );
};

export default ChatWindow;
