import Link from "next/link";

export default function Home() {
  return (
    <main className="landing">
      <nav><span className="brand">LifeBoard</span><Link className="button ghost" href="/login">Entrar</Link></nav>
      <section className="hero">
        <p className="eyebrow">Vida compartilhada, com clareza</p>
        <h1>Pequenos hábitos.<br />Uma visão em comum.</h1>
        <p>Crie boards para acompanhar sua semana e manter todos na mesma página.</p>
        <div className="hero-actions"><Link className="button primary" href="/register">Criar minha conta</Link><Link className="button secondary" href="/login">Já tenho conta</Link></div>
      </section>
    </main>
  );
}
