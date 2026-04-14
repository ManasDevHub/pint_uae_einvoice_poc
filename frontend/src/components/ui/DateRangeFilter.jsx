import { useState, useEffect } from 'react'

export default function DateRangeFilter({ onChange, initialStart = '', initialEnd = '' }) {
  const [start, setStart] = useState(initialStart)
  const [end, setEnd] = useState(initialEnd)

  // Sync state if props change (e.g. user resets)
  useEffect(() => {
    setStart(initialStart)
    setEnd(initialEnd)
  }, [initialStart, initialEnd])

  const handleApply = () => {
    if (start && end && start > end) {
      alert("Start date cannot be after end date.")
      return
    }
    onChange({ start, end })
  }

  const handleClear = () => {
    setStart('')
    setEnd('')
    onChange({ start: '', end: '' })
  }

  return (
    <div className="flex items-center gap-2 bg-[#f8faff] border border-[#e3eaf7] p-2 rounded-xl flex-wrap">
      <div className="flex items-center gap-2">
        <span className="text-xs font-semibold text-[#8899b0] uppercase tracking-wider ml-1">From</span>
        <input 
          type="date" 
          value={start}
          onChange={(e) => setStart(e.target.value)}
          max={end || undefined}
          className="px-2 py-1.5 text-sm border border-[#e3eaf7] rounded-md focus:outline-none focus:border-[#1a6fcf] text-[#1a2340] bg-white"
        />
      </div>
      <div className="flex items-center gap-2">
        <span className="text-xs font-semibold text-[#8899b0] uppercase tracking-wider">To</span>
        <input 
          type="date" 
          value={end}
          onChange={(e) => setEnd(e.target.value)}
          min={start || undefined}
          className="px-2 py-1.5 text-sm border border-[#e3eaf7] rounded-md focus:outline-none focus:border-[#1a6fcf] text-[#1a2340] bg-white"
        />
      </div>
      <div className="flex items-center gap-1 ml-1">
        <button 
          onClick={handleApply}
          disabled={!start || !end}
          className="px-3 py-1.5 bg-[#1a6fcf] text-white text-xs font-semibold rounded-md hover:bg-[#1560b8] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Apply
        </button>
        <button 
          onClick={handleClear}
          className="px-3 py-1.5 bg-white text-[#5a6a85] text-xs font-semibold border border-[#e3eaf7] rounded-md hover:bg-[#f0f4ff] hover:text-[#1a2340] transition-colors"
        >
          Clear
        </button>
      </div>
    </div>
  )
}
