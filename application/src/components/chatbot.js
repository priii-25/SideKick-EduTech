import React, { useState, useRef, useEffect } from 'react';
import './chatbot.css';

const ChatMessage = ({ message, isUser }) => (
  <div className={`message ${isUser ? 'user-message' : 'ai-message'}`}>
    <div className="message-content">
      <div className="avatar">
        {isUser ? '👤' : '🤖'}
      </div>
      <div className="text">
        {message}
      </div>
    </div>
  </div>
);

const Chatbot = () => {
  const [messages, setMessages] = useState([
    { text: "Hello! I'm your AI assistant. How can I help you today?", isUser: false }
  ]);
  const [inputText, setInputText] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const generateAIResponse = async (userInput) => {
    setIsTyping(true);
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    const aiResponse = `I received your message: "${userInput}". This is a simulated response.`;
    
    setMessages(prev => [...prev, { text: aiResponse, isUser: false }]);
    setIsTyping(false);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!inputText.trim()) return;

    setMessages(prev => [...prev, { text: inputText, isUser: true }]);
    const userInput = inputText;
    setInputText('');

    await generateAIResponse(userInput);
  };

  return (
    <div className="app-container">
      <div className="chat-container">
        <header className="chat-header">
          <h1>AI Chat Assistant</h1>
        </header>

        <div className="messages-container">
          {messages.map((message, index) => (
            <ChatMessage
              key={index}
              message={message.text}
              isUser={message.isUser}
            />
          ))}
          {isTyping && (
            <div className="typing-indicator">
              AI is typing<span>.</span><span>.</span><span>.</span>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <form className="input-form" onSubmit={handleSubmit}>
          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder="Type your message here..."
            disabled={isTyping}
          />
          <button type="submit" disabled={!inputText.trim() || isTyping}>
            Send
          </button>
        </form>
      </div>
    </div>
  );
};

export default Chatbot;