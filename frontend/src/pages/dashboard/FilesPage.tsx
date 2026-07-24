import DashboardLayout from "../../components/dashboard/DashboardLayout";
import { useCallback, useState, useEffect } from "react";
import { useOrg } from "../../context/orgContextValue";
import {
  type FileRead,
  listFiles,
  type FilePage,
  deleteFile,
} from "../../api/files";
import { ApiError } from "../../api/client";
import Modal from "../../components/Modal";
import {
  ArrowRight,
  ArrowLeft,
  Plus,
  FileText,
  FileImage,
  FileVideo,
  FileAudio,
  FileArchive,
  FileSpreadsheet,
  File as FileIcon,
  Trash2,
  Download,
  Pencil,
} from "lucide-react";
import UploadForm from "../../components/UploadForm";
import FilePreview from '../../components/FilePreview'
import { downloadFile } from "../../api/files";
import EditForm from "../../components/EditForm";


/** Pick the icon that best represents a file's content type. */
function iconForType(contentType: string) {
  if (contentType.startsWith("image/")) return FileImage;
  if (contentType.startsWith("video/")) return FileVideo;
  if (contentType.startsWith("audio/")) return FileAudio;
  if (contentType === "application/pdf") return FileText;
  if (
    contentType.includes("zip") ||
    contentType.includes("tar") ||
    contentType.includes("compressed")
  )
    return FileArchive;
  if (
    contentType.includes("spreadsheet") ||
    contentType.includes("excel") ||
    contentType === "text/csv"
  )
    return FileSpreadsheet;
  return FileIcon;
}

/**
 * Files page for the selected organisation: a paginated grid of files
 * with preview, download, and (for writers) upload, edit and delete.
 * Prompts to pick an organisation when none is selected.
 */
function FilesPage() {
  const [files, setFiles] = useState<FileRead[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [fileToDelete, setFileToDelete] = useState<FileRead | null>(null);
  const [fileToView, setFileToView] = useState<FileRead | null>(null)
  const [fileToEdit, setFileToEdit] = useState<FileRead | null>(null)

  const { canWrite, currentOrg, loading: orgLoading } = useOrg();

  const pageSize = 9;
  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  const showFiles = currentOrg ? files : [];

  /** Load the current page of files for the selected organisation. */
  const loadFiles = useCallback(() => {
    if (!currentOrg) return Promise.resolve();
    return listFiles(page, pageSize, currentOrg.org_id)
      .then((data: FilePage) => {
        setFiles(data.items);
        setTotal(data.total);
        setError(null);
      })
      .catch((err) => {
        const message =
          err instanceof ApiError ? err.message : "Could not load files.";
        setError(message);
      })
      .finally(() => setLoading(false));
  }, [page, currentOrg]);

  useEffect(() => {
    if (currentOrg) {
      loadFiles();
    }
  }, [loadFiles, currentOrg]);

  /** Download a file, surfacing any failure as an error message. */
  const handleDownload = useCallback((file: FileRead) => {
    downloadFile(file).catch((err) => {
      const message =
        err instanceof ApiError ? err.message : 'Could not download file.'
      setError(message)
    })
  }, [])

  /**
   * Delete the file pending confirmation, then reload; steps back a page
   * when the last item on a non-first page was removed.
   */
  const confirmDelete = useCallback(() => {
    if (!fileToDelete) return;
    deleteFile(fileToDelete.id)
      .then(() => {
        setFileToDelete(null);
        if (files.length === 1 && page > 1) {
          setPage((p) => p - 1);
        } else {
          loadFiles();
        }
      })
      .catch((err) => {
        const message =
          err instanceof ApiError ? err.message : "Could not delete file.";
        setError(message);
        setFileToDelete(null);
      });
  }, [fileToDelete, files.length, page, loadFiles]);


  return (
    <DashboardLayout>
      {orgLoading ? (
        <div className="flex h-full items-center justify-center">
          <p className="text-muted">Loading…</p>
        </div>
      ) : !currentOrg ? (
        <div className="flex h-full items-center justify-center p-6">
          <p className="text-center font-serif text-xl font-bold text-muted">
            Select or create an organisation to see its files.
          </p>
        </div>
      ) : (
        <>
          <div className="flex items-center justify-between">
            <h1 className="font-serif text-2xl font-bold text-black">Files</h1>
            {canWrite && (
              <button
                onClick={() => setIsModalOpen(true)}
                className="inline-flex items-center gap-2 rounded bg-keepr px-4 py-2 font-medium text-white transition-colors duration-200 hover:bg-blue-700"
              >
                Add file <Plus size={15} strokeWidth={2} />
              </button>
            )}
          </div>

          {loading && <p className="mt-4 text-muted">Loading…</p>}

          {error && <p className="mt-4 text-red-600">{error}</p>}

          {!loading && !error && showFiles.length === 0 && (
            <p className="mt-4 text-muted">No files yet.</p>
          )}

          {!loading && !error && showFiles.length > 0 && (
            <ul className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 mt-4">
              {showFiles.map((file) => {
                const Icon = iconForType(file.content_type);
                return (
                  <li
                    key={file.id}
                    className="flex aspect-[4/3] flex-col overflow-hidden rounded shadow-sm ring-1 ring-transparent transition-shadow duration-200 hover:shadow-md hover:ring-keepr"
                  >
                    {/* Icon */}
                    <div
                      onClick={() => setFileToView(file)}
                      className="flex flex-[3] cursor-pointer items-center justify-center bg-blue-100 text-keepr transition-colors hover:bg-blue-200"
                    >
                      <Icon size={60} strokeWidth={1.5} />
                    </div>

                    {/* Text */}
                    <div className="flex flex-[1] items-center bg-white gap-2 border-t border-gray-200 px-3 py-2">
                      <div className="min-w-0 flex-1">
                        <p className="truncate font-medium text-black">
                          {file.title}
                        </p>
                        <p className="truncate text-sm text-muted">
                          {file.filename}
                        </p>
                        {file.description && (
                          <p className="truncate text-xs text-muted">
                            {file.description}
                          </p>
                        )}
                      </div>
                      {canWrite && (
                        <button
                          onClick={() => setFileToEdit(file)}
                          className="shrink-0 p-1 text-muted transition-colors duration-200 hover:text-keepr"
                        >
                          <Pencil size={18} />
                        </button>
                      )}
                      <button
                        onClick={() => handleDownload(file)}
                        className="shrink-0 p-1 text-muted transition-colors duration-200 hover:text-keepr"
                      >
                        <Download size={18} />
                      </button>
                      {canWrite && (
                        <button
                          onClick={() => setFileToDelete(file)}
                          className="shrink-0 p-1 text-muted transition-colors duration-200 hover:text-red-600"
                        >
                          <Trash2 size={18} />
                        </button>
                      )}
                    </div>
                  </li>
                );
              })}
            </ul>
          )}

          {!loading && !error && total > pageSize && (
            <div className="mt-4 flex items-center justify-center gap-4">
              <button
                onClick={() => setPage((p) => p - 1)}
                disabled={page <= 1}
                className="rounded px-3 py-1 transition-colors duration-200 disabled:opacity-40 enabled:hover:bg-gray-100 enabled:hover:text-keepr"
              >
                <ArrowLeft size={14} />
              </button>
              <span className="text-sm text-muted">
                Page {page} / {totalPages}
              </span>
              <button
                onClick={() => setPage((p) => p + 1)}
                disabled={page >= totalPages}
                className="rounded px-3 py-1 transition-colors duration-200 disabled:opacity-40 enabled:hover:bg-gray-100 enabled:hover:text-keepr"
              >
                <ArrowRight size={14} />
              </button>
            </div>
          )}
        </>
      )}

      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Add file"
      >
        <UploadForm
          onSuccess={() => {
            setIsModalOpen(false);
            if (page === 1) {
              loadFiles();
            } else {
              setPage(1);
            }
          }}
        />
      </Modal>
      <Modal
        isOpen={fileToDelete !== null}
        onClose={() => setFileToDelete(null)}
        title="Delete file"
      >
        <p className="text-black">
          Are you sure you want to delete{" "}
          <span className="font-medium">{fileToDelete?.title}</span>? This
          action cannot be undone.
        </p>
        <div className="mt-6 flex justify-end gap-3">
          <button
            onClick={() => setFileToDelete(null)}
            className="rounded px-4 py-2 text-muted transition-colors duration-200 hover:bg-gray-100 hover:text-black"
          >
            Cancel
          </button>
          <button
            onClick={confirmDelete}
            className="rounded bg-red-600 px-4 py-2 font-medium text-white transition-colors duration-200 hover:bg-red-700"
          >
            Delete
          </button>
        </div>
      </Modal>
      <Modal
        isOpen={fileToView !== null}
        onClose={() => setFileToView(null)}
        title={fileToView?.title ?? ''}
        size="xl"
      >
        {fileToView && <FilePreview file={fileToView} />}
      </Modal>
      <Modal
        isOpen={fileToEdit !== null}
        onClose={() => setFileToEdit(null)}
        title="Edit file"
      >
        {fileToEdit && (
          <EditForm
            file={fileToEdit}
            onSuccess={() => {
              setFileToEdit(null);
              loadFiles();
            }}
          />
        )}
      </Modal>
    </DashboardLayout>
  );
}

export default FilesPage;
