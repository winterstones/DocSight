/**
 * SEMAINE 2 — Client Axios avec intercepteur de refresh automatique
 *
 * Pattern senior :
 *  - withCredentials: true → les cookies HttpOnly sont envoyés automatiquement
 *  - Intercepteur 401 → refresh automatique → retry de la requête originale
 *  - React ne manipule jamais les tokens
 */
import axios, { AxiosError } from "axios"

const BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000"

export const apiClient = axios.create({
  baseURL:         `${BASE_URL}/api`,
  withCredentials: true,  // Envoie les cookies HttpOnly automatiquement
  headers: {
    "Content-Type": "application/json",
  },
})

// ─── Intercepteur de réponse : refresh automatique ───────────────────────────

let isRefreshing    = false
let failedQueue:    Array<{ resolve: (v: unknown) => void; reject: (e: unknown) => void }> = []

const processQueue  = (error: AxiosError | null) => {
  failedQueue.forEach(({ resolve, reject }) => error ? reject(error) : resolve(null))
  failedQueue = []
}

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as typeof error.config & { _retry?: boolean }

    // Si 401 et pas encore retryé → tenter un refresh
    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        // Une requête de refresh est déjà en cours → mettre en file d'attente
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        }).then(() => apiClient(originalRequest))
      }

      originalRequest._retry = true
      isRefreshing           = true

      try {
        // Refresh → Django pose un nouveau access_token dans le cookie
        await apiClient.post("/auth/refresh/")
        processQueue(null)
        return apiClient(originalRequest)  // Rejoue la requête originale
      } catch (refreshError) {
        processQueue(refreshError as AxiosError)
        // Refresh échoué → session expirée → rediriger vers login
        window.location.href = "/login"
        return Promise.reject(refreshError)
      } finally {
        isRefreshing = false
      }
    }

    return Promise.reject(error)
  }
)
