import { createRootRouteWithContext, Link, Outlet } from "@tanstack/react-router"
import { TanStackRouterDevtools }                  from "@tanstack/router-devtools"
import type { QueryClient }                         from "@tanstack/react-query"

interface RouterContext {
  queryClient: QueryClient
}

export const Route = createRootRouteWithContext<RouterContext>()({
  component: RootLayout,
})

function RootLayout() {
  return (
    <div className="app-layout">
      <nav className="top-nav" id="main-nav">
        <div className="nav-brand">
          <span className="nav-logo">🔍</span>
          <strong>DocSight</strong>
        </div>
        <div className="nav-links">
          <Link to="/"        activeProps={{ className: "active" }}>Accueil</Link>
          <Link to="/search"  activeProps={{ className: "active" }}>Recherche</Link>
          <Link to="/upload"  activeProps={{ className: "active" }}>Importer</Link>
        </div>
        <div className="nav-user" id="nav-user-menu">
          {/* Rempli par useAuth hook — Semaine 2 */}
        </div>
      </nav>

      <main className="app-main">
        <Outlet />
      </main>

      <footer className="app-footer">
        <p>DocSight — Propulsé par <a href="https://gitlab.com/swiss-armed-forces/cyber-command/cea/loom" target="_blank" rel="noreferrer">Loom</a> (Cyber Command Suisse)</p>
      </footer>

      {/* DevTools uniquement en développement */}
      {import.meta.env.DEV && <TanStackRouterDevtools />}
    </div>
  )
}
