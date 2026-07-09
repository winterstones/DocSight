import { createFileRoute, useNavigate } from "@tanstack/react-router"
import { useState } from "react"
import { useLogin } from "../../hooks/useAuth"

export const Route = createFileRoute("/login/")({
  component: LoginPage,
})

function LoginPage() {
  const [username, setUsername] = useState("")
  const [password, setPassword] = useState("")
  const loginMutation = useLogin()
  const navigate = useNavigate()

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    loginMutation.mutate(
      { username, password },
      {
        onSuccess: () => {
          navigate({ to: "/search" })
        },
      }
    )
  }

  return (
    <div className="login-container">
      <div className="login-card">
        <h1>Connexion à DocSight</h1>
        <p>Veuillez vous identifier pour accéder au portail.</p>
        <form onSubmit={handleSubmit} className="login-form">
          <div className="form-group">
            <label htmlFor="username">Nom d'utilisateur</label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Ex: admin"
              required
            />
          </div>
          <div className="form-group">
            <label htmlFor="password">Mot de passe</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Votre mot de passe"
              required
            />
          </div>
          {loginMutation.isError && (
            <div className="error-message">
              Identifiants invalides ou erreur de connexion.
            </div>
          )}
          <button type="submit" disabled={loginMutation.isPending} className="login-button">
            {loginMutation.isPending ? "Connexion en cours..." : "Se connecter"}
          </button>
        </form>
      </div>
    </div>
  )
}
