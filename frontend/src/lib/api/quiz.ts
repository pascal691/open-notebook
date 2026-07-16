import apiClient from './client'
import { Quiz, QuizGenerateRequest } from '@/lib/types/quiz'

export const quizApi = {
  generate: async (notebookId: string, payload: QuizGenerateRequest) => {
    const response = await apiClient.post<Quiz>(
      `/notebooks/${notebookId}/quizzes`,
      payload
    )
    return response.data
  },

  list: async (notebookId: string) => {
    const response = await apiClient.get<Quiz[]>(
      `/notebooks/${notebookId}/quizzes`
    )
    return response.data
  },

  get: async (quizId: string) => {
    const response = await apiClient.get<Quiz>(`/quizzes/${quizId}`)
    return response.data
  },

  delete: async (quizId: string) => {
    await apiClient.delete(`/quizzes/${quizId}`)
  },
}
