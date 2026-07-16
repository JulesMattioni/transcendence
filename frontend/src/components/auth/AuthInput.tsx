import { useState } from "react";
import { Eye, EyeOff } from "lucide-react";

interface AuthInputProps {
  type?: string;
  placeholder: string;
  value: string;
  onChange: (value: string) => void;
  name: string;
  autoComplete?: string;
}

function AuthInput({
  type = "text",
  placeholder,
  value,
  onChange,
  name,
  autoComplete,
}: AuthInputProps) {
  const [show, setShow] = useState(false);
  const isPassword = type === "password";

  const inputType = isPassword && show ? "text" : type;

  return (
    <div className="relative">
      <input
        type={inputType}
        name={name}
        placeholder={placeholder}
        value={value}
        autoComplete={autoComplete}
        onChange={(e) => onChange(e.target.value)}
        className="w-full border border-gray-200 bg-gray-50 px-4 py-3 pr-11 text-sm text-black placeholder:text-gray-400 focus:border-keepr focus:bg-white focus:outline-none focus:ring-1 focus:ring-keepr"
      />

      {/* Eye toggle */}
      {isPassword && (
        <button
          type="button"
          onClick={() => setShow((s) => !s)}
          className="absolute top-1/2 right-3 -translate-y-1/2 text-gray-400 hover:text-gray-600"
        >
          {show ? <EyeOff size={18} /> : <Eye size={18} />}
        </button>
      )}
    </div>
  );
}

export default AuthInput;
