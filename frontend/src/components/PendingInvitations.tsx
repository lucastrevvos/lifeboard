"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { ApiError, api, errorMessage } from "@/lib/api";
import type { PendingInvitation } from "@/lib/types";

type PendingInvitationsProps = {
  onAccepted: () => Promise<void>;
};

export function PendingInvitations({ onAccepted }: PendingInvitationsProps) {
  const router = useRouter();
  const [invitations, setInvitations] = useState<PendingInvitation[]>([]);
  const [loading, setLoading] = useState(true);
  const [processingId, setProcessingId] = useState<number | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;

    api.listPendingInvitations()
      .then((items) => {
        if (active) setInvitations(items);
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

  async function respond(invitationId: number, action: "accept" | "decline") {
    setProcessingId(invitationId);
    setError("");

    try {
      if (action === "accept") {
        await api.acceptInvitation(invitationId);
      } else {
        await api.declineInvitation(invitationId);
      }

      setInvitations((current) => current.filter((item) => item.id !== invitationId));

      if (action === "accept") {
        await onAccepted();
      }
    } catch (caught) {
      if (caught instanceof ApiError && caught.status === 401) {
        router.replace("/login");
        return;
      }
      setError(errorMessage(caught));
    } finally {
      setProcessingId(null);
    }
  }

  return (
    <section className="content-section" aria-labelledby="pending-invitations-title">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Colaboração</p>
          <h2 id="pending-invitations-title">Convites pendentes</h2>
        </div>
      </div>

      {error && <p className="error banner" role="alert">{error}</p>}
      {loading ? (
        <p className="loading" role="status">Carregando convites...</p>
      ) : invitations.length === 0 ? (
        <p className="section-empty">Você não tem convites pendentes.</p>
      ) : (
        <div className="invitation-list">
          {invitations.map((invitation) => {
            const processing = processingId === invitation.id;
            return (
              <article className="invitation-card" key={invitation.id}>
                <div>
                  <h3>{invitation.board_name}</h3>
                  <p>Convite de <strong>{invitation.invited_by_name}</strong></p>
                  <span className="meta">Pendente · {new Intl.DateTimeFormat("pt-BR", { dateStyle: "medium" }).format(new Date(invitation.created_at))}</span>
                </div>
                <div className="card-actions">
                  <button className="button primary" type="button" disabled={processingId !== null} onClick={() => respond(invitation.id, "accept")}>{processing ? "Processando..." : "Aceitar"}</button>
                  <button className="button secondary" type="button" disabled={processingId !== null} onClick={() => respond(invitation.id, "decline")}>Recusar</button>
                </div>
              </article>
            );
          })}
        </div>
      )}
    </section>
  );
}
