"use client";

import { FormEvent, useState } from "react";
import { useAuth } from "./AuthProvider";

export function AuthSheet({
  open,
  onClose,
  reason = "Sign in with your UIC account to participate.",
}: {
  open: boolean;
  onClose: () => void;
  reason?: string;
}) {
  const { signIn } = useAuth();
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [sending, setSending] = useState(false);
  if (!open) return null;
  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSending(true);
    setMessage(null);
    const error = await signIn(email);
    setMessage(error ?? "Check your UIC inbox for your sign-in link.");
    setSending(false);
  };
  return (
    <div
      className="absolute inset-0 z-50 flex items-end bg-slate-950/35"
      role="dialog"
      aria-modal="true"
    >
      <form
        onSubmit={submit}
        className="w-full rounded-t-3xl bg-white p-6 pb-[max(1.5rem,env(safe-area-inset-bottom))] shadow-2xl"
      >
        <div className="mx-auto mb-5 h-1.5 w-10 rounded-full bg-slate-300" />
        <div className="flex justify-between gap-4">
          <div>
            <h2 className="text-xl font-bold">Sign in to StudyUIC</h2>
            <p className="mt-1 text-sm text-slate-600">{reason}</p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="h-10 w-10 rounded-full hover:bg-slate-100"
            aria-label="Close"
          >
            ✕
          </button>
        </div>
        <label className="mt-5 block text-sm font-medium">
          UIC email
          <input
            required
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            placeholder="netid@uic.edu"
            className="mt-1.5 w-full rounded-xl border border-slate-300 px-3 py-3 text-base"
          />
        </label>
        <button
          disabled={sending}
          className="mt-4 w-full rounded-xl bg-uic-blue py-3 font-semibold text-white disabled:opacity-60"
        >
          {sending ? "Sending…" : "Email me a sign-in link"}
        </button>
        <p className="mt-3 text-center text-xs text-slate-500">
          Personal email addresses are not accepted.
        </p>
        {/* If error message, make text red */}
        {message && (
          <p
            className={`mt-3 text-center text-sm ${
              message.startsWith("Check your") ? "text-slate-500" : "text-red-600"
            }`}
          >
            {message}
          </p>
        )}
      </form>
    </div>
  );
}
