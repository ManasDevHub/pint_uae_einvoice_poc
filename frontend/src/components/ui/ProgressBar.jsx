export default function ProgressBar({ progress, variant = 'primary' }) {
  const bgClasses = {
    primary: "bg-[#1a6fcf]",
    success: "bg-[#22c55e]",
    danger: "bg-[#e53e3e]",
    warning: "bg-[#d97706]"
  }

  const p = Math.max(0, Math.min(100, progress))

  return (
    <div className="w-full bg-[#e3eaf7] rounded-full h-2.5 overflow-hidden">
      <div 
        className={`${bgClasses[variant]} h-2.5 rounded-full transition-all duration-500 ease-in-out`} 
        style={{ width: `${p}%` }}
      ></div>
    </div>
  )
}
