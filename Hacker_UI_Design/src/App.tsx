import { Header } from './components/Header';
import { ChatInterface } from './components/ChatInterface';
import { Sidebar } from './components/Sidebar';
import { useManusChat } from './hooks/useManusChat';

export default function App() {
  const {
    messages,
    taskState,
    thinkingState,
    toolEvents,
    stepEvents,
    contextData,
    todoItems,
    isConnected,
    isStreaming,
    streamBuffer,
    dualPanelMode,
    sendMessage,
    clearConversation,
  } = useManusChat();

  return (
    <div className="relative h-screen w-screen overflow-hidden bg-[#0a0a0a] font-mono text-[#00ff00]">
      {/* Main UI - No background effects */}
      <div className="relative flex h-full flex-col">
        <Header taskState={taskState} />

        <div className="flex flex-1 overflow-hidden border-t border-[#00ff00]">
          {/* Left panel - 70% */}
          <div className="flex w-[70%] flex-col border-r border-[#00ff00] overflow-hidden">
            <ChatInterface
              messages={messages}
              streamBuffer={streamBuffer}
              isStreaming={isStreaming}
              sendMessage={sendMessage}
              clearConversation={clearConversation}
              thinkingState={thinkingState}
              toolEvents={toolEvents}
              stepEvents={stepEvents}
              dualPanelMode={dualPanelMode}
            />
          </div>
          
          {/* Right sidebar - 30% */}
          <div className="w-[30%] overflow-y-auto">
            <Sidebar
              contextData={contextData}
              isConnected={isConnected}
              todoItems={todoItems}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
