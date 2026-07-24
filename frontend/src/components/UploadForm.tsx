import { useState } from "react";
import { uploadFile } from "../api/files";
import { ApiError } from "../api/client";

interface UploadFormProps {
  onSuccess: () => void;
}

/**
 * Form to upload a file with a title and optional description, supporting
 * drag-and-drop or click-to-browse. Calls onSuccess after a successful
 * upload, or shows an error.
 */
function UploadForm({ onSuccess }: UploadFormProps) {
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [isDragging, setIsDragging] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /** Accept the first dropped file into the form. */
  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    setIsDragging(false);
    const dropped = e.dataTransfer.files?.[0];
    if (dropped) {
      setFile(dropped);
    }
  }

  /** Validate the file and title, then upload. */
  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();

    if (!file) {
      setError("Please choose a file.");
      return;
    }
    if (!title.trim()) {
      setError("Please enter a title.");
      return;
    }

    setSubmitting(true);
    setError(null);
    try {
      await uploadFile(file, title, description || undefined);
      onSuccess();
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "Upload failed.";
      setError(message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {/* File input */}

      <div>
        <label className="mb-1 block text-sm font-medium text-black">
          File
        </label>
        <label
          onDragOver={(e) => {
            e.preventDefault();
            setIsDragging(true);
          }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={handleDrop}
          className={`flex cursor-pointer flex-col items-center justify-center rounded border-2 border-dashed p-6 text-center text-sm transition-colors ${
            isDragging
              ? "border-keepr bg-blue-50 text-keepr"
              : "border-gray-300 text-muted"
          }`}
        >
          {file ? (
            <span className="font-medium text-black">{file.name}</span>
          ) : (
            <span>Drag a file here, or click to browse</span>
          )}
          <input
            type="file"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            className="hidden"
          />
        </label>
      </div>

      <div>
        <label className="mb-1 block text-sm font-medium text-black">
          Title
        </label>
        <input
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          className="w-full rounded border border-gray-300 px-3 py-2 transition-colors focus:border-keepr focus:outline-none"
          placeholder="My document"
        />
      </div>

      <div>
        <label className="mb-1 block text-sm font-medium text-black">
          Description <span className="text-muted">(optional)</span>
        </label>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          className="w-full rounded border border-gray-300 px-3 py-2 transition-colors focus:border-keepr focus:outline-none"
          rows={3}
        />
      </div>

      {error && <p className="text-sm text-red-500">{error}</p>}

      <button
        type="submit"
        disabled={submitting}
        className="w-full rounded bg-keepr px-4 py-2 font-medium text-white transition-colors hover:bg-blue-700 disabled:opacity-50"
      >
        {submitting ? "Uploading…" : "Upload"}
      </button>
    </form>
  );
}

export default UploadForm;
