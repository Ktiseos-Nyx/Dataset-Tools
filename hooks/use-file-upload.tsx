import { useCallback, useId, useRef, useState } from 'react'

export interface FileWithPreview {
  id: string
  file: File
  preview?: string
}

export interface UseFileUploadOptions {
  accept?: string
  maxSize?: number
  maxFiles?: number
  onUpload?: (file: File) => Promise<unknown> | void
}

export interface UseFileUploadReturn {
  files: FileWithPreview[]
  errors: string[]
  isDragging: boolean
  removeFile: (id: string) => void
  openFileDialog: () => void
  getInputProps: () => {
    ref: React.RefObject<HTMLInputElement | null>
    type: 'file'
    id: string
    accept?: string
    multiple: boolean
    onChange: (event: React.ChangeEvent<HTMLInputElement>) => Promise<void>
  }
  handleDragEnter: (e: React.DragEvent) => void
  handleDragLeave: (e: React.DragEvent) => void
  handleDragOver: (e: React.DragEvent) => void
  handleDrop: (e: React.DragEvent) => void
}

export function useFileUpload(
  options: UseFileUploadOptions = {}
): UseFileUploadReturn {
  const { accept, maxSize, maxFiles = 1, onUpload } = options

  const id = useId()
  const inputRef = useRef<HTMLInputElement>(null)
  const dragCounterRef = useRef(0)

  const [files, setFiles] = useState<FileWithPreview[]>([])
  const [errors, setErrors] = useState<string[]>([])
  const [isDragging, setIsDragging] = useState(false)

  const validateFile = useCallback(
    (file: File): string | null => {
      if (accept) {
        const acceptedTypes = accept.split(',').map((t) => t.trim())
        const fileType = file.type
        const isAccepted = acceptedTypes.some((type) => {
          if (type.endsWith('/*')) {
            return fileType.startsWith(type.replace('/*', ''))
          }
          return fileType === type
        })

        if (!isAccepted) {
          return `File type not accepted. Allowed: ${accept}`
        }
      }

      if (maxSize && file.size > maxSize) {
        const maxSizeMB = (maxSize / (1024 * 1024)).toFixed(1)
        return `File too large. Max size: ${maxSizeMB}MB`
      }

      return null
    },
    [accept, maxSize]
  )

  const createPreview = useCallback(
    (file: File): Promise<string | undefined> => {
      return new Promise((resolve) => {
        if (file.type.startsWith('image/')) {
          const reader = new FileReader()
          reader.onloadend = () => resolve(reader.result as string)
          reader.onerror = () => resolve(undefined)
          reader.readAsDataURL(file)
        } else {
          resolve(undefined)
        }
      })
    },
    []
  )

  const processFiles = useCallback(
    async (fileList: FileList | File[]) => {
      const filesArray = Array.from(fileList)
      const newErrors: string[] = []
      const validFiles: FileWithPreview[] = []

      for (const file of filesArray) {
        const error = validateFile(file)
        if (error) {
          newErrors.push(error)
          continue
        }

        const preview = await createPreview(file)

        validFiles.push({
          id: `${Date.now()}-${Math.random()}`,
          file,
          preview,
        })

        if (onUpload) {
          await onUpload(file)
        }
      }

      setErrors(newErrors)
      setFiles((prev) => {
        const combined = [...prev, ...validFiles]
        return combined.slice(0, maxFiles)
      })
    },
    [validateFile, createPreview, onUpload, maxFiles]
  )

  const removeFile = useCallback((fileId: string) => {
    setFiles((prev) => prev.filter((f) => f.id !== fileId))
  }, [])

  const openFileDialog = useCallback(() => {
    inputRef.current?.click()
  }, [])

  const handleFileChange = useCallback(
    async (event: React.ChangeEvent<HTMLInputElement>) => {
      const fileList = event.target.files
      if (fileList && fileList.length > 0) {
        await processFiles(fileList)
      }
      event.target.value = ''
    },
    [processFiles]
  )

  const getInputProps = useCallback(() => {
    return {
      ref: inputRef,
      type: 'file' as const,
      id: `${id}-file-input`,
      accept,
      multiple: maxFiles > 1,
      onChange: handleFileChange,
    }
  }, [id, accept, maxFiles, handleFileChange])

  const handleDragEnter = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    dragCounterRef.current++
    if (e.dataTransfer.items && e.dataTransfer.items.length > 0) {
      setIsDragging(true)
    }
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    dragCounterRef.current--
    if (dragCounterRef.current === 0) {
      setIsDragging(false)
    }
  }, [])

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
  }, [])

  const handleDrop = useCallback(
    async (e: React.DragEvent) => {
      e.preventDefault()
      e.stopPropagation()
      setIsDragging(false)
      dragCounterRef.current = 0

      const fileList = e.dataTransfer.files
      if (fileList && fileList.length > 0) {
        await processFiles(fileList)
      }
    },
    [processFiles]
  )

  return {
    files,
    errors,
    isDragging,
    removeFile,
    openFileDialog,
    getInputProps,
    handleDragEnter,
    handleDragLeave,
    handleDragOver,
    handleDrop,
  }
}
