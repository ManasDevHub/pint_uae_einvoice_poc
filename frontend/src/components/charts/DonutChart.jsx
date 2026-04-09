import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from 'recharts'

const COLORS = { FORMAT: '#7c3aed', CALCULATION: '#d97706', COMPLIANCE: '#1a6fcf' }

export default function DonutChart({ data }) {
  return (
    <ResponsiveContainer width="100%" height={220}>
      <PieChart>
        <Pie 
          data={data} 
          cx="50%" cy="50%" 
          innerRadius={60} 
          outerRadius={80} 
          dataKey="value"
          paddingAngle={2}
        >
          {data.map((entry) => <Cell key={entry.name} fill={COLORS[entry.name] || '#8899b0'} />)}
        </Pie>
        <Tooltip contentStyle={{ borderRadius: '8px', border: '1px solid #e3eaf7' }} />
        <Legend verticalAlign="bottom" height={36} iconType="circle" />
      </PieChart>
    </ResponsiveContainer>
  )
}
