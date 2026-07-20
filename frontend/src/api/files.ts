import { apiFetch } from "./client";
import { CURRENT_ORG_ID } from "../config";
import { ApiError } from './client'


export interface FileRead {
  id: number
  title: string
  filename: string
  description: string | null
  organisation_id: number
  content_type: string
  size_bytes: number
  owner_id: number
  created_at: string
}

export interface FileUpdate {
  title?: string
  description?: string
}

export interface FilePage {
  items: FileRead[]
  total: number
  page: number
  page_size: number
}

export function listFiles(page = 1, pageSize = 9): Promise<FilePage> {
  return apiFetch<FilePage>(
    `/core/files?organisation_id=${CURRENT_ORG_ID}&page=${page}&page_size=${pageSize}`,
  )
}

export function uploadFile(
    file: File,
    title: string,
    description?: string,
): Promise<FileRead> {
    const form = new FormData()

    form.append('upload', file)
    form.append('title', title)
    form.append('organisation_id', String(CURRENT_ORG_ID))
    if (description) {
        form.append('description', description)
    }

    return apiFetch<FileRead>('/core/files', {
        method: 'POST',
        body: form,
    })
}

export function getFile(id: number): Promise<FileRead> {
  return apiFetch<FileRead>(
    `/core/files/${id}?organisation_id=${CURRENT_ORG_ID}`,
  )
}

export function deleteFile(id: number): Promise<void> {
  return apiFetch<void>(
    `/core/files/${id}?organisation_id=${CURRENT_ORG_ID}`,
    { method: 'DELETE' },
  )
}

export function updateFile(id: number, data: FileUpdate): Promise<FileRead> {
  return apiFetch<FileRead>(
    `/core/files/${id}?organisation_id=${CURRENT_ORG_ID}`,
    {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    },
  )
}

export async function fetchFileContent(id: number): Promise<Blob> {
  const token = localStorage.getItem('access_token')
  const headers = new Headers()
  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  }

  const response = await fetch(
    `/api/core/files/${id}/content?organisation_id=${CURRENT_ORG_ID}`,
    { headers },
  )
  if (!response.ok) {
    throw new ApiError(response.status, 'Could not load file content.')
  }
  return response.blob()
}

export async function downloadFile(file: FileRead): Promise<void> {
  const blob = await fetchFileContent(file.id)
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = file.filename
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
}
