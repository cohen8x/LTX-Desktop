import { useCallback, useState } from 'react'
import { backendFetch, backendMediaUrl } from '../lib/backend'
import { logger } from '../lib/logger'

export type RetakeMode = 'replace_audio_and_video' | 'replace_video' | 'replace_audio'

export interface RetakeSubmitParams {
  videoPath: string
  startTime: number
  duration: number
  prompt: string
  mode: RetakeMode
}

export interface RetakeResult {
  videoPath: string
  videoUrl: string
}

interface UseRetakeState {
  isRetaking: boolean
  retakeStatus: string
  retakeError: string | null
  result: RetakeResult | null
}

export function useRetake() {
  const [state, setState] = useState<UseRetakeState>({
    isRetaking: false,
    retakeStatus: '',
    retakeError: null,
    result: null,
  })

  const submitRetake = useCallback(async (params: RetakeSubmitParams) => {
    if (!params.videoPath) return

    setState({
      isRetaking: true,
      retakeStatus: 'Generating',
      retakeError: null,
      result: null,
    })

    try {
      let finalVideoPath = params.videoPath
      const backendCreds = await window.electronAPI.getBackend()
      const connectedUrl = backendCreds?.url || ''
      const isExternal = connectedUrl && !connectedUrl.includes('127.0.0.1') && !connectedUrl.includes('localhost')

      const fileUrlToPath = (url: string) => {
        if (url.startsWith('file://')) {
          let p = decodeURIComponent(url.slice(7))
          if (/^\/[A-Za-z]:/.test(p)) p = p.slice(1)
          return p
        }
        return url
      }

      if (isExternal && params.videoPath) {
        setState(prev => ({ ...prev, retakeStatus: 'Uploading video...' }))
        let blob: Blob
        let vidName = 'video.mp4'

        if (params.videoPath.startsWith('blob:')) {
          const resp = await fetch(params.videoPath)
          blob = await resp.blob()
        } else {
          const localPath = fileUrlToPath(params.videoPath)
          const { data, mimeType } = await window.electronAPI.readLocalFile(localPath)
          const byteCharacters = atob(data)
          const byteNumbers = new Array(byteCharacters.length)
          for (let i = 0; i < byteCharacters.length; i++) {
            byteNumbers[i] = byteCharacters.charCodeAt(i)
          }
          const byteArray = new Uint8Array(byteNumbers)
          blob = new Blob([byteArray], { type: mimeType })
          vidName = localPath.split(/[\/\\]/).pop() || 'video.mp4'
        }

        const formData = new FormData()
        formData.append('file', blob, vidName)
        const upRes = await backendFetch('/api/upload', { method: 'POST', body: formData })
        if (!upRes.ok) throw new Error('Failed to upload video')
        finalVideoPath = (await upRes.json()).path
        
        setState(prev => ({ ...prev, retakeStatus: 'Generating' }))
      } else {
        if (params.videoPath.startsWith('blob:')) {
          throw new Error('Local backend requires an absolute file path, but received an unsaved browser file. Please click "upload a file" instead of dragging from another browser window.')
        }
        finalVideoPath = fileUrlToPath(params.videoPath)
      }

      const response = await backendFetch('/api/retake', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          video_path: finalVideoPath,
          start_time: params.startTime,
          duration: params.duration,
          prompt: params.prompt,
          mode: params.mode,
        }),
      })

      const data = await response.json()

      if (response.ok && data.status === 'complete' && data.video_path) {
        let videoUrl: string
        const backendCreds = await window.electronAPI.getBackend()
        const connectedUrl = backendCreds?.url || ''
        const isExternal = connectedUrl && !connectedUrl.includes('127.0.0.1') && !connectedUrl.includes('localhost')
        
        if (isExternal) {
          videoUrl = await backendMediaUrl(data.video_path)
        } else {
          const pathNormalized = data.video_path.replace(/\\/g, '/')
          videoUrl = pathNormalized.startsWith('/') ? `file://${pathNormalized}` : `file:///${pathNormalized}`
        }

        setState({
          isRetaking: false,
          retakeStatus: 'Retake complete!',
          retakeError: null,
          result: {
            videoPath: data.video_path,
            videoUrl,
          },
        })
        return
      }

      const errorMsg = data.error || 'Unknown error'
      setState({
        isRetaking: false,
        retakeStatus: '',
        retakeError: errorMsg,
        result: null,
      })
      logger.error(`Retake failed: ${errorMsg}`)
    } catch (error) {
      const message = (error as Error).message || 'Unknown error'
      logger.error(`Retake error: ${message}`)
      setState({
        isRetaking: false,
        retakeStatus: '',
        retakeError: message,
        result: null,
      })
    }
  }, [])

  const resetRetake = useCallback(() => {
    setState({
      isRetaking: false,
      retakeStatus: '',
      retakeError: null,
      result: null,
    })
  }, [])

  return {
    submitRetake,
    resetRetake,
    isRetaking: state.isRetaking,
    retakeStatus: state.retakeStatus,
    retakeError: state.retakeError,
    retakeResult: state.result,
  }
}
