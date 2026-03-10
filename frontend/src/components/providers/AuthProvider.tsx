"use client";

import { ClerkProvider } from "@clerk/nextjs";
import { useEffect, useState, type ReactNode } from "react";

import { isLikelyValidClerkPublishableKey } from "@/auth/clerkKey";
import {
  clearLocalAuthToken,
  getLocalAuthToken,
  isLocalAuthMode,
} from "@/auth/localAuth";
import { LocalAuthLogin } from "@/components/organisms/LocalAuthLogin";

export function AuthProvider({ children }: { children: ReactNode }) {
  const localMode = isLocalAuthMode();
  const isDemoMode = process.env.NEXT_PUBLIC_DEMO_MODE === "true";
  const [hasMounted, setHasMounted] = useState(false);
  const [hasToken, setHasToken] = useState(false);

  useEffect(() => {
    setHasMounted(true);
    setHasToken(Boolean(getLocalAuthToken()));
  }, []);

  useEffect(() => {
    if (!localMode) {
      clearLocalAuthToken();
    }
  }, [localMode]);

  if (localMode) {
    // During SSR, render a minimal placeholder to avoid hydration mismatch
    if (!hasMounted) {
      return <div className="min-h-screen bg-app" />;
    }
    // Demo mode - bypass login screen
    if (isDemoMode) {
      // Add a small demo indicator
      return (
        <>
          <div className="fixed top-0 left-0 right-0 z-50 bg-yellow-100 border-b border-yellow-300 px-4 py-2 text-center text-sm text-yellow-800">
           🎯 Demo Mode Active - Using default token
          </div>
          <div className="pt-10">
            {children}
          </div>
        </>
      );
    }
    if (!hasToken) {
      return <LocalAuthLogin onAuthenticated={() => setHasToken(true)} />;
    }
    return <>{children}</>;
  }

  const publishableKey = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY;
  const afterSignOutUrl =
    process.env.NEXT_PUBLIC_CLERK_AFTER_SIGN_OUT_URL ?? "/";

  if (!isLikelyValidClerkPublishableKey(publishableKey)) {
    return <>{children}</>;
  }

  return (
    <ClerkProvider
      publishableKey={publishableKey}
      afterSignOutUrl={afterSignOutUrl}
    >
      {children}
    </ClerkProvider>
  );
}
