import { app } from 'electron'
import path from 'path'
import os from 'os'
import fs from 'fs'
import { getProjectAssetsPath } from './app-state'

export const isDev = !app.isPackaged

// Get directory - works in both CJS and ESM contexts
export function getCurrentDir(): string {
  // In bundled output, use app.getAppPath()
  if (!isDev) {
    return path.dirname(app.getPath('exe'))
  }
  // In development, use process.cwd() which is the project root
  return process.cwd()
}

export function getAllowedRoots(): string[] {
  const roots = [
    getCurrentDir(),
    app.getPath('userData'),
    app.getPath('downloads'),
    os.tmpdir(),
  ]
  if (!isDev && process.resourcesPath) {
    roots.push(process.resourcesPath)
  }
  roots.push(getProjectAssetsPath())
  return roots
}

export function loadEnv(): void {
  try {
    const envPath = path.join(getCurrentDir(), '.env')
    if (fs.existsSync(envPath)) {
      const content = fs.readFileSync(envPath, 'utf8')
      content.split('\n').forEach((line: string) => {
        const match = line.match(/^\s*([\w.-]+)\s*=\s*(.*)?\s*$/)
        if (match) {
          const key = match[1]
          let value = match[2] || ''
          if (value.startsWith('"') && value.endsWith('"')) value = value.slice(1, -1)
          else if (value.startsWith("'") && value.endsWith("'")) value = value.slice(1, -1)
          if (!process.env[key]) {
            process.env[key] = value
          }
        }
      })
    }
  } catch (e) {
    console.error('Failed to load .env file', e)
  }
}
