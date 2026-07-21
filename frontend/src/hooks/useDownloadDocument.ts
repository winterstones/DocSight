import { useState } from "react"
import { searchApi } from "../api/search.api"

export function useDownloadDocument() {
  const [isDownloading, setIsDownloading] = useState(false)
  const [error, setError] = useState<Error | null>(null)

  const download = async (documentId: string) => {
    setIsDownloading(true)
    setError(null)
    try {
      const { blob, filename } = await searchApi.downloadDocument(documentId)
      
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (err) {
      setError(err instanceof Error ? err : new Error("Erreur lors du téléchargement du document"))
      console.error("Download error:", err)
    } finally {
      setIsDownloading(false)
    }
  }

  return { download, isDownloading, error }
}
