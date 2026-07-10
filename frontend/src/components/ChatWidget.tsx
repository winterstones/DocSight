import { useState, useEffect, useRef } from "react";
import { useChat } from "../hooks/useSearch";
import { useChatContext } from "../context/ChatContext";

interface Message {
  role: "user" | "assistant";
  content: string;
  sources?: any[];
}

export function ChatWidget() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const chatMutation = useChat();
  const { selectedDocumentIds } = useChatContext();

  // Load from sessionStorage on mount
  useEffect(() => {
    const saved = sessionStorage.getItem("docsight_chat_history");
    if (saved) {
      try {
        setMessages(JSON.parse(saved));
      } catch (e) {
        console.error("Failed to parse chat history", e);
      }
    }
  }, []);

  // Save to sessionStorage when messages change
  useEffect(() => {
    sessionStorage.setItem("docsight_chat_history", JSON.stringify(messages));
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const toggleWidget = () => setIsOpen((prev) => !prev);

  const handleSend = () => {
    if (!inputValue.trim()) return;

    const userMessage: Message = { role: "user", content: inputValue };
    setMessages((prev) => [...prev, userMessage]);
    setInputValue("");

    chatMutation.mutate(
      { question: userMessage.content, documentIds: selectedDocumentIds },
      {
        onSuccess: (data) => {
          setMessages((prev) => [
            ...prev,
            {
              role: "assistant",
              content: data.answer,
              sources: data.sources,
            },
          ]);
        },
        onError: () => {
          setMessages((prev) => [
            ...prev,
            {
              role: "assistant",
              content: "Une erreur est survenue lors de la communication avec l'assistant.",
            },
          ]);
        },
      }
    );
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      handleSend();
    }
  };

  return (
    <>
      <button className="chat-fab" onClick={toggleWidget} aria-label="Toggle chat">
        💬
      </button>

      <div className={`chat-widget-panel ${isOpen ? "open" : ""}`}>
        <div className="chat-header">
          <h3>Assistant DocSight</h3>
          <button className="close-btn" onClick={toggleWidget}>✕</button>
        </div>

        <div className="chat-messages">
          {messages.length === 0 ? (
            <p className="chat-empty">Bonjour ! Comment puis-je vous aider avec vos documents ?</p>
          ) : (
            messages.map((msg, index) => (
              <div key={index} className={`chat-message ${msg.role}`}>
                <div className="message-content">{msg.content}</div>
                {msg.role === "assistant" && msg.sources && msg.sources.length > 0 && (
                  <div className="message-sources">
                    <span className="sources-title">Sources :</span>
                    <ul>
                      {msg.sources.map((src: any) => (
                        <li key={src.id}>
                          <a href={`/search?q=${encodeURIComponent(src.title)}`} target="_blank" rel="noreferrer">
                            {src.title}
                          </a>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ))
          )}
          {chatMutation.isPending && (
            <div className="chat-message assistant thinking">
              <span className="pulse">En cours de réflexion...</span>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="chat-input-area">
          {selectedDocumentIds.length > 0 && (
            <div className="chat-context-badge">
              {selectedDocumentIds.length} document(s) en contexte
            </div>
          )}
          <div className="input-group">
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Posez votre question..."
              disabled={chatMutation.isPending}
            />
            <button onClick={handleSend} disabled={chatMutation.isPending || !inputValue.trim()}>
              Envoyer
            </button>
          </div>
        </div>
      </div>
    </>
  );
}
