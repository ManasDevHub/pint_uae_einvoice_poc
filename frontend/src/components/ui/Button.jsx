export default function Button({ children, variant = 'primary', className = "", disabled, ...props }) {
  const base = "inline-flex items-center justify-center font-medium rounded-lg transition-colors px-4 py-2 text-sm disabled:opacity-50 disabled:cursor-not-allowed"
  const variants = {
    primary: "bg-[#1a6fcf] text-white hover:bg-[#155db0]",
    ghost: "border border-[#e3eaf7] bg-transparent text-[#1a2340] hover:bg-[#f8faff]",
    danger: "bg-[#e53e3e] text-white hover:bg-[#c53030]",
    text: "text-[#1a6fcf] hover:text-[#155db0] hover:bg-[#e8f1ff] px-2"
  }

  return (
    <button disabled={disabled} className={`${base} ${variants[variant]} ${className}`} {...props}>
      {children}
    </button>
  )
}
