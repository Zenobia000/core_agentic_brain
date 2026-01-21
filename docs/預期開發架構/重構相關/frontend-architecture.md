# 🌐 前端架構設計 - React + TypeScript

## 🎯 架構概覽

從 **Vanilla JavaScript** 重構為 **React + TypeScript** 現代前端應用

### 技術棧
- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite
- **State Management**: Zustand
- **Styling**: TailwindCSS + Radix UI
- **WebSocket**: Socket.IO Client
- **Testing**: Vitest + React Testing Library

---

## 📁 前端目錄結構

```
frontend/
├── public/                     # 靜態資源
│   ├── favicon.ico
│   └── manifest.json
├── src/
│   ├── components/            # UI 組件
│   │   ├── ui/               # 基礎 UI 組件
│   │   │   ├── Button.tsx
│   │   │   ├── Input.tsx
│   │   │   ├── Progress.tsx
│   │   │   └── Card.tsx
│   │   ├── layout/           # 版面組件
│   │   │   ├── Header.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   └── MainLayout.tsx
│   │   ├── chat/             # 聊天相關組件
│   │   │   ├── ChatInterface.tsx
│   │   │   ├── MessageBubble.tsx
│   │   │   └── InputArea.tsx
│   │   ├── monitoring/       # 監控組件
│   │   │   ├── TokenMeter.tsx
│   │   │   ├── SystemStatus.tsx
│   │   │   └── ToolStatus.tsx
│   │   ├── workspace/        # 工作區組件
│   │   │   ├── FileExplorer.tsx
│   │   │   ├── FileViewer.tsx
│   │   │   └── WorkspacePanel.tsx
│   │   └── thinking/         # 思考過程組件
│   │       ├── ThinkingTimeline.tsx
│   │       ├── ThinkingStep.tsx
│   │       └── ThinkingPanel.tsx
│   ├── hooks/                # 自定義 Hooks
│   │   ├── useWebSocket.ts
│   │   ├── useTokenMeter.ts
│   │   ├── useChat.ts
│   │   └── useWorkspace.ts
│   ├── services/             # API 服務
│   │   ├── api.ts           # API 客戶端
│   │   ├── websocket.ts     # WebSocket 管理
│   │   └── types.ts         # API 類型定義
│   ├── stores/               # 狀態管理
│   │   ├── chatStore.ts     # 聊天狀態
│   │   ├── agentStore.ts    # Agent 狀態
│   │   ├── workspaceStore.ts # 工作區狀態
│   │   └── systemStore.ts   # 系統狀態
│   ├── types/                # TypeScript 類型
│   │   ├── chat.ts
│   │   ├── agent.ts
│   │   ├── workspace.ts
│   │   └── system.ts
│   ├── utils/                # 工具函數
│   │   ├── formatters.ts
│   │   ├── validators.ts
│   │   └── constants.ts
│   ├── App.tsx              # 主應用組件
│   ├── main.tsx             # 應用入口
│   └── index.css            # 全局樣式
├── package.json
├── tsconfig.json
├── vite.config.ts
└── tailwind.config.js
```

---

## 🏗️ 核心組件設計

### 1. 主應用架構

```typescript
// src/App.tsx
import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MainLayout } from '@/components/layout/MainLayout';
import { ChatProvider } from '@/contexts/ChatContext';
import { WebSocketProvider } from '@/contexts/WebSocketContext';
import { Toaster } from '@/components/ui/toast';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      retry: (failureCount, error) => {
        if (error?.status === 404) return false;
        return failureCount < 3;
      },
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <WebSocketProvider>
        <ChatProvider>
          <MainLayout />
          <Toaster />
        </ChatProvider>
      </WebSocketProvider>
    </QueryClientProvider>
  );
}

export default App;
```

### 2. 版面組件

```typescript
// src/components/layout/MainLayout.tsx
import React, { useState } from 'react';
import { Header } from './Header';
import { Sidebar } from './Sidebar';
import { ChatInterface } from '@/components/chat/ChatInterface';
import { WorkspacePanel } from '@/components/workspace/WorkspacePanel';
import { ThinkingPanel } from '@/components/thinking/ThinkingPanel';
import { SystemStatus } from '@/components/monitoring/SystemStatus';

export const MainLayout: React.FC = () => {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [activePanel, setActivePanel] = useState<'thinking' | 'workspace'>('thinking');

  return (
    <div className="flex h-screen bg-gray-900">
      {/* 側邊欄 */}
      <Sidebar
        open={sidebarOpen}
        onToggle={() => setSidebarOpen(!sidebarOpen)}
        activePanel={activePanel}
        onPanelChange={setActivePanel}
      />

      {/* 主要內容區 */}
      <div className="flex flex-1 overflow-hidden">
        {/* 左側面板 */}
        <div className="w-1/3 border-r border-gray-700 flex flex-col">
          <Header title={activePanel === 'thinking' ? 'AI 思考過程' : '工作區檔案'} />

          <div className="flex-1 overflow-hidden">
            {activePanel === 'thinking' ? (
              <ThinkingPanel />
            ) : (
              <WorkspacePanel />
            )}
          </div>

          {/* 系統狀態 */}
          <SystemStatus />
        </div>

        {/* 聊天界面 */}
        <div className="flex-1 flex flex-col">
          <Header title="對話" />
          <ChatInterface />
        </div>
      </div>
    </div>
  );
};
```

### 3. Token 監控組件

```typescript
// src/components/monitoring/TokenMeter.tsx
import React from 'react';
import { Progress } from '@/components/ui/Progress';
import { Card } from '@/components/ui/Card';
import { useTokenMeter } from '@/hooks/useTokenMeter';
import { AlertTriangle, TrendingUp } from 'lucide-react';

interface TokenMeterProps {
  sessionId?: string;
}

export const TokenMeter: React.FC<TokenMeterProps> = ({ sessionId }) => {
  const { tokenStats, isLoading } = useTokenMeter(sessionId);

  if (isLoading || !tokenStats) {
    return <div className="animate-pulse h-20 bg-gray-800 rounded" />;
  }

  const percentage = (tokenStats.used / tokenStats.budget) * 100;
  const isWarning = percentage > 80;
  const isCritical = percentage > 95;

  return (
    <Card className="p-4 bg-gray-800 border-gray-700">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm text-gray-400">Token 使用量</span>
        {isWarning && (
          <AlertTriangle
            className={`w-4 h-4 ${isCritical ? 'text-red-400' : 'text-yellow-400'}`}
          />
        )}
      </div>

      <Progress
        value={percentage}
        className="h-3 mb-2"
        indicatorClassName={
          isCritical
            ? 'bg-red-500'
            : isWarning
            ? 'bg-yellow-500'
            : 'bg-green-500'
        }
      />

      <div className="flex justify-between items-center text-xs text-gray-400">
        <span>
          {tokenStats.used.toLocaleString()} / {tokenStats.budget.toLocaleString()}
        </span>
        {tokenStats.optimizations > 0 && (
          <span className="flex items-center text-blue-400">
            <TrendingUp className="w-3 h-3 mr-1" />
            節省 {tokenStats.saved.toLocaleString()}
          </span>
        )}
      </div>

      {tokenStats.cost && (
        <div className="mt-2 text-xs text-gray-500">
          預估成本: ${tokenStats.cost.toFixed(4)}
        </div>
      )}
    </Card>
  );
};
```

### 4. 聊天界面組件

```typescript
// src/components/chat/ChatInterface.tsx
import React, { useState, useRef, useEffect } from 'react';
import { useChatStore } from '@/stores/chatStore';
import { useWebSocket } from '@/hooks/useWebSocket';
import { MessageBubble } from './MessageBubble';
import { InputArea } from './InputArea';
import { TokenMeter } from '@/components/monitoring/TokenMeter';
import { ScrollArea } from '@/components/ui/ScrollArea';

export const ChatInterface: React.FC = () => {
  const { messages, currentSession, sendMessage } = useChatStore();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // WebSocket 連接
  useWebSocket(currentSession?.id);

  // 自動滾動到最新訊息
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSendMessage = async (content: string, taskType?: string) => {
    if (!content.trim()) return;

    try {
      await sendMessage(content, taskType);
    } catch (error) {
      console.error('發送訊息失敗:', error);
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Token 監控 */}
      {currentSession && (
        <div className="p-4 border-b border-gray-700">
          <TokenMeter sessionId={currentSession.id} />
        </div>
      )}

      {/* 訊息列表 */}
      <ScrollArea className="flex-1 p-4">
        <div className="space-y-4">
          {messages.map((message) => (
            <MessageBubble
              key={message.id}
              message={message}
            />
          ))}
          <div ref={messagesEndRef} />
        </div>
      </ScrollArea>

      {/* 輸入區域 */}
      <InputArea
        onSend={handleSendMessage}
        disabled={currentSession?.status === 'processing'}
      />
    </div>
  );
};
```

### 5. WebSocket Hook

```typescript
// src/hooks/useWebSocket.ts
import { useEffect, useRef } from 'react';
import { io, Socket } from 'socket.io-client';
import { useChatStore } from '@/stores/chatStore';
import { useAgentStore } from '@/stores/agentStore';
import { useSystemStore } from '@/stores/systemStore';

export const useWebSocket = (sessionId?: string) => {
  const socketRef = useRef<Socket | null>(null);
  const { addMessage, updateSessionStatus } = useChatStore();
  const { addThinkingStep, updateTokenStats } = useAgentStore();
  const { updateSystemHealth } = useSystemStore();

  useEffect(() => {
    if (!sessionId) return;

    // 建立 WebSocket 連接
    const socket = io(`ws://localhost:8000/ws/${sessionId}`, {
      transports: ['websocket'],
      autoConnect: true,
    });

    socketRef.current = socket;

    // 事件監聽
    socket.on('connect', () => {
      console.log('WebSocket 已連接');
    });

    socket.on('disconnect', () => {
      console.log('WebSocket 已斷線');
    });

    // 聊天訊息
    socket.on('message', (data) => {
      addMessage({
        id: data.id,
        content: data.content,
        role: data.role,
        timestamp: new Date(data.timestamp),
      });
    });

    // 思考步驟
    socket.on('thinking_step', (data) => {
      addThinkingStep(sessionId, {
        id: data.id,
        content: data.content,
        timestamp: new Date(data.timestamp),
        type: data.type,
      });
    });

    // Token 使用統計
    socket.on('token_usage', (data) => {
      updateTokenStats(sessionId, data.stats);
    });

    // 會話狀態更新
    socket.on('session_status', (data) => {
      updateSessionStatus(sessionId, data.status);
    });

    // 系統健康狀態
    socket.on('system_health', (data) => {
      updateSystemHealth(data);
    });

    // 錯誤處理
    socket.on('error', (error) => {
      console.error('WebSocket 錯誤:', error);
    });

    return () => {
      socket.disconnect();
      socketRef.current = null;
    };
  }, [sessionId]);

  return {
    socket: socketRef.current,
    isConnected: socketRef.current?.connected ?? false,
  };
};
```

---

## 🗄️ 狀態管理架構

### Chat Store
```typescript
// src/stores/chatStore.ts
import { create } from 'zustand';
import { subscribeWithSelector } from 'zustand/middleware';
import { chatAPI } from '@/services/api';

export interface Message {
  id: string;
  content: string;
  role: 'user' | 'assistant' | 'system';
  timestamp: Date;
  metadata?: {
    tokenUsage?: number;
    executionTime?: number;
  };
}

export interface Session {
  id: string;
  status: 'pending' | 'processing' | 'completed' | 'error';
  taskType: string;
  createdAt: Date;
}

interface ChatState {
  // 狀態
  messages: Message[];
  currentSession: Session | null;
  isLoading: boolean;

  // 動作
  sendMessage: (content: string, taskType?: string) => Promise<void>;
  createSession: (prompt: string, taskType?: string) => Promise<Session>;
  updateSessionStatus: (sessionId: string, status: Session['status']) => void;
  addMessage: (message: Message) => void;
  clearMessages: () => void;
}

export const useChatStore = create<ChatState>()(
  subscribeWithSelector((set, get) => ({
    // 初始狀態
    messages: [],
    currentSession: null,
    isLoading: false,

    // 發送訊息
    sendMessage: async (content: string, taskType = 'general') => {
      set({ isLoading: true });

      try {
        // 添加用戶訊息
        const userMessage: Message = {
          id: crypto.randomUUID(),
          content,
          role: 'user',
          timestamp: new Date(),
        };

        get().addMessage(userMessage);

        // 創建或使用現有會話
        let session = get().currentSession;
        if (!session) {
          session = await get().createSession(content, taskType);
        } else {
          // 發送到現有會話
          await chatAPI.sendToSession(session.id, content);
        }

      } catch (error) {
        console.error('發送訊息失敗:', error);
        throw error;
      } finally {
        set({ isLoading: false });
      }
    },

    // 創建會話
    createSession: async (prompt: string, taskType = 'general') => {
      const response = await chatAPI.createSession({
        prompt,
        task_type: taskType,
      });

      const session: Session = {
        id: response.session_id,
        status: 'pending',
        taskType,
        createdAt: new Date(),
      };

      set({ currentSession: session });
      return session;
    },

    // 更新會話狀態
    updateSessionStatus: (sessionId: string, status: Session['status']) => {
      const { currentSession } = get();
      if (currentSession?.id === sessionId) {
        set({
          currentSession: { ...currentSession, status },
        });
      }
    },

    // 添加訊息
    addMessage: (message: Message) => {
      set(state => ({
        messages: [...state.messages, message],
      }));
    },

    // 清除訊息
    clearMessages: () => {
      set({ messages: [], currentSession: null });
    },
  }))
);
```

### Agent Store
```typescript
// src/stores/agentStore.ts
import { create } from 'zustand';

export interface ThinkingStep {
  id: string;
  content: string;
  timestamp: Date;
  type: 'thinking' | 'action' | 'observation' | 'communication';
  metadata?: {
    tool?: string;
    executionTime?: number;
  };
}

export interface TokenStats {
  used: number;
  budget: number;
  remaining: number;
  optimizations: number;
  saved: number;
  cost?: number;
}

export interface ToolStatus {
  name: string;
  status: 'healthy' | 'degraded' | 'circuit_open';
  lastError?: string;
  errorCount: number;
}

interface AgentState {
  // 狀態
  thinkingSteps: Record<string, ThinkingStep[]>; // sessionId -> steps
  tokenStats: Record<string, TokenStats>; // sessionId -> stats
  toolStatuses: ToolStatus[];

  // 動作
  addThinkingStep: (sessionId: string, step: ThinkingStep) => void;
  updateTokenStats: (sessionId: string, stats: TokenStats) => void;
  updateToolStatus: (tool: string, status: ToolStatus['status'], error?: string) => void;
  clearSession: (sessionId: string) => void;
}

export const useAgentStore = create<AgentState>((set, get) => ({
  // 初始狀態
  thinkingSteps: {},
  tokenStats: {},
  toolStatuses: [
    { name: 'browser_use', status: 'healthy', errorCount: 0 },
    { name: 'python_execute', status: 'healthy', errorCount: 0 },
    { name: 'web_search', status: 'healthy', errorCount: 0 },
  ],

  // 添加思考步驟
  addThinkingStep: (sessionId: string, step: ThinkingStep) => {
    set(state => ({
      thinkingSteps: {
        ...state.thinkingSteps,
        [sessionId]: [...(state.thinkingSteps[sessionId] || []), step],
      },
    }));
  },

  // 更新 Token 統計
  updateTokenStats: (sessionId: string, stats: TokenStats) => {
    set(state => ({
      tokenStats: {
        ...state.tokenStats,
        [sessionId]: stats,
      },
    }));
  },

  // 更新工具狀態
  updateToolStatus: (tool: string, status: ToolStatus['status'], error?: string) => {
    set(state => ({
      toolStatuses: state.toolStatuses.map(t =>
        t.name === tool
          ? {
              ...t,
              status,
              lastError: error,
              errorCount: status === 'circuit_open' ? t.errorCount + 1 : t.errorCount,
            }
          : t
      ),
    }));
  },

  // 清除會話資料
  clearSession: (sessionId: string) => {
    set(state => {
      const { [sessionId]: _, ...remainingSteps } = state.thinkingSteps;
      const { [sessionId]: __, ...remainingStats } = state.tokenStats;

      return {
        thinkingSteps: remainingSteps,
        tokenStats: remainingStats,
      };
    });
  },
}));
```

---

## 🎨 樣式與設計系統

### TailwindCSS 配置
```javascript
// tailwind.config.js
/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        border: 'hsl(var(--border))',
        input: 'hsl(var(--input))',
        ring: 'hsl(var(--ring))',
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        primary: {
          DEFAULT: 'hsl(var(--primary))',
          foreground: 'hsl(var(--primary-foreground))',
        },
        secondary: {
          DEFAULT: 'hsl(var(--secondary))',
          foreground: 'hsl(var(--secondary-foreground))',
        },
        destructive: {
          DEFAULT: 'hsl(var(--destructive))',
          foreground: 'hsl(var(--destructive-foreground))',
        },
        muted: {
          DEFAULT: 'hsl(var(--muted))',
          foreground: 'hsl(var(--muted-foreground))',
        },
        accent: {
          DEFAULT: 'hsl(var(--accent))',
          foreground: 'hsl(var(--accent-foreground))',
        },
        popover: {
          DEFAULT: 'hsl(var(--popover))',
          foreground: 'hsl(var(--popover-foreground))',
        },
        card: {
          DEFAULT: 'hsl(var(--card))',
          foreground: 'hsl(var(--card-foreground))',
        },
      },
      borderRadius: {
        lg: 'var(--radius)',
        md: 'calc(var(--radius) - 2px)',
        sm: 'calc(var(--radius) - 4px)',
      },
      keyframes: {
        'accordion-down': {
          from: { height: 0 },
          to: { height: 'var(--radix-accordion-content-height)' },
        },
        'accordion-up': {
          from: { height: 'var(--radix-accordion-content-height)' },
          to: { height: 0 },
        },
      },
      animation: {
        'accordion-down': 'accordion-down 0.2s ease-out',
        'accordion-up': 'accordion-up 0.2s ease-out',
      },
    },
  },
  plugins: [require('tailwindcss-animate')],
};
```

### CSS 變數定義
```css
/* src/index.css */
@import 'tailwindcss/base';
@import 'tailwindcss/components';
@import 'tailwindcss/utilities';

@layer base {
  :root {
    --background: 222 84% 5%;
    --foreground: 210 40% 98%;
    --card: 222 84% 5%;
    --card-foreground: 210 40% 98%;
    --popover: 222 84% 5%;
    --popover-foreground: 210 40% 98%;
    --primary: 210 40% 98%;
    --primary-foreground: 222 84% 5%;
    --secondary: 217 33% 17%;
    --secondary-foreground: 210 40% 98%;
    --muted: 217 33% 17%;
    --muted-foreground: 215 20% 65%;
    --accent: 217 33% 17%;
    --accent-foreground: 210 40% 98%;
    --destructive: 0 62% 30%;
    --destructive-foreground: 210 40% 98%;
    --border: 217 33% 17%;
    --input: 217 33% 17%;
    --ring: 212 93% 72%;
    --radius: 0.5rem;
  }
}

@layer base {
  * {
    @apply border-border;
  }
  body {
    @apply bg-background text-foreground;
  }
}

/* 自定義樣式 */
.glass-effect {
  @apply bg-white/5 backdrop-blur-sm border border-white/10;
}

.token-meter-warning {
  @apply bg-gradient-to-r from-yellow-500 to-orange-500;
}

.token-meter-critical {
  @apply bg-gradient-to-r from-red-500 to-pink-500;
}
```

---

## 🧪 測試策略

### Component 測試
```typescript
// src/components/monitoring/__tests__/TokenMeter.test.tsx
import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { TokenMeter } from '../TokenMeter';
import * as tokenHook from '@/hooks/useTokenMeter';

// Mock hook
vi.mock('@/hooks/useTokenMeter');

describe('TokenMeter', () => {
  it('should display token usage correctly', () => {
    vi.mocked(tokenHook.useTokenMeter).mockReturnValue({
      tokenStats: {
        used: 1000,
        budget: 4000,
        remaining: 3000,
        optimizations: 2,
        saved: 500,
        cost: 0.032,
      },
      isLoading: false,
    });

    render(<TokenMeter sessionId="test-session" />);

    expect(screen.getByText('1,000 / 4,000')).toBeInTheDocument();
    expect(screen.getByText('節省 500')).toBeInTheDocument();
    expect(screen.getByText('$0.0320')).toBeInTheDocument();
  });

  it('should show warning when usage exceeds 80%', () => {
    vi.mocked(tokenHook.useTokenMeter).mockReturnValue({
      tokenStats: {
        used: 3500,
        budget: 4000,
        remaining: 500,
        optimizations: 0,
        saved: 0,
      },
      isLoading: false,
    });

    render(<TokenMeter sessionId="test-session" />);

    expect(screen.getByLabelText(/warning/i)).toBeInTheDocument();
  });
});
```

### Hook 測試
```typescript
// src/hooks/__tests__/useWebSocket.test.ts
import { renderHook } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { useWebSocket } from '../useWebSocket';

// Mock Socket.IO
vi.mock('socket.io-client', () => ({
  io: vi.fn(() => ({
    on: vi.fn(),
    emit: vi.fn(),
    disconnect: vi.fn(),
    connected: true,
  })),
}));

describe('useWebSocket', () => {
  it('should establish connection with session ID', () => {
    const { result } = renderHook(() => useWebSocket('test-session'));

    expect(result.current.isConnected).toBe(true);
  });

  it('should not connect without session ID', () => {
    const { result } = renderHook(() => useWebSocket());

    expect(result.current.socket).toBeNull();
  });
});
```

---

## 🚀 部署配置

### Vite 配置
```typescript
// vite.config.ts
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          ui: ['@radix-ui/react-progress', 'lucide-react'],
        },
      },
    },
  },
});
```

### 生產 Dockerfile
```dockerfile
# frontend/Dockerfile
FROM node:18-alpine as builder

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

---

## 📊 效能優化

### 程式碼分割
```typescript
// 懶載入路由組件
const ChatInterface = lazy(() => import('@/components/chat/ChatInterface'));
const WorkspacePanel = lazy(() => import('@/components/workspace/WorkspacePanel'));

// 使用 React.memo 優化重渲染
export const TokenMeter = React.memo<TokenMeterProps>(({ sessionId }) => {
  // Component implementation
});

// 使用 useMemo 緩存計算結果
const expensiveValue = useMemo(() => {
  return computeExpensiveValue(props);
}, [dependency]);
```

### 狀態優化
```typescript
// 使用 subscribeWithSelector 避免不必要的重渲染
export const useChatMessages = (sessionId?: string) => {
  return useChatStore(
    useCallback(
      (state) => state.messages.filter(msg => msg.sessionId === sessionId),
      [sessionId]
    )
  );
};
```

---

## ✅ 前端重構檢查清單

### 🏗️ 基礎架構
- [ ] React + TypeScript 專案設置
- [ ] Vite 建構工具配置
- [ ] TailwindCSS 樣式系統
- [ ] 元件庫整合 (Radix UI)

### 🔧 開發工具
- [ ] ESLint + Prettier 配置
- [ ] TypeScript 嚴格模式
- [ ] Vitest 測試框架
- [ ] React Testing Library

### 📱 UI 組件
- [ ] 基礎 UI 組件庫
- [ ] 聊天界面組件
- [ ] Token 監控組件
- [ ] 工作區管理組件
- [ ] 思考過程顯示組件

### 🗄️ 狀態管理
- [ ] Zustand 狀態管理
- [ ] WebSocket 整合
- [ ] API 客戶端設置
- [ ] 錯誤處理機制

### 🧪 測試
- [ ] 單元測試覆蓋率 80%+
- [ ] 組件測試
- [ ] Hook 測試
- [ ] E2E 測試設置

### 🚀 部署
- [ ] Docker 容器化
- [ ] Nginx 配置
- [ ] 程式碼分割
- [ ] 效能優化

**預期完成時間**: 2-3 週
**關鍵里程碑**: 現代化前端界面，與新後端 API 完整整合