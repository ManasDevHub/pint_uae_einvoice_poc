export default function Card({ children, className = "" }) {
  return (
    <div className={`bg-white border border-[#e3eaf7] rounded-xl shadow-sm ${className}`}>
      {children}
    </div>
  )
}
