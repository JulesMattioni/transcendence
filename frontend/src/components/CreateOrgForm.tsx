import { useState } from "react";
import { createOrg } from "../api/org";
import { ApiError } from "../api/client";
import type { OrganisationRead } from "../api/org";

interface CreateOrgFormProps {
  onSuccess: (org: OrganisationRead) => void;
}


function CreateOrgForm({ onSuccess }: CreateOrgFormProps) {
  const [name, setName] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

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
          className="w-full border border-gray-300 px-3 py-2"
          placeholder="My organisation"
        />
      </div>

      {error && <p className="text-sm text-red-500">{error}</p>}

      <button
        type="submit"
        disabled={submitting}
        className="w-full bg-keepr px-4 py-2 font-medium text-white disabled:opacity-50"
      >
        {submitting ? "Creating…" : "Create organisation"}
      </button>
    </form>
  );
}

export default CreateOrgForm;
