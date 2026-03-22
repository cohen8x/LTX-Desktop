import { session } from 'electron'
import { isDev } from './config'

// Enforce Content Security Policy via response headers (tamper-proof from renderer)
export function setupCSP(): void {
  session.defaultSession.webRequest.onHeadersReceived((details, callback) => {
    let cspStr = isDev
      ? [
          "default-src 'self'",
          "script-src 'self' 'unsafe-inline'",
          "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
          "font-src 'self' https://fonts.gstatic.com",
          "connect-src 'self' http://localhost:* http://127.0.0.1:* ws://localhost:* ws://127.0.0.1:*",
          "img-src 'self' data: blob: file:",
          "media-src 'self' blob: file:",
          "object-src 'none'",
          "base-uri 'self'",
          "form-action 'self'",
          "frame-ancestors 'none'",
        ].join('; ')
      : [
          "default-src 'self'",
          "script-src 'self'",
          "style-src 'self' https://fonts.googleapis.com",
          "font-src 'self' https://fonts.gstatic.com",
          "connect-src 'self' http://localhost:* http://127.0.0.1:* ws://localhost:* ws://127.0.0.1:*",
          "img-src 'self' data: blob: file:",
          "media-src 'self' blob: file:",
          "object-src 'none'",
          "base-uri 'self'",
          "form-action 'self'",
          "frame-ancestors 'none'",
        ].join('; ')

    // Dynamically inject the external backend URL to allow connections
    const externalUrl = process.env.LTX_EXTERNAL_BACKEND_URL
    if (externalUrl) {
      try {
        const urlObj = new URL(externalUrl)
        const wsProtocol = urlObj.protocol === 'https:' ? 'wss:' : 'ws:'
        const allowedOrigin = `${urlObj.protocol}//${urlObj.host} ${wsProtocol}//${urlObj.host}`
        cspStr = cspStr.replace('connect-src', `connect-src ${allowedOrigin}`)
      } catch (e) {
        console.warn('Failed to parse LTX_EXTERNAL_BACKEND_URL for CSP injection:', e)
      }
    }

    callback({
      responseHeaders: {
        ...details.responseHeaders,
        'Content-Security-Policy': [cspStr],
      },
    })
  })
}
