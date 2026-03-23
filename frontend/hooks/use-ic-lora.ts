import { useCallback, useState } from 'react'
import { backendFetch, backendMediaUrl } from '../lib/backend'
import { logger } from '../lib/logger'

export type IcLoraConditioningType = 'canny' | 'depth' | 'pose'

export interface IcLoraSubmitParams {
  videoPath: string
  conditioningType: IcLoraConditioningType
  conditioningStrength: number
  prompt: string
}

export interface IcLoraResult {
  videoPath: string
  videoUrl: string
}

interface UseIcLoraState {
  isGenerating: boolean
  status: string
  error: string | null
  result: IcLoraResult | null
}

export function useIcLora() {
  const [state, setState] = useState<UseIcLoraState>({
    isGenerating: false,
    status: '',
    error: null,
    result: null,
  })

  const submitIcLora = useCallback(async (params: IcLoraSubmitParams) => {
    if (!params.videoPath || !params.prompt.trim()) return

    setState({
      isGenerating: true,
      status: 'Generating',
      error: null,
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
        setState(prev => ({ ...prev, status: 'Uploading video...' }))
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
        
        setState(prev => ({ ...prev, status: 'Generating' }))
      } else {
        if (params.videoPath.startsWith('blob:')) {
          throw new Error('Local backend requires an absolute file path, but received an unsaved browser file. Please click "upload a file" instead of dragging from another browser window.')
        }
        finalVideoPath = fileUrlToPath(params.videoPath)
      }

      const response = await backendFetch('/api/ic-lora/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          video_path: finalVideoPath,
          conditioning_type: params.conditioningType,
          conditioning_strength: params.conditioningStrength,
          prompt: params.prompt,
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
          isGenerating: false,
          status: 'Generation complete!',
          error: null,
          result: {
            videoPath: data.video_path,
            videoUrl,
          },
        })
        return
      }

      const errorMsg = data.error || 'Unknown error'
      logger.error(`IC-LoRA failed: ${errorMsg}`)
      setState({
        isGenerating: false,
        status: '',
        error: errorMsg,
        result: null,
      })
    } catch (error) {
      const message = (error as Error).message || 'Unknown error'
      logger.error(`IC-LoRA error: ${message}`)
      setState({
        isGenerating: false,
        status: '',
        error: message,
        result: null,
      })
    }
  }, [])

  const reset = useCallback(() => {
    setState({
      isGenerating: false,
      status: '',
      error: null,
      result: null,
    })
  }, [])

  return {
    submitIcLora,
    resetIcLora: reset,
    isIcLoraGenerating: state.isGenerating,
    icLoraStatus: state.status,
    icLoraError: state.error,
    icLoraResult: state.result,
  }
}
