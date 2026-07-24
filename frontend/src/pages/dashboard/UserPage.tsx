import { useEffect, useState } from "react";
import { MapPin, Mail, Shield, Check, Loader2 } from "lucide-react";
import DashboardLayout from "../../components/dashboard/DashboardLayout";
import { getAvatarUrl, availableAvatarIds } from "../../utils/avatars";
import { me, updateProfile, disable2fa, type UserRead } from "../../api/auth";
import TwoFactorSetupModal from "../../components/dashboard/TwoFactorSetupModal";

/**
 * Profile page: view the user's account, pick an avatar and edit
 * location, save changes, and enable or disable two-factor authentication.
 */
function UserPage() {
  const [user, setUser] = useState<UserRead | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [location, setLocation] = useState("");
  const [avatarId, setAvatarId] = useState(1);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [twoFaModalOpen, setTwoFaModalOpen] = useState(false);
  const [twoFaBusy, setTwoFaBusy] = useState(false);
  const [twoFaError, setTwoFaError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    me()
      .then((data) => {
        if (!active) return;
        setUser(data);
        setLocation(data.location ?? "");
        setAvatarId(data.avatar_id);
      })
      .catch(() => active && setError("Unable to load your profile."))
      .finally(() => active && setLoading(false));
    return () => {
      active = false;
    };
  }, []);

  const dirty =
    user != null &&
    (location.trim() !== (user.location ?? "") || avatarId !== user.avatar_id);

  /** Save the edited avatar and location, with transient saved feedback. */
  async function handleSave() {
    setSaving(true);
    setSaved(false);
    setSaveError(null);
    try {
      const updated = await updateProfile({
        location: location.trim(),
        avatar_id: avatarId,
      });
      setUser(updated);
      setLocation(updated.location ?? "");
      setAvatarId(updated.avatar_id);
      setSaved(true);
      setTimeout(() => setSaved(false), 2500);
    } catch {
      setSaveError("Could not save your changes. Please try again.");
    } finally {
      setSaving(false);
    }
  }

  /** Disable 2FA immediately, or open the setup modal to enable it. */
  function handleToggle2fa() {
    if (!user) return;
    setTwoFaError(null);
    if (user.is_2fa_enabled) {
      setTwoFaBusy(true);
      disable2fa()
        .then((updated) => setUser(updated))
        .catch(() => setTwoFaError("Could not disable 2FA. Please try again."))
        .finally(() => setTwoFaBusy(false));
    } else {
      setTwoFaModalOpen(true);
    }
  }

  /** Reflect newly enabled 2FA in the local user state. */
  function handle2faEnabled() {
    setUser((prev) => (prev ? { ...prev, is_2fa_enabled: true } : prev));
  }


  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex h-64 items-center justify-center text-muted">
          <Loader2 className="mr-2 animate-spin" size={20} />
          Loading profile…
        </div>
      </DashboardLayout>
    );
  }

  if (error || !user) {
    return (
      <DashboardLayout>
        <h1 className="font-serif text-2xl font-bold text-black">My Profile</h1>
        <p className="mt-4 text-red-600">{error ?? "Profile unavailable."}</p>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <h1 className="font-serif text-2xl font-bold text-black">My Profile</h1>
      <p className="mt-1 text-sm text-muted">
        Manage your personal information and profile picture.
      </p>

      <section className="mt-8 rounded bg-white p-6 shadow-sm sm:p-8">
        <div className="flex items-center gap-5 border-b border-gray-100 pb-6">
          <img
            src={getAvatarUrl(avatarId)}
            alt="Profile avatar"
            className="h-20 w-20 shrink-0 rounded-full border border-gray-200 object-cover"
          />
          <div className="min-w-0">
            <h2 className="font-serif text-xl font-bold text-black">
              {user.first_name} {user.last_name}
            </h2>
            <p className="mt-1 flex items-center gap-1.5 truncate text-sm text-muted">
              <Mail size={14} className="shrink-0" />
              {user.email}
            </p>
            <div className="mt-2 flex items-center gap-3">
              <span
                className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium ${
                  user.is_2fa_enabled
                    ? "bg-green-100 text-green-700"
                    : "bg-gray-100 text-gray-600"
                }`}
              >
                <Shield size={12} />
                {user.is_2fa_enabled ? "2FA enabled" : "2FA disabled"}
              </span>

              {/* 2fa switch */}
              <button
                type="button"
                role="switch"
                disabled={twoFaBusy}
                onClick={handleToggle2fa}
                className={`relative inline-flex h-6 w-11 shrink-0 items-center rounded-full transition-colors disabled:opacity-50 ${
                  user.is_2fa_enabled ? "bg-keepr" : "bg-gray-300"
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    user.is_2fa_enabled ? "translate-x-6" : "translate-x-1"
                  }`}
                />
              </button>
            </div>
            {twoFaError && (
              <p className="mt-1 text-xs text-red-600">{twoFaError}</p>
            )}

          </div>
        </div>

        <div className="pt-6">
          <p className="text-sm font-medium text-black">Profile picture</p>
          <div className="mt-3 flex flex-wrap gap-3">
            {availableAvatarIds.map((id) => {
              const selected = id === avatarId;
              return (
                <button
                  key={id}
                  type="button"
                  onClick={() => setAvatarId(id)}
                  className={`relative h-16 w-16 overflow-hidden rounded-full border-2 transition ${
                    selected
                      ? "border-keepr ring-2 ring-keepr/30"
                      : "border-transparent hover:border-gray-300"
                  }`}
                >
                  <img
                    src={getAvatarUrl(id)}
                    alt={`Avatar ${id}`}
                    className="h-full w-full object-cover"
                  />
                  {selected && (
                    <span className="absolute right-0 bottom-0 flex h-5 w-5 items-center justify-center rounded-full bg-keepr text-white">
                      <Check size={12} />
                    </span>
                  )}
                </button>
              );
            })}
          </div>
        </div>

        {/* Location */}
        <div className="mt-6">
          <label htmlFor="location" className="text-sm font-medium text-black">
            Location
          </label>
          <div className="relative mt-2">
            <MapPin
              size={16}
              className="pointer-events-none absolute top-1/2 left-3 -translate-y-1/2 text-subtle"
            />
            <input
              id="location"
              type="text"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              placeholder="e.g. Paris, France"
              maxLength={100}
              className="w-full rounded border border-gray-200 py-2.5 pr-4 pl-9 text-sm text-black outline-none transition-colors focus:border-keepr"
            />
          </div>
        </div>

        {/* Actions */}
        <div className="mt-8 flex items-center gap-4 border-t border-gray-100 pt-6">
          <button
            type="button"
            onClick={handleSave}
            disabled={!dirty || saving}
            className="inline-flex items-center gap-2 rounded bg-keepr px-5 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {saving && <Loader2 className="animate-spin" size={16} />}
            {saving ? "Saving…" : "Save changes"}
          </button>
          {saved && (
            <span className="flex items-center gap-1.5 text-sm text-green-600">
              <Check size={16} />
              Saved
            </span>
          )}
          {saveError && <span className="text-sm text-red-600">{saveError}</span>}
        </div>
      </section>
      <TwoFactorSetupModal
        isOpen={twoFaModalOpen}
        onClose={() => setTwoFaModalOpen(false)}
        onEnabled={handle2faEnabled}
      />
    </DashboardLayout>
  );
}

export default UserPage;
