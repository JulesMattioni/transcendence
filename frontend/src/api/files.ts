import { apiFetch } from "./client";
import { CURRENT_ORG_ID } from "../config";

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

export function listFiles(): Promise<FileRead[]> {
    return apiFetch<FileRead[]>(`/core/files?organisation_id=${CURRENT_ORG_ID}`)
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