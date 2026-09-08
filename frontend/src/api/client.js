import axios from 'axios'

const client = axios.create({ baseURL: 'http://localhost:8000' })

export const askAgent = (studentId, question) =>
  client.post('/ask', { student_id: studentId, question }).then(r => r.data)

export const answerQuiz = (studentId, answers) =>
  client.post('/answer', { student_id: studentId, answers }).then(r => r.data)

export const getMastery = (studentId) =>
  client.get(`/student/${studentId}/mastery`).then(r => r.data)

export const getConcepts = () =>
  client.get('/concepts').then(r => r.data)