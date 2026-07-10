import { createRootRouteWithContext, Link, Outlet } from "@tanstack/react-router"
import { TanStackRouterDevtools }                  from "@tanstack/router-devtools"
import type { QueryClient }                         from "@tanstack/react-query"
import { useAuth, useLogout } from "../hooks/useAuth"
import { ChatProvider } from "../context/ChatContext"
import { ChatWidget } from "../components/ChatWidget"

interface RouterContext {
  queryClient: QueryClient
}

export const Route = createRootRouteWithContext<RouterContext>()({
  component: RootLayout,
})

function RootLayout() {
  const { data: user, isLoading } = useAuth()
  const logoutMutation = useLogout()

  return (
    <ChatProvider>
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
          {isLoading ? (
            <span style={{ fontSize: '0.9rem', color: 'var(--color-text-muted)' }}>...</span>
          ) : user ? (
            <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
              <span style={{ fontSize: '0.9rem' }}>{user.username}</span>
              <button 
                className="btn btn-secondary" 
                style={{ padding: '0.4rem 0.8rem', fontSize: '0.85rem' }} 
                onClick={() => logoutMutation.mutate()}
                disabled={logoutMutation.isPending}
              >
                Déconnexion
              </button>
            </div>
          ) : (
            <Link to="/login" className="btn btn-primary" style={{ padding: '0.4rem 0.8rem', fontSize: '0.85rem' }}>
              Connexion
            </Link>
          )}
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
      <ChatWidget />
    </div>
    </ChatProvider>
  )
}
