import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { examsApi } from '@/lib/api/exams'
import { useToast } from '@/lib/hooks/use-toast'
import { useTranslation } from '@/lib/hooks/use-translation'
import { getApiErrorMessage } from '@/lib/utils/error-handler'
import {
  GenerateExamRequest,
  SubmitExamRequest,
  UpdateExamRequest,
} from '@/lib/types/exams'

export const EXAM_QUERY_KEYS = {
  all: ['exams'] as const,
  byNotebook: (notebookId: string) => ['exams', 'notebook', notebookId] as const,
  detail: (id: string, includeSolutions: boolean) =>
    ['exams', id, { includeSolutions }] as const,
  submissions: (id: string) => ['exams', id, 'submissions'] as const,
  submission: (submissionId: string) => ['exam-submissions', submissionId] as const,
}

export function useExams(notebookId?: string) {
  return useQuery({
    queryKey: notebookId ? EXAM_QUERY_KEYS.byNotebook(notebookId) : EXAM_QUERY_KEYS.all,
    queryFn: () => examsApi.list(notebookId),
    enabled: notebookId === undefined || !!notebookId,
  })
}

export function useExam(id?: string, includeSolutions = false, options?: { enabled?: boolean }) {
  const examId = id ?? ''
  return useQuery({
    queryKey: EXAM_QUERY_KEYS.detail(examId, includeSolutions),
    queryFn: () => examsApi.get(examId, includeSolutions),
    enabled: !!examId && (options?.enabled ?? true),
  })
}

export function useGenerateExam() {
  const queryClient = useQueryClient()
  const { toast } = useToast()
  const { t } = useTranslation()

  return useMutation({
    mutationFn: (data: GenerateExamRequest) => examsApi.generate(data),
    onSuccess: (exam) => {
      queryClient.invalidateQueries({ queryKey: EXAM_QUERY_KEYS.byNotebook(exam.notebook_id) })
      queryClient.invalidateQueries({ queryKey: EXAM_QUERY_KEYS.all })
      toast({
        title: t('common.success'),
        description: t('exams.generateSuccess'),
      })
    },
    onError: (error: unknown) => {
      toast({
        title: t('common.error'),
        description: getApiErrorMessage(error, (key) => t(key)),
        variant: 'destructive',
      })
    },
  })
}

export function useUpdateExam() {
  const queryClient = useQueryClient()
  const { toast } = useToast()
  const { t } = useTranslation()

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateExamRequest }) =>
      examsApi.update(id, data),
    onSuccess: (exam) => {
      queryClient.invalidateQueries({ queryKey: EXAM_QUERY_KEYS.all })
      queryClient.invalidateQueries({ queryKey: EXAM_QUERY_KEYS.byNotebook(exam.notebook_id) })
      toast({
        title: t('common.success'),
        description: t('exams.updateSuccess'),
      })
    },
    onError: (error: unknown) => {
      toast({
        title: t('common.error'),
        description: getApiErrorMessage(error, (key) => t(key)),
        variant: 'destructive',
      })
    },
  })
}

export function useDeleteExam() {
  const queryClient = useQueryClient()
  const { toast } = useToast()
  const { t } = useTranslation()

  return useMutation({
    mutationFn: (id: string) => examsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: EXAM_QUERY_KEYS.all })
      toast({
        title: t('common.success'),
        description: t('exams.deleteSuccess'),
      })
    },
    onError: (error: unknown) => {
      toast({
        title: t('common.error'),
        description: getApiErrorMessage(error, (key) => t(key)),
        variant: 'destructive',
      })
    },
  })
}

export function useSubmitExam() {
  const queryClient = useQueryClient()
  const { toast } = useToast()
  const { t } = useTranslation()

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: SubmitExamRequest }) =>
      examsApi.submit(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: EXAM_QUERY_KEYS.submissions(id) })
    },
    onError: (error: unknown) => {
      toast({
        title: t('common.error'),
        description: getApiErrorMessage(error, (key) => t(key)),
        variant: 'destructive',
      })
    },
  })
}

export function useExamSubmissions(id?: string, options?: { enabled?: boolean }) {
  const examId = id ?? ''
  return useQuery({
    queryKey: EXAM_QUERY_KEYS.submissions(examId),
    queryFn: () => examsApi.listSubmissions(examId),
    enabled: !!examId && (options?.enabled ?? true),
  })
}
