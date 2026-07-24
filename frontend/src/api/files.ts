import { apiFetch } from "./client";
import { requireCurrentOrgId } from "./currentOrg";
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

export interface FileTypeStat {
  category: string
  file_count: number
  total_bytes: number
}

export interface FileBucketStat {
  bucket_start: string
  file_count: number
}

export interface FileStats {
  total_files: number
  total_bytes: number
  by_type: FileTypeStat[]
  by_bucket: FileBucketStat[]
}

/**
 * Fetch aggregated file analytics for an organisation, optionally
 * bounded to a date range.
 */
export function getFileStats(
  orgId: number = requireCurrentOrgId(),
  start?: string,
  end?: string,
): Promise<FileStats> {
  const params = new URLSearchParams({ organisation_id: String(orgId) })
  if (start) params.set('start', start)
  if (end) params.set('end', end)
  return apiFetch<FileStats>(`/core/files/stats?${params.toString()}`)
}

/** Fetch one page of an organisation's files, newest first. */
export function listFiles(
  page = 1,
  pageSize = 9,
  orgId: number = requireCurrentOrgId(),
): Promise<FilePage> {
  return apiFetch<FilePage>(
    `/core/files?organisation_id=${orgId}&page=${page}&page_size=${pageSize}`,
  )
}


/**
 * Upload a file with its metadata to the current organisation as
 * multipart form data.
 */
export function uploadFile(
    file: File,
    title: string,
    description?: string,
): Promise<FileRead> {
    const form = new FormData()
    const orgId = requireCurrentOrgId()

    form.append('upload', file)
    form.append('title', title)
    form.append('organisation_id', String(orgId))
    if (description) {
        form.append('description', description)
    }

    return apiFetch<FileRead>('/core/files', {
        method: 'POST',
        body: form,
    })
}

/** Fetch a single file's metadata within the current organisation. */
export function getFile(id: number): Promise<FileRead> {
  const orgId = requireCurrentOrgId()
  return apiFetch<FileRead>(
    `/core/files/${id}?organisation_id=${orgId}`,
  )
}

/** Delete a file from the current organisation. */
export function deleteFile(id: number): Promise<void> {
  const orgId = requireCurrentOrgId()
  return apiFetch<void>(
    `/core/files/${id}?organisation_id=${orgId}`,
    { method: 'DELETE' },
  )
}

/** Update a file's editable metadata (title, description). */
export function updateFile(id: number, data: FileUpdate): Promise<FileRead> {
  const orgId = requireCurrentOrgId()
  return apiFetch<FileRead>(
    `/core/files/${id}?organisation_id=${orgId}`,
    {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    },
  )
}

/**
 * Fetch a file's raw binary content as a Blob. Bypasses apiFetch to read
 * the response as binary rather than JSON.
 */
export async function fetchFileContent(id: number): Promise<Blob> {
  const token = localStorage.getItem('access_token')
  const headers = new Headers()
  const orgId = requireCurrentOrgId()
  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  }

  const response = await fetch(
    `/api/core/files/${id}/content?organisation_id=${orgId}`,
    { headers },
  )
  if (!response.ok) {
    throw new ApiError(response.status, 'Could not load file content.')
  }
  return response.blob()
}

/**
 * Download a file to the user's device under its original filename by
 * fetching its content and triggering a temporary anchor click.
 */
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
