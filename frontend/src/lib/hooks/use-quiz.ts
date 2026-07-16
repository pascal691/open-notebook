import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { quizApi } from '@/lib/api/quiz'
import { QUERY_KEYS } from '@/lib/api/query-client'
import { useToast } from '@/lib/hooks/use-toast'
import { useTranslation } from '@/lib/hooks/use-translation'
import { getApiErrorKey } from '@/lib/utils/error-handler'
import { QuizGenerateRequest } from '@/lib/types/quiz'

export function useQuizzes(notebookId: string) {
  const query = useQuery({
    queryKey: QUERY_KEYS.quizzes(notebookId),
    queryFn: () => quizApi.list(notebookId),
    enabled: Boolean(notebookId),
  })

  return {
    ...query,
    quizzes: query.data ?? [],
  }
}

export function useGenerateQuiz(notebookId: string) {
  const queryClient = useQueryClient()
  const { toast } = useToast()
  const { t } = useTranslation()

  return useMutation({
    mutationFn: (payload: QuizGenerateRequest) => quizApi.generate(notebookId, payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: QUERY_KEYS.quizzes(notebookId) })
      toast({
        title: t('quiz.generationStarted'),
        description: t('quiz.generationStartedDesc'),
      })
    },
    onError: (error: unknown) => {
      toast({
        title: t('quiz.failedToGenerate'),
        description: getApiErrorKey(error, t('common.error')),
        variant: 'destructive',
      })
    },
  })
}

export function useDeleteQuiz(notebookId: string) {
  const queryClient = useQueryClient()
  const { toast } = useToast()
  const { t } = useTranslation()

  return useMutation({
    mutationFn: (quizId: string) => quizApi.delete(quizId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.quizzes(notebookId) })
      toast({
        title: t('quiz.quizDeleted'),
      })
    },
    onError: (error: unknown) => {
      toast({
        title: t('quiz.failedToDelete'),
        description: getApiErrorKey(error, t('common.error')),
        variant: 'destructive',
      })
    },
  })
}
