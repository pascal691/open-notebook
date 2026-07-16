import apiClient from './client'
import {
  Exam,
  ExamListItem,
  ExamSubmission,
  GenerateExamRequest,
  SubmitExamRequest,
  UpdateExamRequest,
} from '@/lib/types/exams'

export const examsApi = {
  list: async (notebookId?: string) => {
    const response = await apiClient.get<ExamListItem[]>('/exams', {
      params: notebookId ? { notebook_id: notebookId } : undefined,
    })
    return response.data
  },

  get: async (id: string, includeSolutions = false) => {
    const response = await apiClient.get<Exam>(`/exams/${id}`, {
      params: includeSolutions ? { include_solutions: true } : undefined,
    })
    return response.data
  },

  generate: async (data: GenerateExamRequest) => {
    const response = await apiClient.post<Exam>('/exams', data)
    return response.data
  },

  update: async (id: string, data: UpdateExamRequest) => {
    const response = await apiClient.put<Exam>(`/exams/${id}`, data)
    return response.data
  },

  delete: async (id: string) => {
    await apiClient.delete(`/exams/${id}`)
  },

  submit: async (id: string, data: SubmitExamRequest) => {
    const response = await apiClient.post<ExamSubmission>(`/exams/${id}/submit`, data)
    return response.data
  },

  listSubmissions: async (id: string) => {
    const response = await apiClient.get<ExamSubmission[]>(`/exams/${id}/submissions`)
    return response.data
  },

  getSubmission: async (submissionId: string) => {
    const response = await apiClient.get<ExamSubmission>(`/exam-submissions/${submissionId}`)
    return response.data
  },
}
