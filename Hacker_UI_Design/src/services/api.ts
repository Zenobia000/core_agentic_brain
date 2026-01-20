/**
 * API Service for connecting to OpenManus backend
 */

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system' | 'feedback';
  content: string;
  timestamp?: string;
}

export interface TaskUpdate {
  name: string;
  currentPhase: number;
  totalPhases: number;
  phaseName: string;
  waitingFor?: string | null;
}

export interface ThinkingUpdate {
  summary: string;
  detail?: string;
  steps?: string[];
}

export interface ToolEvent {
  tool: string;
  status: 'running' | 'success' | 'error';
  result?: string;
  timestamp: string;
}

export interface ContextUpdate {
  tokens: [number, number];
  model: string;
  cost: number;
  latency: number;
}

export interface FeedbackData {
  type: 'success' | 'warning' | 'error';
  data: {
    action?: string;
    details?: string;
    issue?: string;
    suggestion?: string;
    reason?: string;
    nextAction?: string;
  };
}

class ApiService {
  private baseUrl: string;
  private ws: WebSocket | null = null;
  private sessionId: string | null = null;
  private eventHandlers: Map<string, Function[]> = new Map();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;

  constructor(baseUrl: string = 'http://localhost:8000') {
    this.baseUrl = baseUrl;
  }

  /**
   * Initialize WebSocket connection
   */
  async connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${new URL(this.baseUrl).host}/ws`;

      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        console.log('WebSocket connected');
        this.reconnectAttempts = 0;
        this.emit('connected');

        // Send init message
        this.send('init', {
          mode: 'hacker',
          sessionId: this.sessionId
        });

        resolve();
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.handleMessage(data);
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        this.emit('error', error);
        reject(error);
      };

      this.ws.onclose = () => {
        console.log('WebSocket disconnected');
        this.emit('disconnected');
        this.attemptReconnect();
      };
    });
  }

  /**
   * Send message via WebSocket
   */
  send(type: string, payload: any): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type, payload }));
    } else {
      console.warn('WebSocket not ready, message queued');
      // TODO: Implement message queue
    }
  }

  /**
   * Handle incoming WebSocket messages
   */
  private handleMessage(data: any): void {
    const { type, payload } = data;

    switch (type) {
      case 'connected':
        this.sessionId = payload.session_id;
        this.emit('session_established', payload);
        break;

      case 'init_complete':
        this.emit('init_complete', payload);
        break;

      case 'task_update':
        this.emit('task_update', payload);
        break;

      case 'conversation':
        this.emit('message', {
          role: payload.role,
          content: payload.content
        });
        break;

      case 'thinking':
        if (typeof payload === 'string') {
          this.emit('thinking_update', { summary: payload });
        } else {
          const { summary, steps } = payload;
          this.emit('thinking_update', { summary, steps });
        }
        break;

      case 'tool_event':
        this.emit('tool_event', payload);
        break;

      case 'feedback':
        this.emit('feedback', payload);
        break;

      case 'context_update':
        this.emit('context_update', payload);
        break;

      case 'todo_update':
        this.emit('todo_update', payload);
        break;

      case 'clear_conversation':
        this.emit('clear_conversation');
        break;

      case 'export_complete':
        this.emit('export_complete', payload);
        break;

      default:
        this.emit(type, payload);
    }
  }

  /**
   * Attempt to reconnect WebSocket
   */
  private attemptReconnect(): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`Reconnect attempt ${this.reconnectAttempts}`);

      setTimeout(() => {
        this.connect().catch(console.error);
      }, this.reconnectDelay * this.reconnectAttempts);
    }
  }

  /**
   * Send chat message via HTTP endpoint with streaming
   */
  async sendChatMessage(query: string): Promise<void> {
    const response = await fetch(`${this.baseUrl}/api/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        query,
        session_id: this.sessionId
      })
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const reader = response.body?.getReader();
    const decoder = new TextDecoder();

    if (!reader) {
      throw new Error('No response body');
    }

    let buffer = '';

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        // Process complete lines
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.trim() && line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              this.handleStreamData(data);
            } catch (error) {
              console.error('Error parsing stream data:', error);
            }d
          }
        }
      }
    } finally {
      reader.releaseLock();
    }
  }

  /**
   * Handle streaming data
   */
  private handleStreamData(data: any): void {
    switch (data.type) {
      case 'start':
        this.sessionId = data.session_id;
        this.emit('stream_start');
        break;

      case 'token':
        this.emit('stream_token', data.token);
        break;

      case 'thinking_update':
        if (typeof data === 'string') {
          this.emit('thinking_update', { summary: data });
        } else {
          const { summary, steps } = data;
          this.emit('thinking_update', { summary, steps });
        }
        break;

      case 'tool_start':
        this.emit('tool_event', {
          tool: data.tool,
          status: 'running',
          timestamp: new Date().toISOString()
        });
        break;

      case 'tool_complete':
        this.emit('tool_event', {
          tool: data.tool,
          status: 'success',
          result: data.result,
          timestamp: new Date().toISOString()
        });
        break;

      case 'task_update':
        this.emit('task_update', {
          name: data.name,
          currentPhase: data.current_phase,
          totalPhases: data.total_phases,
          phaseName: data.phase_name
        });
        break;

      case 'done':
        this.emit('stream_complete');
        break;

      case 'error':
        this.emit('stream_error', data.message);
        break;
    }
  }

  /**
   * Send chat message via WebSocket
   */
  sendChatViaWebSocket(query: string): void {
    this.send('chat', { query });
  }

  /**
   * Send command
   */
  sendCommand(command: string): void {
    if (command.startsWith('/')) {
      this.send('command', { command });
    }
  }

  /**
   * Export conversation
   */
  exportConversation(format: 'md' | 'json' = 'md'): void {
    this.send('export', { format });
  }

  /**
   * Get system status
   */
  async getStatus(): Promise<any> {
    const response = await fetch(`${this.baseUrl}/api/status`);
    return response.json();
  }

  /**
   * Get settings
   */
  async getSettings(): Promise<any> {
    const response = await fetch(`${this.baseUrl}/api/settings`);
    return response.json();
  }

  /**
   * Get sessions
   */
  async getSessions(): Promise<any> {
    const response = await fetch(`${this.baseUrl}/api/sessions`);
    return response.json();
  }

  /**
   * Delete session
   */
  async deleteSession(sessionId: string): Promise<void> {
    await fetch(`${this.baseUrl}/api/sessions/${sessionId}`, {
      method: 'DELETE'
    });
  }

  /**
   * Event emitter methods
   */
  on(event: string, handler: Function): void {
    if (!this.eventHandlers.has(event)) {
      this.eventHandlers.set(event, []);
    }
    this.eventHandlers.get(event)?.push(handler);
  }

  off(event: string, handler: Function): void {
    const handlers = this.eventHandlers.get(event);
    if (handlers) {
      const index = handlers.indexOf(handler);
      if (index > -1) {
        handlers.splice(index, 1);
      }
    }
  }

  emit(event: string, data?: any): void {
    const handlers = this.eventHandlers.get(event);
    if (handlers) {
      handlers.forEach(handler => handler(data));
    }
  }

  /**
   * Disconnect WebSocket
   */
  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}

// Create singleton instance
export const apiService = new ApiService(
  import.meta.env.VITE_API_URL || 'http://localhost:8000'
);

// Export types for components
export type { ApiService };