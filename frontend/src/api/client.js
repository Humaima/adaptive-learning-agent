import axios from 'axios'

const client = axios.create({ baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000' })

client.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

let isRefreshing = false

client.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    if (error.response?.status === 401 && !originalRequest._retry && !isRefreshing) {
      originalRequest._retry = true
      isRefreshing = true
      try {
        const refreshToken = localStorage.getItem('refresh_token')
        const { data } = await axios.post(`${client.defaults.baseURL}/auth/refresh`, { refresh_token: refreshToken })
        localStorage.setItem('access_token', data.access_token)
        localStorage.setItem('refresh_token', data.refresh_token)
        originalRequest.headers.Authorization = `Bearer ${data.access_token}`
        return client(originalRequest)
      } catch {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        window.location.href = '/login'
      } finally {
        isRefreshing = false
      }
    }
    return Promise.reject(error)
  }
)

const storeTokens = (data) => {
  localStorage.setItem('access_token', data.access_token)
  localStorage.setItem('refresh_token', data.refresh_token)
  return data
}

export const register = (username, email, password) =>
  client.post('/auth/register', { username, email, password }).then(r => storeTokens(r.data))

export const login = async (username, password) => {
  const form = new URLSearchParams()
  form.append('username', username)
  form.append('password', password)
  const { data } = await client.post('/auth/login', form, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  })
  return storeTokens(data)
}

export const logout = () => {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
}
export const isLoggedIn = () => !!localStorage.getItem('access_token')

export const askAgent = (question) => client.post('/ask', { question }).then(r => r.data)
export const answerQuiz = (answers) => client.post('/answer', { answers }).then(r => r.data)
export const getMastery = () => client.get('/student/me/mastery').then(r => r.data)
export const getConcepts = () => client.get('/concepts').then(r => r.data)
export const getLearningPath = () => client.get('/student/me/learning-path').then(r => r.data)
export const addNote = (concept_id, title, content) =>
  client.post('/notes', { concept_id, title, content }).then(r => r.data)
export const getNotes = () => client.get('/notes').then(r => r.data)
export const deleteNote = (id) => client.delete(`/notes/${id}`).then(r => r.data)

export const generateFlashcards = (concept_id) => client.post('/flashcards/generate', { concept_id }).then(r => r.data)
export const getDueFlashcards = () => client.get('/flashcards/due').then(r => r.data)
export const reviewFlashcard = (id, knew_it) => client.post(`/flashcards/${id}/review`, { knew_it }).then(r => r.data)
export const getQuizHistory = () => client.get('/quiz-history').then(r => r.data)