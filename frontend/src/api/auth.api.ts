import { apiClient } from "./client"
import type { User } from "../schemas/search.schema"

export const authApi = {
  login: async (credentials: Record<string, string>) => {
    const { data } = await apiClient.post<{ message: string }>("/auth/login/", credentials)
    return data
  },
  
  logout: async () => {
    const { data } = await apiClient.post<{ message: string }>("/auth/logout/")
    return data
  },
  
  me: async ({ signal }: { signal?: AbortSignal } = {}) => {
    const { data } = await apiClient.get<User>("/auth/me/", { signal })
    return data
  },
}
