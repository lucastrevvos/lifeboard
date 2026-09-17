"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";

import { AppHeader } from "@/components/AppHeader";
import { ProtectedPage } from "@/components/ProtectedPage";
import { ApiError, api, errorMessage } from "@/lib/api";
import type { Board, User } from "@/lib/types";

function BoardsContent({ user }: { user: User }) {
  const router = useRouter();
  const [boards, setBoards] = useState<Board[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;

    api.listBoards()
      .then((items) => {
        if (active) setBoards(items);
      })
      .catch((caught) => {
        if (!active) return;
        if (caught instanceof ApiError && caught.status === 401) {
          router.replace("/login");
          return;
        }
        setError(errorMessage(caught));
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => { active = false; };
  }, [router]);

  async function createBoard(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const nameInput = new FormData(form).get("name");
    setCreating(true);
    setError("");
    try {
      const board = await api.createBoard(String(nameInput));
      setBoards((current) => [...current, board]);
      form.reset();
    } catch (caught) {
      if (caught instanceof ApiError && caught.status === 401) {
        router.replace("/login");
        return;
      }
      setError(errorMessage(caught));
    } finally {
      setCreating(false);
    }
  }

  return (
    <><AppHeader user={user} /><main className="dashboard">
      <div className="page-heading"><div><p className="eyebrow">Seu espaço</p><h1>Boards</h1><p className="muted">Escolha um board ou crie um novo para começar.</p></div></div>
      <section className="create-panel"><h2>Novo board</h2><form className="inline-form" onSubmit={createBoard}><label className="sr-only" htmlFor="board-name">Nome do board</label><input id="board-name" name="name" placeholder="Ex.: Casa, Família, Projeto" minLength={1} maxLength={120} required /><button className="button primary" type="submit" disabled={creating}>{creating ? "Criando..." : "Criar board"}</button></form></section>
      {error && <p className="error banner" role="alert">{error}</p>}
      {loading ? <p className="loading" role="status">Carregando boards...</p> : boards.length === 0 ? <div className="empty-state"><span>✦</span><h2>Seu primeiro board começa aqui</h2><p>Use o formulário acima para criar um espaço compartilhado.</p></div> : <div className="board-grid">{boards.map((board) => <article className="board-card" key={board.id}><div className="board-icon">{board.name.charAt(0).toUpperCase()}</div><div><h2>{board.name}</h2><span className="role">{board.role}</span></div><Link className="button secondary" href={`/boards/${board.id}`}>Abrir <span aria-hidden="true">→</span></Link></article>)}</div>}
    </main></>
  );
}

export default function BoardsPage() {
  return <ProtectedPage>{(user) => <BoardsContent user={user} />}</ProtectedPage>;
}
