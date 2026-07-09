# DocSight JWT Double-Cookie Authentication

DocSight implements a secure token authentication architecture using two JSON Web Tokens (JWT) stored in HTTP-only, secure cookies. This approach prevents client-side JavaScript access (XSS protection) while maintaining seamless session persistence.

## 1. Token Lifetime & Configuration

The parameters are configured in the Django settings (`base.py`) under the `SIMPLE_JWT` configuration dictionary:

| Parameter | Value | Location / Cookie Name | Purpose |
| :--- | :--- | :--- | :--- |
| `ACCESS_TOKEN_LIFETIME` | 15 Minutes | `access_token` | Short-lived token for authorizing API requests. |
| `REFRESH_TOKEN_LIFETIME` | 7 Days | `refresh_token` | Long-lived token used to request a new access token. |
| `AUTH_COOKIE_HTTP_ONLY` | `True` | N/A | Restricts access to the cookie via browser JS. |
| `AUTH_COOKIE_SECURE` | Dependent (`False` in dev) | N/A | Only transmits cookie over HTTPS. |
| `AUTH_COOKIE_SAMESITE` | `Strict` | N/A | Prevents CSRF transmission of cookies. |

---

## 2. Backend Authentication Endpoints

All authentication endpoints are located under `/api/auth/`:

### 2.1. Login
- **Endpoint**: `POST /api/auth/login/`
- **Request Body**:
  ```json
  {
    "username": "operator_a",
    "password": "operator123"
  }
  ```
- **Response Body**:
  ```json
  {
    "user": {
      "id": 2,
      "username": "operator_a",
      "email": "opa@docsight.local",
      "first_name": "",
      "last_name": "",
      "role": "operator"
    }
  }
  ```
- **Response Headers**: Sets `access_token` and `refresh_token` cookies.

### 2.2. Logout
- **Endpoint**: `POST /api/auth/logout/`
- **Response Body**:
  ```json
  {
    "detail": "Logged out successfully."
  }
  ```
- **Action**: Blacklists the current refresh token and clears both cookies.

### 2.3. Token Refresh
- **Endpoint**: `POST /api/auth/refresh/`
- **Request Headers**: Expects `refresh_token` cookie.
- **Response Body**:
  ```json
  {
    "detail": "Token refreshed."
  }
  ```
- **Response Headers**: Sets a new `access_token` and rotated `refresh_token` cookie.

### 2.4. Profile Verification
- **Endpoint**: `GET /api/auth/me/`
- **Response Body**:
  ```json
  {
    "user": {
      "id": 2,
      "username": "operator_a",
      "email": "opa@docsight.local",
      "first_name": "",
      "last_name": "",
      "role": "operator"
    }
  }
  ```

---

## 3. Frontend Integration Flow

The frontend calls the API using Axios with automatic cookie propagation and token refresh.

```
React App               Axios Client                DocSight API
    |                        |                            |
    |---- Get Data --------->|                            |
    |                        |---- GET /api/search/ ----->| (Cookie sent automatically)
    |                        |<--- 401 Unauthorized ------| (Access Token Expired)
    |                        |                            |
    |                        |---- POST /auth/refresh/ -->| (Sends Refresh Token)
    |                        |<--- 200 OK (New Cookies) --| (Sets New Access Cookie)
    |                        |                            |
    |                        |---- GET /api/search/ ----->| (Retries original request)
    |<--- Render Data -------|<--- 200 OK (Data) ---------|
```

### Axios Interceptor Implementation

```typescript
import axios, { AxiosError } from "axios"

export const apiClient = axios.create({
  baseURL: "http://localhost:8000/api",
  withCredentials: true, // Crucial: forces browser to include cookies automatically
})

let isRefreshing = false
let failedQueue: Array<{ resolve: (v: unknown) => void; reject: (e: unknown) => void }> = []

const processQueue = (error: AxiosError | null) => {
  failedQueue.forEach(({ resolve, reject }) => error ? reject(error) : resolve(null))
  failedQueue = []
}

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as typeof error.config & { _retry?: boolean }

    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        }).then(() => apiClient(originalRequest))
      }

      originalRequest._retry = true
      isRefreshing = true

      try {
        await apiClient.post("/auth/refresh/")
        processQueue(null)
        return apiClient(originalRequest) // Retry original call
      } catch (refreshError) {
        processQueue(refreshError as AxiosError)
        window.location.href = "/login" // Session expired -> redirect
        return Promise.reject(refreshError)
      } finally {
        isRefreshing = false
      }
    }
    return Promise.reject(error)
  }
)
```
