/**
 * SEMAINE 1 — Zod : Validation à la frontière réseau
 *
 * Ces schemas sont la source de vérité des types frontend.
 * Types TypeScript inférés automatiquement via z.infer<>
 * => 0 duplication de définitions de types.
 */
import { z } from "zod"

// ─── Enums ────────────────────────────────────────────────────────────────────

export const FileTypeSchema = z.enum([
  "pdf", "docx", "xlsx", "pptx", "image", "email", "archive", "unknown",
])

export const SearchStatusSchema = z.enum(["idle", "loading", "success", "error"])

// ─── Entités ──────────────────────────────────────────────────────────────────

export const SearchResultSchema = z.object({
  id:              z.string(),
  title:           z.string(),
  content_preview: z.string(),
  file_type:       FileTypeSchema,
  tags:            z.array(z.string()),
  score:           z.number().min(0).max(1),
  thumbnail_url:   z.string().url().nullable(),
})

export const SearchResponseSchema = z.object({
  results:   z.array(SearchResultSchema),
  total:     z.number().int().nonnegative(),
  query:     z.string(),
  page:      z.number().int().positive(),
  page_size: z.number().int().positive(),
})

export const ChatResponseSchema = z.object({
  answer:  z.string(),
  sources: z.array(SearchResultSchema),
})

export const UserSchema = z.object({
  id:         z.number(),
  username:   z.string(),
  email:      z.string().email(),
  first_name: z.string(),
  last_name:  z.string(),
  role:       z.enum(["operator", "supervisor", "admin"]),
})

// ─── Search params (TanStack Router) ─────────────────────────────────────────

export const SearchParamsSchema = z.object({
  q:          z.string().default(""),
  tags:       z.array(z.string()).default([]),
  file_types: z.array(z.string()).default([]),
  page:       z.coerce.number().int().positive().default(1),
  page_size:  z.coerce.number().int().positive().max(100).default(20),
})

// ─── Types inférés ────────────────────────────────────────────────────────────

export type SearchResult   = z.infer<typeof SearchResultSchema>
export type SearchResponse = z.infer<typeof SearchResponseSchema>
export type ChatResponse   = z.infer<typeof ChatResponseSchema>
export type User           = z.infer<typeof UserSchema>
export type FileType       = z.infer<typeof FileTypeSchema>
export type SearchParams   = z.infer<typeof SearchParamsSchema>
