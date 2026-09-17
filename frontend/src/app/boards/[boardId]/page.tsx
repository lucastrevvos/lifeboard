"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { AppHeader } from "@/components/AppHeader";
import { BoardManagement } from "@/components/BoardManagement";
import { ProtectedPage } from "@/components/ProtectedPage";
import { WeeklyBoard } from "@/components/WeeklyBoard";
import { ApiError, api, errorMessage } from "@/lib/api";
import type { Board, User } from "@/lib/types";

function BoardContent({ user, boardId }: { user: User; boardId: string }) {
  const router = useRouter();
  const numericBoardId = Number(boardId);
  const validBoardId = Number.isInteger(numericBoardId) && numericBoardId > 0;
  const [board, setBoard] = useState<Board | null>(null);
  const [loading, setLoading] = useState(validBoardId);
  const [error, setError] = useState(validBoardId ? "" : "Board inválido.");

  useEffect(() => {
    let active = true;
    if (!validBoardId) return () => { active = false; };
    api.listBoards()
      .then((items) => {
        if (!active) return;
        const currentBoard = items.find((item) => item.id === numericBoardId);
        if (!currentBoard) { setError("Board não encontrado ou você não possui acesso a ele."); return; }
        setBoard(currentBoard);
      })
      .catch((caught) => {
        if (!active) return;
        if (caught instanceof ApiError && caught.status === 401) { router.replace("/login"); return; }
        setError(errorMessage(caught));
      })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [numericBoardId, router, validBoardId]);

  return <><AppHeader user={user} /><main className="dashboard">
    <Link className="back-link" href="/boards">← Voltar aos boards</Link>
    {loading ? <p className="loading" role="status">Carregando board...</p> : error ? <p className="error banner" role="alert">{error}</p> : board ? <><div className="page-heading board-heading"><div><p className="eyebrow">Board</p><h1>{board.name}</h1><p className="muted">Acompanhe a semana e organize este espaço.</p></div></div><WeeklyBoard boardId={board.id} /><BoardManagement board={board} /></> : null}
  </main></>;
}

export default function BoardPage() {
  const { boardId } = useParams<{ boardId: string }>();
  return <ProtectedPage>{(user) => <BoardContent user={user} boardId={boardId} />}</ProtectedPage>;
}
