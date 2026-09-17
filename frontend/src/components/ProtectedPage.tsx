"use client";

import { useRouter } from "next/navigation";
import { ReactNode, useEffect, useState } from "react";

import { ApiError, api, errorMessage } from "@/lib/api";
import type { User } from "@/lib/types";

type ProtectedPageProps = {
  children: (user: User) => ReactNode;
};

export function ProtectedPage({ children }: ProtectedPageProps) {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;

    api.currentUser()
      .then((currentUser) => {
        if (active) setUser(currentUser);
      })
      .catch((caught) => {
        if (!active) return;
        if (caught instanceof ApiError && caught.status === 401) {
          router.replace("/login");
          return;
        }
        setError(errorMessage(caught));
      });

    return () => { active = false; };
  }, [router]);

  if (error) {
    return <main className="centered-page"><div className="status-card"><p className="error" role="alert">{error}</p><button className="button secondary" onClick={() => location.reload()}>Tentar novamente</button></div></main>;
  }

  if (!user) {
    return <main className="centered-page"><p className="loading" role="status">Verificando sua sessão...</p></main>;
  }

  return children(user);
}
