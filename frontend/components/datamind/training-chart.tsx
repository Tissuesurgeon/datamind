"use client";

import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import type { TrainingHistoryPoint } from "@/types";

export function TrainingChart({
  data,
  height = 220,
}: {
  data: TrainingHistoryPoint[];
  height?: number;
}) {
  return (
    <div className="rounded-2xl border border-border-subtle bg-surface-1 p-4">
      <div className="mb-3 flex items-baseline justify-between">
        <h4 className="text-sm font-medium">Training loss</h4>
        <span className="font-mono text-xs text-text-muted">
          {data.length ? `step ${data[data.length - 1].step}` : "no data"}
        </span>
      </div>
      <ResponsiveContainer width="100%" height={height}>
        <AreaChart data={data} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
          <defs>
            <linearGradient id="loss" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#F5A524" stopOpacity={0.45} />
              <stop offset="100%" stopColor="#F5A524" stopOpacity={0.02} />
            </linearGradient>
          </defs>
          <XAxis
            dataKey="step"
            stroke="#666"
            fontSize={11}
            tickLine={false}
            axisLine={false}
          />
          <YAxis
            stroke="#666"
            fontSize={11}
            tickLine={false}
            axisLine={false}
            domain={[0, "auto"]}
          />
          <Tooltip
            contentStyle={{
              background: "rgba(17,17,20,0.95)",
              border: "1px solid rgba(255,255,255,0.08)",
              borderRadius: 8,
              fontSize: 12,
              color: "white",
            }}
            cursor={{ stroke: "rgba(255,255,255,0.12)", strokeWidth: 1 }}
          />
          <Area
            type="monotone"
            dataKey="loss"
            stroke="#F5A524"
            fill="url(#loss)"
            strokeWidth={2}
            isAnimationActive={false}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
