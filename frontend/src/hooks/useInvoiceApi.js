import { useState, useCallback } from 'react'
import { API_BASE } from '../constants/api'

function parseAndDescribeJson(raw) {
  try {
    return { data: JSON.parse(raw), error: null }
  } catch (err) {
    const msg = err.message
    let friendly = msg

    if (msg.includes('Unexpected token')) {
      const tokenMatch = msg.match(/token '(.*?)'/)
      const token = tokenMatch ? tokenMatch[1] : null
      
      const positionMatch = msg.match(/position (\d+)/)
      
      if (token === ',' && msg.includes('is not valid JSON')) {
          friendly = "Syntax Error: Missing value before comma. Check your numbers and trailing commas."
      } else if (positionMatch) {
          const pos = parseInt(positionMatch[1], 10)
          const context = raw.substring(Math.max(0, pos - 15), Math.min(raw.length, pos + 15))
          friendly = `Syntax Error near: "...${context}..."`
      }
    }
    return { data: null, error: friendly }
  }
}


async function apiFetch(url, payload, apiKey) {
  const headers = { 
    'Content-Type': 'application/json',
    'ngrok-skip-browser-warning': 'true'
  }
  if (apiKey) headers['X-API-Key'] = apiKey

  const res = await fetch(API_BASE + url, {
    method: 'POST',
    headers,
    body: JSON.stringify(payload)
  })

  if (!res.ok && res.status !== 422) {
    throw new Error(`HTTP ${res.status}: ${res.statusText}`)
  }
  return res.json()
}

export function useInvoiceApi() {
  const [stages, setStages] = useState({
    validate: 'idle',   // idle | loading | success | error
    asp:      'idle',
    submit:   'idle',
  })
  const [results, setResults] = useState({
    validate: null,
    asp:      null,
    submit:   null,
  })
  const [error, setError] = useState(null)
  const [isRunning, setIsRunning] = useState(false)

  const setStage = (key, val) => setStages(s => ({ ...s, [key]: val }))
  const setResult = (key, val) => setResults(r => ({ ...r, [key]: val }))

  const reset = useCallback(() => {
    setStages({ validate: 'idle', asp: 'idle', submit: 'idle' })
    setResults({ validate: null, asp: null, submit: null })
    setError(null)
    setIsRunning(false)
  }, [])

  const runPipeline = useCallback(async (payload, apiKey) => {
    reset()
    setIsRunning(true)
    setError(null)

    let parsed
    if (typeof payload === 'string') {
      const { data, error: parseErr } = parseAndDescribeJson(payload)
      if (parseErr) {
        setResult('validate', {
          status: "FAILURE",
          report: {
            invoice_number: "N/A",
            is_valid: false,
            total_errors: 1,
          errors: [{
            field: "JSON Structure",
            error: parseErr,
            severity: "HIGH",
            category: "FORMAT"
          }],
          metrics: { total_checks: 1, passed_checks: 0, failed_checks: 1, pass_percentage: 0.0 },
          timestamp: new Date().toISOString(),
          field_results: [{
            group: "System Check",
            fields: [{
              field: "JSON Structure",
              label: "JSON Structure",
              value: "Malformed JSON",
              status: "fail",
              pint_ref: "FORMAT",
              error: parseErr
            }]
          }]
        }
      })
      setIsRunning(false)
      return
    }
    parsed = data
  } else {
    parsed = payload
  }

    // Stage 1: Internal validate
    setStage('validate', 'loading')
    try {
      const r = await apiFetch('/api/v1/validate-invoice', parsed, apiKey)
      setResult('validate', r)
      
      const isValid = r?.report?.is_valid
      if (isValid === false) {
        // ⛔ STOP HERE — do not call ASP or FTA
        setStage('validate', 'success') // The API call itself was successful
        setStage('asp', 'idle')
        setStage('submit', 'idle')
        setIsRunning(false)
        return
      }

      setStage('validate', 'success')
    } catch (e) {
      setStage('validate', 'error')
      setError(e.message.includes('Failed to fetch')
        ? 'Cannot reach backend — is uvicorn running on port 8000?'
        : e.message)
      setIsRunning(false)
      return
    }

    // Stage 2: ASP mock validate
    setStage('asp', 'loading')
    try {
      const r = await apiFetch('/asp/v1/validate', parsed, apiKey)
      setResult('asp', r)
      setStage('asp', r?.asp_status === 'ACCEPTED' ? 'success' : 'error')
    } catch (e) {
      setStage('asp', 'error')
      setError(e.message)
      setIsRunning(false)
      return
    }

    // Stage 3: ASP mock submit (FTA)
    setStage('submit', 'loading')
    try {
      const r = await apiFetch('/asp/v1/submit', parsed, apiKey)
      setResult('submit', r)
      setStage('submit', r?.asp_status === 'CLEARED' ? 'success' : 'error')
    } catch (e) {
      setStage('submit', 'error')
      setError(e.message)
    }

    setIsRunning(false)
  }, [reset])

  const runSingle = useCallback(async (endpoint, payload, apiKey) => {
    reset()
    setIsRunning(true)
    const key = endpoint === '/api/v1/validate-invoice' ? 'validate'
               : endpoint === '/asp/v1/validate' ? 'asp' : 'submit'

    let parsed
    if (typeof payload === 'string') {
      const { data, error: parseErr } = parseAndDescribeJson(payload)
      if (parseErr) {
        setResult(key, {
          status: "FAILURE",
          report: {
            invoice_number: "N/A",
            is_valid: false,
            total_errors: 1,
          errors: [{
            field: "JSON Structure",
            error: parseErr,
            severity: "HIGH",
            category: "FORMAT"
          }],
          metrics: { total_checks: 1, passed_checks: 0, failed_checks: 1, pass_percentage: 0.0 },
          timestamp: new Date().toISOString(),
          field_results: [{
            group: "System Check",
            fields: [{
              field: "JSON Structure",
              label: "JSON Structure",
              value: "Malformed JSON",
              status: "fail",
              pint_ref: "FORMAT",
              error: parseErr
            }]
          }]
        }
      })
      setIsRunning(false)
      return
    }
    parsed = data
  } else {
    parsed = payload
  }

    setStage(key, 'loading')
    try {
      const r = await apiFetch(endpoint, parsed, apiKey)
      setResult(key, r)
      setStage(key, 'success')
    } catch (e) {
      setStage(key, 'error')
      setError(e.message.includes('Failed to fetch')
        ? 'Cannot reach backend — is uvicorn running on port 8000?'
        : e.message)
    }
    setIsRunning(false)
  }, [reset])

  return { stages, results, error, isRunning, runPipeline, runSingle, reset }
}
