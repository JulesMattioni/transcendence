import { useEffect, useState } from "react";
import QRCode from "qrcode";
import { Loader2, Copy, Check } from "lucide-react";
import Modal from "../Modal";
import { enable2fa, verify2fa } from "../../api/auth";

interface TwoFactorSetupModalProps {
  isOpen: boolean;
  onClose: () => void;
  onEnabled: () => void;
}

function TwoFactorSetupContent({
  onClose,
  onEnabled,
}: Omit<TwoFactorSetupModalProps, "isOpen">) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [secret, setSecret] = useState("");
  const [qrDataUrl, setQrDataUrl] = useState("");
  const [copied, setCopied] = useState(false);

  const [code, setCode] = useState("");
  const [verifying, setVerifying] = useState(false);
  const [verifyError, setVerifyError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    enable2fa()
      .then(async (creds) => {
        if (!active) return;
        setSecret(creds.secret);
        const dataUrl = await QRCode.toDataURL(creds.otpauth_uri, {
          margin: 1,
          width: 200,
        });
        if (active) setQrDataUrl(dataUrl);
      })
      .catch(() => active && setError("Could not start 2FA setup. Please try again."))
      .finally(() => active && setLoading(false));

    return () => {
      active = false;
    };
  }, []);

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(secret);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      setCopied(false);
    }
  }

  async function handleVerify() {
    setVerifying(true);
    setVerifyError(null);
    try {
      await verify2fa(code.trim());
      onEnabled();
      onClose();
    } catch {
      setVerifyError("Invalid code. Please try again.");
    } finally {
      setVerifying(false);
    }
  }

  const codeValid = /^\d{6}$/.test(code.trim());

  if (loading) {
    return (
      <div className="flex h-48 items-center justify-center text-muted">
        <Loader2 className="mr-2 animate-spin" size={20} />
        Preparing setup…
      </div>
    );
  }

  if (error) {
    return <p className="py-8 text-center text-sm text-red-600">{error}</p>;
  }

  return (
    <div className="space-y-5">
      <p className="text-sm text-muted">
        Scan this QR code with your authenticator app (Google Authenticator,
        Authy…), then enter the 6-digit code it generates.
      </p>

      {qrDataUrl && (
        <div className="flex justify-center">
          <img
            src={qrDataUrl}
            alt="2FA QR code"
            className="border border-gray-200"
          />
        </div>
      )}

      {/* Scan unavailable */}
      <div>
        <p className="text-xs font-medium text-subtle">Or enter this key manually</p>
        <div className="mt-1 flex items-center gap-2">
          <code className="flex-1 truncate bg-gray-100 px-3 py-2 font-mono text-sm text-black">
            {secret}
          </code>
          <button
            type="button"
            onClick={handleCopy}
            aria-label="Copy secret"
            className="flex h-9 w-9 items-center justify-center border border-gray-200 text-muted transition-colors hover:text-black"
          >
            {copied ? <Check size={16} className="text-green-600" /> : <Copy size={16} />}
          </button>
        </div>
      </div>

      {/* Code input */}
      <div>
        <label htmlFor="totp" className="text-sm font-medium text-black">
          Verification code
        </label>
        <input
          id="totp"
          type="text"
          inputMode="numeric"
          autoComplete="one-time-code"
          maxLength={6}
          value={code}
          onChange={(e) => setCode(e.target.value.replace(/\D/g, ""))}
          placeholder="123456"
          className="mt-2 w-full border border-gray-200 px-4 py-2.5 text-center text-lg tracking-[0.3em] text-black outline-none focus:border-keepr"
        />
        {verifyError && (
          <p className="mt-2 text-sm text-red-600">{verifyError}</p>
        )}
      </div>

      <div className="flex justify-end gap-3 pt-2">
        <button
          type="button"
          onClick={onClose}
          className="px-4 py-2.5 text-sm font-medium text-muted transition-colors hover:text-black"
        >
          Cancel
        </button>
        <button
          type="button"
          onClick={handleVerify}
          disabled={!codeValid || verifying}
          className="inline-flex items-center gap-2 bg-keepr px-5 py-2.5 text-sm font-semibold text-white transition-colors enabled:hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {verifying && <Loader2 className="animate-spin" size={16} />}
          {verifying ? "Verifying…" : "Enable"}
        </button>
      </div>
    </div>
  );
}

function TwoFactorSetupModal({
  isOpen,
  onClose,
  onEnabled,
}: TwoFactorSetupModalProps) {
  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Enable two-factor authentication"
      size="sm"
    >
      {isOpen && (
        <TwoFactorSetupContent
          key={isOpen ? "open" : "closed"}
          onClose={onClose}
          onEnabled={onEnabled}
        />
      )}
    </Modal>
  );
}

export default TwoFactorSetupModal;
