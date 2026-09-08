import axios from 'axios'

const client = axios.create({ baseURL: 'http://localhost:8000' })

client.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

export const register = (username, email, password) =>
  client.post('/auth/register', { username, email, password }).then(r => r.data)

export const login = async (username, password) => {
  const form = new URLSearchParams()
  form.append('username', username)
  form.append('password', password)
  const { data } = await client.post('/auth/login', form, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  })
  localStorage.setItem('access_token', data.access_token)
  return data
}

export const logout = () => localStorage.removeItem('access_token')
export const isLoggedIn = () => !!localStorage.getItem('access_token')

export const askAgent = (question) => client.post('/ask', { question }).then(r => r.data)
export const answerQuiz = (answers) => client.post('/answer', { answers }).then(r => r.data)
export const getMastery = () => client.get('/student/me/mastery').then(r => r.data)
export const getConcepts = () => client.get('/concepts').then(r => r.data)