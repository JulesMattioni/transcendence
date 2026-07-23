import { useState } from "react";
import { ArrowRight, ArrowLeft } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { signup, startGoogleLogin, startFtLogin } from "../api/auth";
import { ApiError } from "../api/client";
import {
  validateEmail,
  validateRequired,
  validatePasswordMatch,
  isPasswordValid,
} from "../utils/validation";
import AuthLayout from "../components/auth/AuthLayout";
import AuthInput from "../components/auth/AuthInput";
import AuthButton from "../components/auth/AuthButton";
import GoogleIcon from "../components/icons/GoogleIcon";
import FortyTwoIcon from "../components/icons/FortyTwoIcon";
import PasswordChecklist from "../components/auth/PasswordChecklist";
import PasswordMatch from "../components/auth/PasswordMatch";

function RegisterPage() {
  const [first_name, setFirstName] = useState("");
  const [last_name, setLastName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm_password, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");

    const emailError = validateEmail(email);
    if (emailError) return setError(emailError);

    const firstNameError = validateRequired(first_name, "First name");
    if (firstNameError) return setError(firstNameError);

    const lastNameError = validateRequired(last_name, "Last name");
    if (lastNameError) return setError(lastNameError);

    if (!isPasswordValid(password)) {
      return setError("Password does not meet all requirements.");
    }

    const matchError = validatePasswordMatch(password, confirm_password);
    if (matchError) return setError(matchError);

    setLoading(true);
    try {
      await signup({ first_name, last_name, email, password });
      navigate("/dashboard");
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Something went wrong. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  }

  async function handleGoogleLogin() {
    setError("");
    setLoading(true);
    try {
      await startGoogleLogin();
    } catch {
      setError("Could not start Google sign-in. Please try again.");
      setLoading(false);
    }
  }

  async function handleFtLogin() {
    setError("");
    setLoading(true);
    try {
      await startFtLogin();
    } catch {
      setError("Could not start 42 sign-in. Please try again.");
      setLoading(false);
    }
  }

  return (
    <AuthLayout>
      <p className="text-center font-sans font-bold text-2xl">Keepr.</p>
      <h1 className="text-center font-serif font-bold text-4xl">
        Create your account
      </h1>

      <form onSubmit={handleSubmit} className="mt-4 space-y-4">
        <p className="text-center font-sans font-light text-sm text-muted">
          Get started with Keepr.
        </p>
        {error && <p className="text-center text-sm text-red-500">{error}</p>}
        <div className="grid grid-cols-2 gap-3">
          <AuthInput
            type="text"
            name="FirstName"
            placeholder="First Name"
            value={first_name}
            onChange={setFirstName}
          />
          <AuthInput
            type="text"
            name="LastName"
            placeholder="Last Name"
            value={last_name}
            onChange={setLastName}
          />
        </div>
        <AuthInput
          type="email"
          name="email"
          placeholder="email@example.com"
          value={email}
          onChange={setEmail}
        />
        <AuthInput
          type="password"
          name="password"
          placeholder="Password"
          value={password}
          onChange={setPassword}
          autoComplete="new-password"
        />
        <PasswordChecklist password={password} />
        <AuthInput
          type="password"
          name="ConfirmPassword"
          placeholder="Confirm Password"
          value={confirm_password}
          onChange={setConfirmPassword}
          autoComplete="new-password"
        />
        <PasswordMatch password={password} confirm={confirm_password} />
        <AuthButton
          children="Create Account"
          loading={loading}
          icon=<ArrowRight size={15} strokeWidth={2} />
        />
        <div className="grid grid-cols-2 gap-3">
          <AuthButton
            children="Create with "
            variant="outline"
            type="button"
            icon=<GoogleIcon />
            onClick={handleGoogleLogin}
            loading={loading}
          />
          <AuthButton
            children="Create with "
            variant="outline"
            type="button"
            icon=<FortyTwoIcon />
            onClick={handleFtLogin}
            loading={loading}
          />
        </div>
        <p className="text-center font-sans font-light text-sm text-muted">
          Already have an account ?{" "}
          <Link to={"/login"} className="hover:text-black underline">
            {" "}
            Sign In
          </Link>
        </p>
        <Link
          to={"/"}
          className="flex items-center text-sans text-sm text-muted hover:text-black"
        >
          <ArrowLeft size={14} className="text-keepr" />
          Back
        </Link>
      </form>
    </AuthLayout>
  );
}

export default RegisterPage;
