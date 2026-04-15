/**
 * Downloads a CSV file from an API endpoint that requires authentication headers.
 * Uses fetch() + Blob instead of window.open() so custom headers can be sent.
 */
export async function downloadCsv(url, filename = 'export.csv') {
  try {
    const res = await fetch(url, {
      headers: {
        'X-API-Key': 'demo-key-123',
      },
    })

    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(err.message || `Download failed (${res.status})`)
    }

    const blob = await res.blob()
    const objectUrl = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = objectUrl
    a.download = filename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(objectUrl)
    return true
  } catch (e) {
    throw e
  }
}

/** Standard headers for all API fetch() calls */
export const API_HEADERS = {
  'Content-Type': 'application/json',
  'X-API-Key': 'demo-key-123',
}
