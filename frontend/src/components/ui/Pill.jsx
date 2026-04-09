export default function Pill({ children, variant = 'gray', className = "" }) {
  const variants = {
    green: "bg-[#f0fdf4] text-[#22c55e] border-[#bbf7d0]",
    red: "bg-[#fff5f5] text-[#e53e3e] border-[#fed7d7]",
    blue: "bg-[#e8f1ff] text-[#1a6fcf] border-[#bfdbfe]",
    teal: "bg-[#f0fdfa] text-[#0d9488] border-[#ccfbf1]",
    violet: "bg-[#f5f3ff] text-[#7c3aed] border-[#ddd6fe]",
    warning: "bg-[#fffbeb] text-[#e07b00] border-[#fde68a]",
    gray: "bg-[#f8faff] text-[#5a6a85] border-[#e3eaf7]"
  }

  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold border ${variants[variant] || variants.gray} ${className}`}>
      {children}
    </span>
  )
}
