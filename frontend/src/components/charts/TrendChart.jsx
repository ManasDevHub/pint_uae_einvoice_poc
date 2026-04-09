import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'

export default function TrendChart({ data }) {
  return (
    <ResponsiveContainer width="100%" height={200}>
      <LineChart data={data}>
        <XAxis dataKey="date" tick={{ fontSize: 11, fill: '#8899b0' }} axisLine={false} tickLine={false} />
        <YAxis domain={[0, 100]} tick={{ fontSize: 11, fill: '#8899b0' }} axisLine={false} tickLine={false} />
        <Tooltip formatter={(v) => [`${v}%`, 'Pass rate']} contentStyle={{ borderRadius: '8px', border: '1px solid #e3eaf7' }} />
        <Line type="monotone" dataKey="pass_rate" stroke="#1a6fcf" strokeWidth={3} dot={false} activeDot={{ r: 6 }} />
      </LineChart>
    </ResponsiveContainer>
  )
}
