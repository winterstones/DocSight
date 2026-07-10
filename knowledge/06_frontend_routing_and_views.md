# Frontend Routing, Authentication Hooks & Search Page Views

DocSight's frontend is built using React 18, TanStack Router (v1) for type-safe routing, TanStack Query (v5) for asynchronous state management, and TanStack Table (v8) for tabular search results formatting.

---

## 1. Routing Structure & Context

The router is configured with a type-safe `RouterContext` to inject dependencies (like `QueryClient`) into loaders for prefetching data.

```
       +---------------------------------------------+
       |             __root.tsx Layout               |
       |  (Nav Brand, Main Nav Links, User Info/Out) |
       +---------------------------------------------+
                              |
         +--------------------+--------------------+
         |                                         |
         v                                         v
   /login/ Route                            /search/ Route
  (LoginPage form,                        (SearchPage views, loader,
   useLogin mutation)                      validateSearch schema)
```

### 1.1. Root Layout (`__root.tsx`)
- Renders the global layout including the top navigation bar (`#main-nav`) and footer.
- The user menu (`#nav-user-menu`) displays either:
  - An inline loading indicator during verification checks.
  - A connection link redirecting to `/login` if unauthenticated.
  - The active user's username alongside a `Log Out` button if authenticated.

### 1.2. Login Page (`/login/`)
- A simple, dedicated credentials form matching standard email/password parameters.
- Uses the `useLogin` mutation hook and redirects the user to `/search` upon successful verification.

### 1.3. Search Route (`/search/`)
- Integrates TanStack Router's `validateSearch` parameter matching the Zod validation schema:
  - `q` (string query, defaults to `""`).
  - `tags` (array of strings, defaults to `[]`).
  - `file_types` (array of strings, defaults to `[]`).
  - `page` (positive integer, defaults to `1`).
  - `page_size` (positive integer, defaults to `20`).
- **Loader Dependency**: Watches query changes and pre-fetches data via `queryClient.prefetchQuery` in the route loader before mounting the view.

---

## 2. Authentication Hooks (`hooks/useAuth.ts`)

Asynchronous authentication state is managed through TanStack Query queries and mutations:

| Hook | Operation Type | Cache Key | Action & Behaviors |
| :--- | :--- | :--- | :--- |
| `useAuth` | Query | `["auth", "me"]` | Fetches `/auth/me/`. Disable retries on `401` errors. `staleTime` is set to 5 minutes. |
| `useIsAdmin` | Helper | Dependent | Reads `useAuth` data, returns `True` if `role == "admin"`. |
| `useIsOperator`| Helper | Dependent | Reads `useAuth` data, returns `True` if role is operator, supervisor, or admin. |
| `useLogin` | Mutation | N/A | Submits credentials. On success, invalidates the `["auth", "me"]` cache to trigger a user profile refetch. |
| `useLogout` | Mutation | N/A | Calls backend logout. On success, clears the entire query client cache and redirects to `/login`. |

### React Query Hooks Definition

```typescript
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { authApi } from "../api/auth.api"

export const authKeys = {
  all: ["auth"] as const,
  me: () => [...authKeys.all, "me"] as const,
}

export function useAuth() {
  return useQuery({
    queryKey: authKeys.me(),
    queryFn: ({ signal }) => authApi.me({ signal }),
    retry: false,
    staleTime: 1000 * 60 * 5,
  })
}

export function useLogin() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: authApi.login,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: authKeys.me() })
    },
  })
}

export function useLogout() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: authApi.logout,
    onSuccess: () => {
      queryClient.clear()
      window.location.href = "/login"
    },
  })
}
```

---

## 3. Search Page Layout & Interactions

The search page (`routes/search/index.tsx`) integrates advanced UI operations matching server-side capabilities.

### 3.1. Query Debouncing
To prevent excessive backend loads on every keystroke, input changes are debounced by `300ms` before calling the router navigator:
```typescript
const handleSearch = (q: string) => {
  if (debounceRef.current) clearTimeout(debounceRef.current)
  debounceRef.current = setTimeout(() => {
    navigate({ search: (prev) => ({ ...prev, q, page: 1 }) })
  }, 300)
}
```

### 3.2. Sidebar Filters
The sidebar houses query checkboxes enabling operators to toggle file type filters and document tags.
- Toggling a filter updates the route's search parameters:
  ```typescript
  const toggleTag = (tag: string) => {
    navigate({
      search: (prev) => ({
        ...prev,
        page: 1,
        tags: prev.tags.includes(tag) ? prev.tags.filter(t => t !== tag) : [...prev.tags, tag]
      })
    })
  }
  ```

### 3.3. View Rendering Modes (List vs. Grid)
Users can toggle between two visual layouts:
- **List View**: Renders results inside a structured HTML `<table>` using `useReactTable` containing columns for document titles, file types, document tags, and search scores.
- **Grid View**: Renders a CSS grid layout composed of individual `<DocumentCard>` components.

```typescript
export function DocumentCard({ document, view = "grid" }) {
  return (
    <div className={`document-card ${view}`}>
      {document.thumbnail_url ? (
        <img src={document.thumbnail_url} alt={document.title} className="doc-thumbnail" />
      ) : (
        <div className="doc-thumbnail placeholder">
          <span className={`badge badge-${document.file_type}`}>{document.file_type}</span>
        </div>
      )}
      <div className="doc-content">
        <h3 className="doc-title">{document.title}</h3>
        <p className="doc-preview">{document.content_preview}</p>
        <div className="doc-meta">
          <div className="doc-tags">
            {document.tags.map(tag => <span key={tag} className="tag">{tag}</span>)}
          </div>
          <span className="doc-score">Relevance: {Math.round(document.score * 100)}%</span>
        </div>
      </div>
    </div>
  )
}
```

### 3.4. Pagination Controls
Server-side pagination is driven directly by updating the router search parameters (`page` parameter), triggering a stale cache invalidate and query reload:
- **Previous page action**: `navigate({ search: (prev) => ({ ...prev, page: prev.page - 1 }) })`
- **Next page action**: `navigate({ search: (prev) => ({ ...prev, page: prev.page + 1 }) })`
