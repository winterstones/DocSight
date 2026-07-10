import { createContext, useContext, useState, ReactNode } from "react";

interface ChatContextType {
  selectedDocumentIds: string[];
  toggleDocumentSelection: (id: string) => void;
  clearSelections: () => void;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

export function ChatProvider({ children }: { children: ReactNode }) {
  const [selectedDocumentIds, setSelectedDocumentIds] = useState<string[]>([]);

  const toggleDocumentSelection = (id: string) => {
    setSelectedDocumentIds((prev) =>
      prev.includes(id) ? prev.filter((docId) => docId !== id) : [...prev, id]
    );
  };

  const clearSelections = () => {
    setSelectedDocumentIds([]);
  };

  return (
    <ChatContext.Provider
      value={{ selectedDocumentIds, toggleDocumentSelection, clearSelections }}
    >
      {children}
    </ChatContext.Provider>
  );
}

export function useChatContext() {
  const context = useContext(ChatContext);
  if (context === undefined) {
    throw new Error("useChatContext must be used within a ChatProvider");
  }
  return context;
}
