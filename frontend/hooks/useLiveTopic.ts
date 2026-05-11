"use client";

import { useEffect, useRef, useState } from "react";

import { getWsBase } from "@/lib/env";
import type { RealtimeEvent } from "@/types";

type Options = {
  enabled?: boolean;
  onEvent?: (evt: RealtimeEvent) => void;
};

export function useLiveTopic(topic: string | null | undefined, opts: Options = {}) {
  const { enabled = true, onEvent } = opts;
  const [events, setEvents] = useState<RealtimeEvent[]>([]);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const onEventRef = useRef(onEvent);
  onEventRef.current = onEvent;

  useEffect(() => {
    if (!topic || !enabled) return;
    let stopped = false;
    let retry = 0;
    let retryTimer: number | undefined;

    const connect = () => {
      if (stopped) return;
      const url = `${getWsBase()}/${encodeURIComponent(topic)}`;
      try {
        const ws = new WebSocket(url);
        wsRef.current = ws;
        ws.onopen = () => {
          setConnected(true);
          retry = 0;
        };
        ws.onmessage = (e) => {
          try {
            const data = JSON.parse(e.data) as RealtimeEvent;
            setEvents((prev) => {
              const next = [...prev, data];
              return next.length > 200 ? next.slice(next.length - 200) : next;
            });
            onEventRef.current?.(data);
          } catch {
            /* ignore */
          }
        };
        ws.onerror = () => {
          // Will fire onclose immediately after.
        };
        ws.onclose = () => {
          setConnected(false);
          if (stopped) return;
          retry += 1;
          const delay = Math.min(1000 * 2 ** retry, 8000);
          retryTimer = window.setTimeout(connect, delay);
        };
      } catch {
        retry += 1;
        retryTimer = window.setTimeout(connect, Math.min(1000 * 2 ** retry, 8000));
      }
    };

    connect();
    return () => {
      stopped = true;
      if (retryTimer) window.clearTimeout(retryTimer);
      wsRef.current?.close();
    };
  }, [topic, enabled]);

  return { events, connected, clear: () => setEvents([]) };
}
