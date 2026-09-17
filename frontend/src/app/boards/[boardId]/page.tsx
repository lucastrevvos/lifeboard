"use client";

import Link from "next/link";
import { useParams } from "next/navigation";

import { AppHeader } from "@/components/AppHeader";
import { ProtectedPage } from "@/components/ProtectedPage";

export default function BoardPage() {
  const { boardId } = useParams<{ boardId: string }>();

  return <ProtectedPage>{(user) => <><AppHeader user={user} /><main className="dashboard"><Link className="back-link" href="/boards">← Voltar aos boards</Link><section className="placeholder"><p className="eyebrow">Board #{boardId}</p><h1>Seu quadro semanal vem a seguir</h1><p>Nesta primeira etapa, a seleção do board já está funcionando. Categorias e acompanhamento semanal serão implementados na próxima slice.</p><Link className="button primary" href="/boards">Escolher outro board</Link></section></main></>}</ProtectedPage>;
}
