/**
 * React hook for Manus chat integration
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { apiService, ChatMessage, TaskUpdate, ThinkingUpdate, ToolEvent, ContextUpdate, FeedbackData } from '../services/api';
import { StepEvent } from '../components/StepEventPanel';

interface UseManusChat {
  // State
  messages: ChatMessage[];
  taskState: TaskUpdate | null;
  thinkingState: ThinkingUpdate | null;
  toolEvents: ToolEvent[];
  stepEvents: StepEvent[];
  contextData: ContextUpdate | null;
  todoItems: any[];
  isConnected: boolean;
  isStreaming: boolean;
  streamBuffer: string;
  dualPanelMode: boolean;

  // Actions
  sendMessage: (message: string) => Promise<void>;
  sendCommand: (command: string) => void;
  clearConversation: () => void;
  exportConversation: (format: 'md' | 'json') => void;
  connect: () => Promise<void>;
  disconnect: () => void;
}

export function useManusChat(): UseManusChat {
  // State
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [taskState, setTaskState] = useState<TaskUpdate | null>(null);
  const [thinkingState, setThinkingState] = useState<ThinkingUpdate | null>(null);
  const [toolEvents, setToolEvents] = useState<ToolEvent[]>([]);
  const [stepEvents, setStepEvents] = useState<StepEvent[]>([]);
  const [contextData, setContextData] = useState<ContextUpdate | null>(null);
  const [todoItems, setTodoItems] = useState<any[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamBuffer, setStreamBuffer] = useState('');
  const [dualPanelMode, setDualPanelMode] = useState(true);  // Enable dual panel by default

  const streamBufferRef = useRef('');

  // Initialize connection on mount
  useEffect(() => {
    const initConnection = async () => {
      try {
        await apiService.connect();
      } catch (error) {
        console.error('Failed to connect:', error);
      }
    };

    initConnection();

    // Cleanup on unmount
    return () => {
      apiService.disconnect();
    };
  }, []);

  // Setup event listeners
  useEffect(() => {
    // Connection events
    const handleConnected = () => {
      setIsConnected(true);
      addSystemMessage('Connected to Manus backend');
    };

    const handleDisconnected = () => {
      setIsConnected(false);
      addSystemMessage('Disconnected from backend');
    };

    const handleError = (error: any) => {
      addSystemMessage(`Error: ${error.message || 'Connection failed'}`);
    };

    // Message events
    const handleMessage = (message: ChatMessage) => {
      setMessages(prev => [...prev, message]);
    };

    // Streaming events
    const handleStreamStart = () => {
      setIsStreaming(true);
      streamBufferRef.current = '';
      setStreamBuffer('');
    };

    const handleStreamToken = (token: string) => {
      streamBufferRef.current += token;
      setStreamBuffer(streamBufferRef.current);
    };

    const handleStreamComplete = () => {
      if (streamBufferRef.current) {
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: streamBufferRef.current,
          timestamp: new Date().toISOString()
        }]);
      }
      setIsStreaming(false);
      streamBufferRef.current = '';
      setStreamBuffer('');
    };

    const handleStreamError = (error: string) => {
      setIsStreaming(false);
      addSystemMessage(`Stream error: ${error}`);
    };

    // Task updates
    const handleTaskUpdate = (update: TaskUpdate) => {
      setTaskState(update);
    };

    // Thinking updates
    const handleThinkingUpdate = (update: ThinkingUpdate) => {
      setThinkingState(update);
    };

    // Tool events
    const handleToolEvent = (event: ToolEvent) => {
      setToolEvents(prev => [...prev, event]);
    };

    // Context updates
    const handleContextUpdate = (update: ContextUpdate) => {
      setContextData(update);
    };

    // Feedback events
    const handleFeedback = (feedback: FeedbackData) => {
      const { type, data } = feedback;
      let message = '';

      if (type === 'success') {
        message = `✓ Done: ${data.action} (${data.details})`;
      } else if (type === 'warning') {
        message = `⚠ Warning: ${data.issue}; ${data.suggestion}`;
      } else if (type === 'error') {
        message = `✗ Failed: ${data.reason} → ${data.nextAction}`;
      }

      if (message) {
        setMessages(prev => [...prev, {
          role: 'feedback',
          content: message,
          timestamp: new Date().toISOString()
        }]);
      }
    };

    // Todo updates
    const handleTodoUpdate = (todos: any[]) => {
      setTodoItems(todos);
    };

    // Clear conversation
    const handleClearConversation = () => {
      setMessages([]);
      setToolEvents([]);
      setThinkingState(null);
      addSystemMessage('Conversation cleared');
    };

    // Export complete
    const handleExportComplete = (data: any) => {
      // Create download link
      const blob = new Blob([data.content], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `conversation_${Date.now()}.${data.format}`;
      a.click();
      URL.revokeObjectURL(url);

      addSystemMessage(`Exported conversation as ${data.format}`);
    };

    // Handle step events from the structured event system
    const handleStepEvent = (event: StepEvent) => {
      setStepEvents(prev => [...prev, event]);
    };

    // Register event handlers
    apiService.on('connected', handleConnected);
    apiService.on('disconnected', handleDisconnected);
    apiService.on('error', handleError);
    apiService.on('message', handleMessage);
    apiService.on('stream_start', handleStreamStart);
    apiService.on('stream_token', handleStreamToken);
    apiService.on('stream_complete', handleStreamComplete);
    apiService.on('stream_error', handleStreamError);
    apiService.on('task_update', handleTaskUpdate);
    apiService.on('thinking_update', handleThinkingUpdate);
    apiService.on('tool_event', handleToolEvent);
    apiService.on('context_update', handleContextUpdate);
    apiService.on('feedback', handleFeedback);
    apiService.on('todo_update', handleTodoUpdate);
    apiService.on('clear_conversation', handleClearConversation);
    apiService.on('export_complete', handleExportComplete);
    apiService.on('step_event', handleStepEvent);

    // Cleanup
    return () => {
      apiService.off('connected', handleConnected);
      apiService.off('disconnected', handleDisconnected);
      apiService.off('error', handleError);
      apiService.off('message', handleMessage);
      apiService.off('stream_start', handleStreamStart);
      apiService.off('stream_token', handleStreamToken);
      apiService.off('stream_complete', handleStreamComplete);
      apiService.off('stream_error', handleStreamError);
      apiService.off('task_update', handleTaskUpdate);
      apiService.off('thinking_update', handleThinkingUpdate);
      apiService.off('tool_event', handleToolEvent);
      apiService.off('context_update', handleContextUpdate);
      apiService.off('feedback', handleFeedback);
      apiService.off('todo_update', handleTodoUpdate);
      apiService.off('clear_conversation', handleClearConversation);
      apiService.off('export_complete', handleExportComplete);
      apiService.off('step_event', handleStepEvent);
    };
  }, []);

  // Helper function to add system messages
  const addSystemMessage = (content: string) => {
    setMessages(prev => [...prev, {
      role: 'system',
      content,
      timestamp: new Date().toISOString()
    }]);
  };

  // Send message
  const sendMessage = useCallback(async (message: string) => {
    if (!message.trim()) return;

    // Add user message
    setMessages(prev => [...prev, {
      role: 'user',
      content: message,
      timestamp: new Date().toISOString()
    }]);

    // Handle commands
    if (message.startsWith('/')) {
      apiService.sendCommand(message);
      return;
    }

    // Send via WebSocket or HTTP streaming
    try {
      if (isConnected) {
        // Use WebSocket if connected
        apiService.sendChatViaWebSocket(message);
      } else {
        // Fallback to HTTP streaming
        await apiService.sendChatMessage(message);
      }
    } catch (error) {
      console.error('Error sending message:', error);
      addSystemMessage('Failed to send message');
    }
  }, [isConnected]);

  // Send command
  const sendCommand = useCallback((command: string) => {
    apiService.sendCommand(command);
  }, []);

  // Clear conversation
  const clearConversation = useCallback(() => {
    setMessages([]);
    setToolEvents([]);
    setStepEvents([]);
    setThinkingState(null);
    setTaskState(null);
  }, []);

  // Export conversation
  const exportConversation = useCallback((format: 'md' | 'json') => {
    apiService.exportConversation(format);
  }, []);

  // Connect to backend
  const connect = useCallback(async () => {
    try {
      await apiService.connect();
    } catch (error) {
      console.error('Connection failed:', error);
    }
  }, []);

  // Disconnect from backend
  const disconnect = useCallback(() => {
    apiService.disconnect();
  }, []);

  return {
    // State
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

    // Actions
    sendMessage,
    sendCommand,
    clearConversation,
    exportConversation,
    connect,
    disconnect
  };
}