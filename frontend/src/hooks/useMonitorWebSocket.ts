import { useState, useEffect, useRef, useCallback } from "react";
import type {
  MonitorEvent,
  ConnectionStatus,
  MessageStats,
  WSMessage,
} from "@/types/monitor";

export interface UseMonitorWebSocketReturn {
  events: MonitorEvent[];
  connectionStatus: ConnectionStatus | null;
  stats: MessageStats | null;
  isConnected: boolean;
  clearHistory: () => void;
  resetStats: () => void;
}

const RECONNECT_DELAY = 3000;
const MAX_HISTORY = 100;

export const useMonitorWebSocket = (
  url?: string,
): UseMonitorWebSocketReturn => {
  const resolvedUrl =
    url ||
    (typeof window !== "undefined"
      ? `${window.location.protocol === "https:" ? "wss:" : "ws:"}//${window.location.host}/ws/monitor`
      : "ws://localhost:8080/ws/monitor");
  const [events, setEvents] = useState<MonitorEvent[]>([]);
  const [connectionStatus, setConnectionStatus] =
    useState<ConnectionStatus | null>(null);
  const [stats, setStats] = useState<MessageStats | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(
    null,
  );

  const clearReconnectTimer = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
  }, []);

  const connect = useCallback(() => {
    clearReconnectTimer();

    if (
      wsRef.current &&
      wsRef.current.readyState !== WebSocket.CLOSED &&
      wsRef.current.readyState !== WebSocket.CLOSING
    ) {
      return;
    }

    const ws = new WebSocket(resolvedUrl);

    ws.onopen = () => {
      console.log("[Monitor] WebSocket 已连接");
      setIsConnected(true);
    };

    ws.onmessage = (event) => {
      let message: WSMessage;

      try {
        message = JSON.parse(event.data) as WSMessage;
      } catch (error) {
        console.error("[Monitor] WebSocket 消息解析失败:", error);
        return;
      }

      if (message.type === "history") {
        setEvents(message.events);
      } else if (message.type === "stats") {
        setStats(message.data.stats);
        setConnectionStatus(message.data.connection_status);
      } else if (message.type === "event") {
        setEvents((prev) => [...prev, message.event].slice(-MAX_HISTORY));
      } else if (message.type === "ack") {
        console.log("[Monitor]", message.message);
      }
    };

    ws.onerror = (error) => {
      console.error("[Monitor] WebSocket 发生错误:", error);
    };

    ws.onclose = () => {
      console.log(
        `[Monitor] WebSocket 已断开，将在 ${RECONNECT_DELAY / 1000} 秒后重连`,
      );
      setIsConnected(false);
      setConnectionStatus(null);
      setStats(null);
      wsRef.current = null;

      reconnectTimeoutRef.current = setTimeout(() => {
        connect();
      }, RECONNECT_DELAY);
    };

    wsRef.current = ws;
  }, [clearReconnectTimer, resolvedUrl]);

  useEffect(() => {
    connect();

    return () => {
      clearReconnectTimer();

      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [connect, clearReconnectTimer]);

  const clearHistory = useCallback(() => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: "clear_history" }));
      setEvents([]);
    }
  }, []);

  const resetStats = useCallback(() => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: "reset_stats" }));
    }
  }, []);

  return {
    events,
    connectionStatus,
    stats,
    isConnected,
    clearHistory,
    resetStats,
  };
};
