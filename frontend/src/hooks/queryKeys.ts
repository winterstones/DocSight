/**
 * SEMAINE 3 — TanStack Query : QueryKeys structurées
 *
 * Pattern senior : les queryKeys sont une API interne.
 * Structure hiérarchique pour invalidations ciblées.
 */
import type { SearchParams } from "../schemas/search.schema"

export const searchKeys = {
  all:    ()                   => ["search"]                           as const,
  lists:  ()                   => ["search", "list"]                  as const,
  list:   (params: SearchParams) => ["search", "list", params]        as const,
  tags:   ()                   => ["search", "tags"]                  as const,
  chat:   (question: string)   => ["search", "chat", question]        as const,
}
