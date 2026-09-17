"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";

import { ApiError, api, errorMessage } from "@/lib/api";
import type { Board, Category, CategoryKind } from "@/lib/types";

const kindLabels: Record<CategoryKind, string> = { individual: "Individual", shared: "Compartilhada" };

function sortCategories(categories: Category[]) {
  return [...categories].sort((left, right) => left.position - right.position || left.id - right.id);
}

type BoardManagementProps = {
  board: Board;
  onCategoriesChanged: () => void;
};

export function BoardManagement({ board, onCategoriesChanged }: BoardManagementProps) {
  const router = useRouter();
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [categoryError, setCategoryError] = useState("");
  const [creating, setCreating] = useState(false);
  const [categoryMutation, setCategoryMutation] = useState(false);
  const [deactivatingCategoryId, setDeactivatingCategoryId] = useState<number | null>(null);
  const [inviteError, setInviteError] = useState("");
  const [inviteSuccess, setInviteSuccess] = useState("");
  const [inviting, setInviting] = useState(false);

  useEffect(() => {
    let active = true;
    api.listCategories(board.id)
      .then((items) => { if (active) setCategories(sortCategories(items)); })
      .catch((caught) => {
        if (!active) return;
        if (caught instanceof ApiError && caught.status === 401) { router.replace("/login"); return; }
        setCategoryError(errorMessage(caught));
      })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [board.id, router]);

  async function createCategory(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    setCreating(true);
    setCategoryError("");
    try {
      const category = await api.createCategory(board.id, {
        name: String(data.get("name")),
        kind: String(data.get("kind")) as CategoryKind,
        position: Number(data.get("position")),
      });
      setCategories((current) => sortCategories([...current, category]));
      form.reset();
      onCategoriesChanged();
    } catch (caught) {
      if (caught instanceof ApiError && caught.status === 401) { router.replace("/login"); return; }
      setCategoryError(errorMessage(caught));
    } finally { setCreating(false); }
  }

  async function moveCategory(index: number, direction: -1 | 1) {
    const targetIndex = index + direction;
    if (targetIndex < 0 || targetIndex >= categories.length) return;

    const candidate = [...categories];
    [candidate[index], candidate[targetIndex]] = [candidate[targetIndex], candidate[index]];
    setCategoryMutation(true);
    setCategoryError("");

    try {
      const reordered = await api.reorderCategories(
        board.id,
        candidate.map((category) => category.id),
      );
      setCategories(reordered);
      onCategoriesChanged();
    } catch (caught) {
      if (caught instanceof ApiError && caught.status === 401) { router.replace("/login"); return; }
      setCategoryError(errorMessage(caught));
    } finally {
      setCategoryMutation(false);
    }
  }

  async function deactivateCategory(category: Category) {
    const confirmed = window.confirm(
      `Desativar a categoria "${category.name}"?\n\nEla deixará de aparecer no quadro ativo. As respostas existentes serão preservadas.`,
    );
    if (!confirmed) return;

    setCategoryMutation(true);
    setDeactivatingCategoryId(category.id);
    setCategoryError("");

    try {
      await api.deactivateCategory(board.id, category.id);
      setCategories((current) => current.filter((item) => item.id !== category.id));
      onCategoriesChanged();
    } catch (caught) {
      if (caught instanceof ApiError && caught.status === 401) { router.replace("/login"); return; }
      setCategoryError(errorMessage(caught));
    } finally {
      setCategoryMutation(false);
      setDeactivatingCategoryId(null);
    }
  }

  async function inviteMember(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const email = String(new FormData(form).get("email"));
    setInviting(true);
    setInviteError("");
    setInviteSuccess("");
    try {
      await api.inviteMember(board.id, email);
      setInviteSuccess(`Convite enviado para ${email}.`);
      form.reset();
    } catch (caught) {
      if (caught instanceof ApiError && caught.status === 401) { router.replace("/login"); return; }
      setInviteError(errorMessage(caught));
    } finally { setInviting(false); }
  }

  return (
    <div className="management-grid">
      <section className="content-section" aria-labelledby="categories-title">
        <div className="section-heading">
          <div><p className="eyebrow">Organização</p><h2 id="categories-title">Categorias</h2></div>
          <span className="role-badge">{board.role === "owner" ? "Proprietário" : "Membro"}</span>
        </div>
        {categoryError && <p className="error banner" role="alert">{categoryError}</p>}
        {loading ? <p className="loading" role="status">Carregando categorias...</p> : categories.length === 0 ? <p className="section-empty">Nenhuma categoria ativa neste board.</p> : (
          <div className="category-list">{categories.map((category, index) => <article className="category-row" key={category.id}><div className="category-details"><h3>{category.name}</h3><span className={`kind kind-${category.kind}`}>{kindLabels[category.kind]}</span><span className="position">Posição {category.position}</span></div>{board.role === "owner" && <div className="category-actions"><div className="category-order-actions"><button className="button secondary" type="button" disabled={categoryMutation || creating || index === 0} aria-label={`Mover ${category.name} para cima`} onClick={() => moveCategory(index, -1)}>↑ Subir</button><button className="button secondary" type="button" disabled={categoryMutation || creating || index === categories.length - 1} aria-label={`Mover ${category.name} para baixo`} onClick={() => moveCategory(index, 1)}>↓ Descer</button></div><button className="button destructive" type="button" disabled={categoryMutation || creating} onClick={() => deactivateCategory(category)}>{deactivatingCategoryId === category.id ? "Desativando..." : "Desativar"}</button></div>}</article>)}</div>
        )}
        {board.role === "owner" && <div className="management-form"><h3>Nova categoria</h3><form onSubmit={createCategory}>
          <label htmlFor="category-name">Nome<input id="category-name" name="name" minLength={1} maxLength={120} required /></label>
          <div className="form-row"><label htmlFor="category-kind">Tipo<select id="category-kind" name="kind" defaultValue="individual"><option value="individual">Individual</option><option value="shared">Compartilhada</option></select></label><label htmlFor="category-position">Posição<input id="category-position" name="position" type="number" min={0} step={1} defaultValue={0} required /></label></div>
          <button className="button primary" type="submit" disabled={creating || categoryMutation}>{creating ? "Criando..." : "Criar categoria"}</button>
        </form></div>}
      </section>
      {board.role === "owner" && <section className="content-section" aria-labelledby="invite-member-title">
        <div className="section-heading"><div><p className="eyebrow">Membros</p><h2 id="invite-member-title">Convidar membro</h2></div></div>
        <p className="muted">Envie um convite para uma pessoa que já possui cadastro no LifeBoard.</p>
        {inviteError && <p className="error banner" role="alert">{inviteError}</p>}
        {inviteSuccess && <p className="success banner" role="status">{inviteSuccess}</p>}
        <form className="inline-form invite-form" onSubmit={inviteMember}><label className="sr-only" htmlFor="invite-email">E-mail da pessoa</label><input id="invite-email" name="email" type="email" placeholder="pessoa@exemplo.com" required /><button className="button primary" type="submit" disabled={inviting}>{inviting ? "Enviando..." : "Enviar convite"}</button></form>
      </section>}
    </div>
  );
}
