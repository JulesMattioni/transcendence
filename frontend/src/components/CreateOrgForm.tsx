import { useState } from "react";
import { createOrg } from "../api/org";
import { ApiError } from "../api/client";
import type { OrganisationRead } from "../api/org";

interface CreateOrgFormProps {
  onSuccess: (org: OrganisationRead) => void;
}


/**
 * Form to create an organisation. Validates the name, submits it, and
 * reports the created organisation through onSuccess or shows an error.
 */
function CreateOrgForm({ onSuccess }: CreateOrgFormProps) {
  const [name, setName] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /** Validate and submit the new organisation name. */
  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();

    if (!name.trim()) {
      setError("Please enter an organisation name.");
      return;
    }

    setSubmitting(true);
    setError(null);
    try {
      const org = await createOrg(name.trim());
      onSuccess(org);
    } catch (err) {
      const message =
        err instanceof ApiError ? err.message : "Could not create organisation.";
      setError(message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="mb-1 block text-sm font-medium text-black">
          Organisation name
        </label>
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="w-full rounded border border-gray-300 px-3 py-2 transition-colors focus:border-keepr focus:outline-none"
          placeholder="My organisation"
        />
      </div>

      {error && <p className="text-sm text-red-500">{error}</p>}

      <button
        type="submit"
        disabled={submitting}
        className="w-full rounded bg-keepr px-4 py-2 font-medium text-white transition-colors hover:bg-blue-700 disabled:opacity-50"
      >
        {submitting ? "Creating…" : "Create organisation"}
      </button>
    </form>
  );
}

export default CreateOrgForm;
