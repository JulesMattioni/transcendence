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


export function getFile(id: number): Promise<FileRead> {
    return apiFetch<FileRead>(`/core/files/${id}`)
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

export function deleteFile(id: number): Promise<void> {
    return apiFetch<void>(`/core/files/${id}`, {
        method: 'DELETE',
    })
}

export function updateFile(id: number, data: FileUpdate): Promise<FileRead> {
  return apiFetch<FileRead>(`/core/files/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
}

export async function fetchFileContent(id: number): Promise<Blob> {
  const token = localStorage.getItem('token')
  const headers = new Headers()
  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  }

  const response = await fetch(`/api/core/files/${id}/content`, { headers })
  if (!response.ok) {
    console.error('file content status:', response.status, await response.text())
    throw new ApiError(response.status, 'Could not load file content.')
  }
  return response.blob()
}
