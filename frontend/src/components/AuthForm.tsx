"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import { api, errorMessage } from "@/lib/api";

type AuthFormProps = {
  mode: "login" | "register";
};

export function AuthForm({ mode }: AuthFormProps) {
  const router = useRouter();
  const isRegister = mode === "register";
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError("");

    const form = new FormData(event.currentTarget);
    const email = String(form.get("email"));
    const password = String(form.get("password"));

    try {
      if (isRegister) {
        await api.register({ name: String(form.get("name")), email, password });
      }
      await api.login({ email, password });
      router.replace("/boards");
    } catch (caught) {
      setError(errorMessage(caught));
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="centered-page">
      <section className="auth-card">
        <Link className="brand" href="/">LifeBoard</Link>
        <p className="eyebrow">{isRegister ? "Comece seu espaço" : "Bem-vindo de volta"}</p>
        <h1>{isRegister ? "Criar conta" : "Entrar"}</h1>
        <p className="muted">
          {isRegister ? "Organize o que importa com as pessoas que importam." : "Acesse seus boards compartilhados."}
        </p>

        <form onSubmit={handleSubmit}>
          {isRegister && (
            <label>
              Nome
              <input name="name" type="text" autoComplete="name" minLength={1} maxLength={120} required />
            </label>
          )}
          <label>
            E-mail
            <input name="email" type="email" autoComplete="email" required />
          </label>
          <label>
            Senha
            <input name="password" type="password" autoComplete={isRegister ? "new-password" : "current-password"} minLength={isRegister ? 8 : 1} maxLength={128} required />
          </label>
          {error && <p className="error" role="alert">{error}</p>}
          <button className="button primary full" type="submit" disabled={loading}>
            {loading ? "Aguarde..." : isRegister ? "Criar conta" : "Entrar"}
          </button>
        </form>

        <p className="switch-auth">
          {isRegister ? "Já tem uma conta?" : "Ainda não tem uma conta?"}{" "}
          <Link href={isRegister ? "/login" : "/register"}>{isRegister ? "Entrar" : "Criar conta"}</Link>
        </p>
      </section>
    </main>
  );
}
