import React from "react"
import ReactDOM from "react-dom/client"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { RouterProvider, createRouter } from "@tanstack/react-router"
import { routeTree } from "./routeTree.gen" // Auto-généré par TanStack Router Vite plugin
import "./index.css"

// ─── TanStack Query client ────────────────────────────────────────────────────

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry:              1,
      staleTime:          1000 * 30,   // 30 secondes par défaut
      refetchOnWindowFocus: false,
    },
  },
})

// ─── TanStack Router ──────────────────────────────────────────────────────────

const router = createRouter({
  routeTree,
  context: { queryClient },   // Injecté dans chaque loader
})

// Typage TypeScript du routeur (pattern TanStack Router)
declare module "@tanstack/react-router" {
  interface Register {
    router: typeof router
  }
}

// ─── Rendu ────────────────────────────────────────────────────────────────────

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  </React.StrictMode>
)
