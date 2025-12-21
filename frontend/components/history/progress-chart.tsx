"use client";

import { SubjectProgress } from "@/lib/history/types";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

interface ProgressChartProps {
  data: SubjectProgress["trend"];
}

export function ProgressChart({ data }: ProgressChartProps) {
  // Format data for chart if needed, but the structure {date, score} works well.
  // We might want to format the date tick.

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-3 border border-border shadow-sm rounded-lg text-sm">
          <p className="font-medium text-zinc-900">{new Date(label).toLocaleDateString()}</p>
          <p className="text-zinc-500">
            Score: <span className="font-bold text-zinc-900">{payload[0].value}%</span>
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="h-[300px] w-full bg-white p-6 rounded-xl border border-border">
      <h3 className="text-lg font-bold text-zinc-900 mb-6">Performance Trend</h3>
      <div className="h-[200px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart
            data={data}
            margin={{ top: 5, right: 20, left: -20, bottom: 0 }}
          >
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E4E4E7" />
            <XAxis 
                dataKey="date" 
                tick={{ fontSize: 12, fill: "#71717A" }} 
                tickLine={false}
                axisLine={false}
                tickFormatter={(value) => new Date(value).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}
                dy={10}
            />
            <YAxis 
                tick={{ fontSize: 12, fill: "#71717A" }} 
                tickLine={false}
                axisLine={false}
                domain={[0, 100]}
                ticks={[0, 20, 40, 60, 80, 100]}
            />
            <Tooltip content={<CustomTooltip />} cursor={{ stroke: '#E4E4E7', strokeWidth: 2 }} />
            <Line
              type="monotone"
              dataKey="score"
              stroke="#52525B" // Zinc-600
              strokeWidth={2}
              dot={{ r: 4, fill: "#52525B", strokeWidth: 0 }}
              activeDot={{ r: 6, fill: "#18181B" }} // Zinc-900
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
