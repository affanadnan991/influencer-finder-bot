"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import type { JobStatus } from "./api";

const WS_BASE = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000";

/**
 * Hook that connects to the WebSocket progress stream for a job.
 * Falls back to HTTP polling if WebSocket fails.
 */
export function useJobProgress(jobId: string | null) {
  const [status, setStatus] = useState<JobStatus | null>(null);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const fallbackRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Fallback: poll via HTTP if WS fails
  const startPolling = useCallback(
    (id: string) => {
      if (fallbackRef.current) return;
      const poll = async () => {
        try {
          const res = await fetch(
            `${WS_BASE.replace("ws://", "http://").replace("wss://", "https://")}/api/status/${id}`
          );
          if (res.ok) {
            const data = await res.json();
            setStatus(data);
            if (data.status === "completed" || data.status === "failed") {
              if (fallbackRef.current) {
                clearInterval(fallbackRef.current);
                fallbackRef.current = null;
              }
            }
          }
        } catch {
          // keep trying
        }
      };
      poll();
      fallbackRef.current = setInterval(poll, 2000);
    },
    []
  );

  useEffect(() => {
    if (!jobId) {
      setStatus(null);
      setConnected(false);
      return;
    }

    const ws = new WebSocket(`${WS_BASE}/ws/progress/${jobId}`);
    wsRef.current = ws;

    ws.onopen = () => {
      setConnected(true);
    };

    ws.onmessage = (event) => {
      try {
        const data: JobStatus = JSON.parse(event.data);
        setStatus(data);
      } catch {
        // ignore malformed messages
      }
    };

    ws.onerror = () => {
      // Fallback to polling
      setConnected(false);
      startPolling(jobId);
    };

    ws.onclose = () => {
      setConnected(false);
    };

    return () => {
      ws.close();
      wsRef.current = null;
      if (fallbackRef.current) {
        clearInterval(fallbackRef.current);
        fallbackRef.current = null;
      }
    };
  }, [jobId, startPolling]);

  return { status, connected };
}
