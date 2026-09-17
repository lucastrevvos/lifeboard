"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { ApiError, api, errorMessage } from "@/lib/api";
import type { CategoryKind, ResponseState, WeeklyBoard as WeeklyBoardData } from "@/lib/types";

const dayLabels = ["SEG", "TER", "QUA", "QUI", "SEX", "SÁB", "DOM"];
const kindLabels: Record<CategoryKind, string> = { individual: "Individual", shared: "Compartilhada" };
const stateLabels: Record<ResponseState, string> = { yes: "YES", no: "NO", pending: "PENDENTE" };
const stateSymbols: Record<ResponseState, string> = { yes: "✓", no: "✕", pending: "—" };

function formatLocalDate(date: Date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function formatShortDate(value: string) {
  const [, month, day] = value.split("-");
  return `${day}/${month}`;
}

function formatReadableDate(value: string) {
  const [year, month, day] = value.split("-");
  return `${day}/${month}/${year}`;
}

export function WeeklyBoard({ boardId }: { boardId: number }) {
  const router = useRouter();
  const [referenceDate] = useState(() => formatLocalDate(new Date()));
  const [week, setWeek] = useState<WeeklyBoardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [savingCells, setSavingCells] = useState<Set<string>>(() => new Set());
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    api.getWeeklyBoard(boardId, referenceDate)
      .then((data) => { if (active) setWeek(data); })
      .catch((caught) => {
        if (!active) return;
        if (caught instanceof ApiError && caught.status === 401) { router.replace("/login"); return; }
        setError(errorMessage(caught));
      })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [boardId, referenceDate, router]);

  async function saveResponse(categoryId: number, categoryName: string, responseDate: string, value: boolean) {
    const cellKey = `${categoryId}:${responseDate}`;
    if (savingCells.has(cellKey)) return;
    setSavingCells((current) => new Set(current).add(cellKey));
    setError("");

    try {
      const saved = await api.setResponse(boardId, categoryId, responseDate, value);
      setWeek((current) => current ? {
        ...current,
        categories: current.categories.map((category) => category.id !== saved.category_id ? category : {
          ...category,
          days: category.days.map((day) => day.date === saved.response_date ? { ...day, state: saved.state } : day),
        }),
      } : current);
    } catch (caught) {
      if (caught instanceof ApiError && caught.status === 401) { router.replace("/login"); return; }
      setError(`Não foi possível atualizar ${categoryName}: ${errorMessage(caught)}`);
    } finally {
      setSavingCells((current) => {
        const next = new Set(current);
        next.delete(cellKey);
        return next;
      });
    }
  }

  return (
    <section className="weekly-board-section" aria-labelledby="weekly-board-title">
      <div className="section-heading weekly-heading">
        <div><p className="eyebrow">Acompanhamento</p><h2 id="weekly-board-title">Quadro semanal</h2></div>
        {week && <p className="week-range">Semana {formatShortDate(week.week_start)} – {formatShortDate(week.week_end)}</p>}
      </div>
      {error && <p className="error banner" role="alert">{error}</p>}
      {loading ? <p className="loading" role="status">Carregando quadro semanal...</p> : !week ? null : week.categories.length === 0 ? <p className="weekly-empty">Este board ainda não possui categorias para acompanhar.</p> : (
        <div className="weekly-board-scroll">
          <table className="weekly-board-table">
            <thead><tr><th scope="col">Categoria</th>{week.categories[0].days.map((day, index) => <th scope="col" key={day.date}><span>{dayLabels[index]}</span><small>{formatShortDate(day.date)}</small></th>)}</tr></thead>
            <tbody>{week.categories.map((category) => <tr key={category.id}>
              <th scope="row"><strong>{category.name}</strong><span>{kindLabels[category.kind]}</span>{category.kind === "shared" && <small>Resposta compartilhada</small>}</th>
              {category.days.map((day) => {
                const cellKey = `${category.id}:${day.date}`;
                const saving = savingCells.has(cellKey);
                const readableDate = formatReadableDate(day.date);
                return <td key={day.date} className={`weekly-cell state-${day.state}`}>
                  <span className="cell-state" title={stateLabels[day.state]}><span aria-hidden="true">{stateSymbols[day.state]}</span><span className="sr-only">{stateLabels[day.state]}</span></span>
                  <div className="cell-actions" aria-label={`Resposta de ${category.name} em ${readableDate}`}>
                    <button type="button" className={day.state === "yes" ? "selected yes" : "yes"} disabled={saving} aria-label={`Marcar ${category.name} como sim em ${readableDate}`} aria-pressed={day.state === "yes"} onClick={() => saveResponse(category.id, category.name, day.date, true)}>✓</button>
                    <button type="button" className={day.state === "no" ? "selected no" : "no"} disabled={saving} aria-label={`Marcar ${category.name} como não em ${readableDate}`} aria-pressed={day.state === "no"} onClick={() => saveResponse(category.id, category.name, day.date, false)}>✕</button>
                  </div>
                  {saving && <span className="cell-saving" role="status">Salvando...</span>}
                </td>;
              })}
            </tr>)}</tbody>
          </table>
        </div>
      )}
    </section>
  );
}
