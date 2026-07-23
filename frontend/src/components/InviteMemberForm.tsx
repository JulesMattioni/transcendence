import { useState } from "react";
import { inviteMember, OrgRole } from "../api/org";
import { ApiError } from "../api/client";

interface InviteMemberFormProps {
  orgId: number;
  onSuccess: () => void;
}

function InviteMemberForm({ orgId, onSuccess }: InviteMemberFormProps) {
  const [email, setEmail] = useState("");
  const [roleId, setRoleId] = useState<number>(OrgRole.Reader);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!email.trim()) {
      setError("Please enter an email.");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      await inviteMember(orgId, email.trim(), roleId);
      onSuccess();
    } catch (err) {
      const message =
        err instanceof ApiError ? err.message : "Could not send invitation.";
      setError(message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="mb-1 block text-sm font-medium text-black">
          Email
        </label>
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="w-full border border-gray-300 px-3 py-2"
          placeholder="person@example.com"
        />
      </div>

      <div>
        <label className="mb-1 block text-sm font-medium text-black">
          Role
        </label>
        <select
          value={roleId}
          onChange={(e) => setRoleId(Number(e.target.value))}
          className="w-full border border-gray-300 px-3 py-2"
        >
          <option value={OrgRole.Admin}>Admin</option>
          <option value={OrgRole.Editor}>Editor</option>
          <option value={OrgRole.Reader}>Reader</option>
        </select>
      </div>

      {error && <p className="text-sm text-red-500">{error}</p>}

      <button
        type="submit"
        disabled={submitting}
        className="w-full bg-keepr px-4 py-2 font-medium text-white disabled:opacity-50"
      >
        {submitting ? "Sending…" : "Send invitation"}
      </button>
    </form>
  );
}

export default InviteMemberForm;
