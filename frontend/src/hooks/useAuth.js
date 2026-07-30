export const useAuth = () => {
  const getToken = () => localStorage.getItem('access_token')

  const setToken = (token) => {
    localStorage.setItem('access_token', token)
  }

  const clearToken = () => {
    localStorage.removeItem('access_token')
  }

  const isAuthenticated = () => !!getToken()

  return {
    getToken,
    setToken,
    clearToken,
    isAuthenticated,
  }
}
