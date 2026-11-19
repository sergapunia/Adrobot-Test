import { Link, NavLink, useLocation } from "react-router-dom";
import type { ReactNode } from "react";

export function Layout({ children }: { children: ReactNode }) {
  const location = useLocation();
  const editorActive = location.pathname === "/editor" || location.pathname.startsWith("/campaigns/");

  return (
    <div className="page">
      <header className="topbar">
        <Link to="/" className="brand">
          <span className="brand-mark" />
          Keitaro
        </Link>
        <nav className="nav">
          <NavLink to="/" end>
            Создать
          </NavLink>
          <NavLink to="/editor" className={() => (editorActive ? "active" : "")}>
            Редактор
          </NavLink>
        </nav>
      </header>
      <main className="content">{children}</main>
    </div>
  );
}
