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
    retry: false, // Ne pas retry les erreurs 401
    staleTime: 1000 * 60 * 5, // 5 minutes
  })
}

export function useIsAdmin() {
  const { data: user } = useAuth()
  return user?.role === "admin"
}

export function useIsOperator() {
  const { data: user } = useAuth()
  return user?.role === "operator" || user?.role === "supervisor" || user?.role === "admin"
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
