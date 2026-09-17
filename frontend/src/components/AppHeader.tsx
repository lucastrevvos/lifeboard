"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { api, errorMessage } from "@/lib/api";
import type { User } from "@/lib/types";

export function AppHeader({ user }: { user: User }) {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function logout() {
    setLoading(true);
    setError("");
    try {
      await api.logout();
      router.replace("/login");
    } catch (caught) {
      setError(errorMessage(caught));
      setLoading(false);
    }
  }

  return (
    <header className="app-header">
      <Link className="brand" href="/boards">LifeBoard</Link>
      <div className="account">
        <div><strong>{user.name}</strong><span>{user.email}</span></div>
        <button className="button ghost" onClick={logout} disabled={loading}>{loading ? "Saindo..." : "Sair"}</button>
      </div>
      {error && <p className="header-error" role="alert">{error}</p>}
    </header>
  );
}
