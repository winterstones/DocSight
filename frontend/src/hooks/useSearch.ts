/**
 * SEMAINE 3 — TanStack Query hooks
 *
 * Concepts démontrés :
 *  - AbortSignal : requête annulée si params changent avant réponse
 *  - keepPreviousData : pas de flash vide entre pages
 *  - staleTime : cache intelligent (pas de refetch inutile)
 *  - useMutation avec invalidation ciblée
 */
import {
  useQuery,
  useMutation,
  useQueryClient,
  keepPreviousData,
} from "@tanstack/react-query"
import { searchApi } from "../api/search.api"
import { searchKeys } from "./queryKeys"
import type { SearchParams } from "../schemas/search.schema"

// ─── Hook : Recherche principale ──────────────────────────────────────────────

export function useSearch(params: SearchParams) {
  return useQuery({
    queryKey: searchKeys.list(params),

    queryFn: ({ signal }) =>
      // AbortSignal passé par TanStack Query → axios annule la requête HTTP
      // si les params changent avant que la réponse arrive (race condition éliminée)
      searchApi.search(params, signal),

    enabled:           true,  // Permet de charger les résultats initiaux (vide)
    staleTime:         1000 * 30,             // Résultats frais 30 secondes
    placeholderData:   keepPreviousData,      // Garde les anciens résultats pendant le chargement
    retry:             1,
  })
}

// ─── Hook : Tags disponibles ──────────────────────────────────────────────────

export function useTags() {
  return useQuery({
    queryKey: searchKeys.tags(),
    queryFn:  ({ signal }) => searchApi.getTags(signal),
    staleTime: 1000 * 60 * 5,  // Les tags changent rarement → cache 5min
  })
}

// ─── Hook : Upload de document ────────────────────────────────────────────────

export function useUploadDocument() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ file, tags }: { file: File; tags?: string[] }) =>
      searchApi.upload(file, tags),

    onSuccess: () => {
      // Invalide TOUS les caches de recherche → le nouveau document apparaît
      queryClient.invalidateQueries({ queryKey: searchKeys.all() })
    },
  })
}

// ─── Hook : Chat RAG ─────────────────────────────────────────────────────────

export function useChat() {
  return useMutation({
    mutationFn: ({ question, documentIds }: { question: string; documentIds?: string[] }) =>
      searchApi.chat(question, documentIds),
  })
}
