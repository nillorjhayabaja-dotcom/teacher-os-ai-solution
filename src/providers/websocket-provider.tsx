// ============================================================
// TeacherOS — WebSocket Provider
// ============================================================
import { useEffect, useRef, createContext, useContext, useCallback, type ReactNode } from "react";
import { useAuthStore } from "@/stores/auth-store";
import { useNotificationStore } from "@/stores/notification-store";
import type { Notification } from "@/types";

type WebSocketContextValue = {
  send: (message: string) => void;
  isConnected: boolean;
};

const WebSocketContext = createContext<WebSocketContextValue>({
  send: () => {},
  isConnected: false,
});

export function useWebSocket() {
  return useContext(WebSocketContext);
}

const RECONNECT_DELAYS = [1000, 2000, 4000, 8000, 16000, 30000];

export function WebSocketProvider({ children }: { children: ReactNode }) {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectRef = useRef(0);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout>>(undefined);
  const isConnectedRef = useRef(false);

  const accessToken = useAuthStore((s) => s.accessToken);
  const addNotification = useNotificationStore((s) => s.addNotification);

  const connect = useCallback(() => {
    if (!accessToken) return;

    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${window.location.host}/ws?token=${accessToken}`;

    try {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        isConnectedRef.current = true;
        reconnectRef.current = 0;
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === "notification") {
            addNotification(data.payload as Notification);
          }
        } catch {
          // Ignore non-JSON messages
        }
      };

      ws.onclose = () => {
        isConnectedRef.current = false;
        wsRef.current = null;

        // Auto-reconnect
        const delay =
          RECONNECT_DELAYS[Math.min(reconnectRef.current, RECONNECT_DELAYS.length - 1)];
        reconnectRef.current++;
        reconnectTimerRef.current = setTimeout(connect, delay);
      };

      ws.onerror = () => {
        ws.close();
      };
    } catch {
      // Connection failed - will retry via onclose
    }
  }, [accessToken, addNotification]);

  useEffect(() => {
    connect();
    return () => {
      clearTimeout(reconnectTimerRef.current);
      wsRef.current?.close();
    };
  }, [connect]);

  const send = useCallback((message: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(message);
    }
  }, []);

  return (
    <WebSocketContext.Provider value={{ send, isConnected: isConnectedRef.current }}>
      {children}
    </WebSocketContext.Provider>
  );
}