/**
 * SEMAINE 1 — Couche API search
 *
 * Valide chaque réponse avec Zod à la frontière réseau.
 * Si le backend renvoie un type inattendu → erreur immédiate et localisée.
 */
import { apiClient } from "./client"
import {
  SearchResponseSchema,
  ChatResponseSchema,
  type SearchParams,
  type SearchResponse,
  type ChatResponse,
} from "../schemas/search.schema"

export const searchApi = {
  /**
   * Recherche full-text avec AbortSignal pour annulation.
   * SEMAINE 3 : TanStack Query passe le signal automatiquement.
   */
  search: async (params: SearchParams, signal?: AbortSignal): Promise<SearchResponse> => {
    const response = await apiClient.get("/search/", {
      params: {
        q:          params.q,
        tags:       params.tags?.join(",") || undefined,
        file_types: params.file_types?.join(",") || undefined,
        page:       params.page,
        page_size:  params.page_size,
      },
      signal,
    })
    return SearchResponseSchema.parse(response.data)
  },

  chat: async (question: string, documentIds?: string[]): Promise<ChatResponse> => {
    const response = await apiClient.post("/search/chat/", {
      question,
      document_ids: documentIds ?? [],
    })
    return ChatResponseSchema.parse(response.data)
  },

  getTags: async (signal?: AbortSignal): Promise<string[]> => {
    const response = await apiClient.get("/search/tags/", { signal })
    return response.data.tags as string[]
  },

  upload: async (file: File, tags?: string[]): Promise<{ document_id: string; status: string }> => {
    const formData = new FormData()
    formData.append("file", file)
    tags?.forEach((tag) => formData.append("tags", tag))

    const response = await apiClient.post("/search/upload/", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    })
    return response.data
  },

  downloadDocument: async (id: string, signal?: AbortSignal): Promise<{ blob: Blob; filename: string }> => {
    const response = await apiClient.get(`/search/documents/${id}/download/`, {
      responseType: "blob",
      signal,
    })
    
    let filename = `${id}.bin`
    const disposition = response.headers["content-disposition"]
    if (disposition) {
      const match = disposition.match(/filename="?([^"]+)"?/)
      if (match && match[1]) {
        filename = match[1]
      }
    }
    
    return { blob: response.data, filename }
  },
}
