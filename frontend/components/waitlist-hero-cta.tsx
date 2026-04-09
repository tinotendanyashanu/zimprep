"use client";

import { FormEvent, useMemo, useState } from "react";
import { usePathname } from "next/navigation";
import { CheckCircle2 } from "lucide-react";

import { joinWaitlist } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

type WaitlistHeroCTAProps = {
  buttonClassName?: string;
  formClassName?: string;
  compact?: boolean;
};

export function WaitlistHeroCTA({
  buttonClassName,
  formClassName,
  compact = false,
}: WaitlistHeroCTAProps) {
  const pathname = usePathname();
  const [isOpen, setIsOpen] = useState(false);
  const [email, setEmail] = useState("");
  const [phoneNumber, setPhoneNumber] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const sourcePage = useMemo(() => pathname || "/", [pathname]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setSuccessMessage(null);
    setIsSubmitting(true);

    try {
      const response = await joinWaitlist({
        email: email.trim(),
        phone_number: phoneNumber.trim(),
        source_page: sourcePage,
      });

      setSuccessMessage(
        response.already_joined
          ? "You are already on the waitlist. We updated your details."
          : "You are on the waitlist. We will reach out when access opens."
      );
      setEmail("");
      setPhoneNumber("");
    } catch (submitError) {
      const message =
        submitError instanceof Error
          ? submitError.message
          : "Could not join the waitlist right now.";
      setError(message);
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className={compact ? "w-full max-w-xl mx-auto" : "w-full max-w-2xl mx-auto"}>
      <Button
        type="button"
        size="lg"
        variant="outline"
        className={buttonClassName}
        onClick={() => setIsOpen((open) => !open)}
      >
        Join Waitlist
      </Button>

      {isOpen && (
        <form
          onSubmit={handleSubmit}
          className={formClassName}
        >
          <div className="grid gap-3 sm:grid-cols-2">
            <Input
              type="email"
              inputMode="email"
              autoComplete="email"
              placeholder="Email address"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              required
            />
            <Input
              type="tel"
              inputMode="tel"
              autoComplete="tel"
              placeholder="Phone number"
              value={phoneNumber}
              onChange={(event) => setPhoneNumber(event.target.value)}
              required
            />
          </div>

          <div className="flex flex-col items-center gap-3 sm:flex-row sm:justify-between">
            <p className="text-xs text-muted-foreground">
              We only use these details to contact people waiting for access.
            </p>
            <Button type="submit" isLoading={isSubmitting} className="w-full sm:w-auto">
              Submit
            </Button>
          </div>

          {error && <p className="text-sm font-medium text-red-600">{error}</p>}

          {successMessage && (
            <p className="inline-flex items-center gap-2 text-sm font-medium text-emerald-700">
              <CheckCircle2 className="h-4 w-4" />
              {successMessage}
            </p>
          )}
        </form>
      )}
    </div>
  );
}
