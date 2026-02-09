'use client'

import {
  AlertCircleIcon,
  FileIcon,
  ImageIcon,
  UploadIcon,
  XIcon,
} from 'lucide-react'

import { Button } from '@/components/ui/button'
import { useFileUpload } from '@/hooks/use-file-upload'

export interface FileDropzoneProps {
  accept?: string
  maxSizeMB?: number
  maxFiles?: number
  multiple?: boolean
  onUpload?: (file: File) => Promise<unknown> | void
}

export const FileDropzone = ({
  accept,
  maxSizeMB = 2,
  maxFiles,
  multiple = false,
  onUpload,
}: FileDropzoneProps) => {
  const maxSize = maxSizeMB * 1024 * 1024
  const finalMaxFiles = maxFiles ?? (multiple ? 5 : 1)

  const {
    files,
    isDragging,
    errors,
    handleDragEnter,
    handleDragLeave,
    handleDragOver,
    handleDrop,
    openFileDialog,
    removeFile,
    getInputProps,
  } = useFileUpload({
    accept,
    maxSize,
    maxFiles: finalMaxFiles,
    onUpload,
  })

  const previewUrl = files[0]?.preview || null
  const uploadedFile = files[0]?.file || null
  const hasFiles = files.length > 0

  return (
    <div className="flex flex-col gap-4">
      <div className="relative">
        {/* Drop area */}
        <div
          className="border-input has-[input:focus]:border-ring has-[input:focus]:ring-ring/50 data-[dragging=true]:bg-accent/50 relative flex min-h-52 flex-col items-center justify-center overflow-hidden rounded-xl border border-dashed p-4 transition-colors has-[input:focus]:ring-[3px]"
          data-dragging={isDragging || undefined}
          onDragEnter={handleDragEnter}
          onDragLeave={handleDragLeave}
          onDragOver={handleDragOver}
          onDrop={handleDrop}
        >
          <input
            {...getInputProps()}
            aria-label="Upload file"
            className="sr-only"
          />
          {/* Single file mode: show file inside drop area */}
          {!multiple && uploadedFile ? (
            <div className="absolute inset-0 flex items-center justify-center p-4">
              {previewUrl ? (
                <img
                  alt={uploadedFile.name || 'Uploaded file'}
                  className="mx-auto max-h-full rounded object-contain"
                  src={previewUrl}
                />
              ) : (
                <div className="flex flex-col items-center justify-center gap-2 text-center">
                  <div
                    aria-hidden="true"
                    className="bg-background flex size-16 shrink-0 items-center justify-center rounded-full border"
                  >
                    <FileIcon className="size-8 opacity-60" />
                  </div>
                  <p className="text-sm font-medium">{uploadedFile.name}</p>
                  <p className="text-muted-foreground text-xs">
                    {uploadedFile.size < 1024 * 1024
                      ? `${(uploadedFile.size / 1024).toFixed(0)} KB`
                      : `${(uploadedFile.size / 1024 / 1024).toFixed(2)} MB`}
                  </p>
                </div>
              )}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center px-4 py-3 text-center">
              <div
                aria-hidden="true"
                className="bg-background mb-2 flex size-11 shrink-0 items-center justify-center rounded-full border"
              >
                <ImageIcon className="size-4 opacity-60" />
              </div>
              <p className="mb-1.5 text-sm font-medium">
                Drop your {multiple ? 'files' : 'file'} here
              </p>
              <p className="text-muted-foreground text-xs">
                {accept ? `${accept.split(',').join(', ')} ` : 'Any file type '}
                (max. {maxSizeMB}MB)
                {multiple &&
                  finalMaxFiles > 1 &&
                  ` · Up to ${finalMaxFiles} files`}
              </p>
              <Button
                className="mt-4"
                onClick={openFileDialog}
                variant="outline"
              >
                <UploadIcon
                  aria-hidden="true"
                  className="-ms-1 size-4 opacity-60"
                />
                Select {multiple ? 'files' : 'file'}
              </Button>
            </div>
          )}
        </div>

        {/* Remove button for single file mode */}
        {!multiple && uploadedFile && (
          <div className="absolute top-4 right-4">
            <button
              aria-label="Remove file"
              className="focus-visible:border-ring focus-visible:ring-ring/50 z-50 flex size-8 cursor-pointer items-center justify-center rounded-full bg-black/60 text-white transition-[color,box-shadow] outline-none hover:bg-black/80 focus-visible:ring-[3px]"
              onClick={() => removeFile(files[0]?.id)}
              type="button"
            >
              <XIcon aria-hidden="true" className="size-4" />
            </button>
          </div>
        )}
      </div>

      {/* Error messages */}
      {errors.length > 0 && (
        <div
          className="text-destructive flex items-center gap-1 text-xs"
          role="alert"
        >
          <AlertCircleIcon className="size-3 shrink-0" />
          <span>{errors[0]}</span>
        </div>
      )}

      {/* Uploaded files list for multiple mode */}
      {multiple && hasFiles && (
        <div className="space-y-2">
          {files.map((fileWithPreview) => {
            const { id, file, preview } = fileWithPreview
            return (
              <div
                key={id}
                className="bg-muted/50 border-border relative flex items-center gap-3 rounded-lg border p-3"
              >
                {preview ? (
                  <img
                    src={preview}
                    alt={file.name}
                    className="size-10 shrink-0 rounded object-cover"
                  />
                ) : (
                  <div className="bg-background flex size-10 shrink-0 items-center justify-center rounded border">
                    <FileIcon className="size-4 opacity-60" />
                  </div>
                )}
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium">{file.name}</p>
                  <p className="text-muted-foreground text-xs">
                    {file.size < 1024 * 1024
                      ? `${(file.size / 1024).toFixed(0)} KB`
                      : `${(file.size / 1024 / 1024).toFixed(2)} MB`}
                  </p>
                </div>
                <button
                  onClick={() => removeFile(id)}
                  aria-label={`Remove ${file.name}`}
                  className="text-muted-foreground hover:text-destructive shrink-0 transition-colors"
                  type="button"
                >
                  <XIcon className="size-4" />
                </button>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
