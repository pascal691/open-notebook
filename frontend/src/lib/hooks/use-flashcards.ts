import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { flashcardsApi } from '@/lib/api/flashcards'
import { QUERY_KEYS } from '@/lib/api/query-client'
import { useToast } from '@/lib/hooks/use-toast'
import { useTranslation } from '@/lib/hooks/use-translation'
import { getApiErrorKey } from '@/lib/utils/error-handler'
import { FlashcardGenerateRequest } from '@/lib/types/flashcards'

export function useFlashcardDecks(notebookId: string) {
  const query = useQuery({
    queryKey: QUERY_KEYS.flashcardDecks(notebookId),
    queryFn: () => flashcardsApi.list(notebookId),
    enabled: Boolean(notebookId),
  })

  return {
    ...query,
    decks: query.data ?? [],
  }
}

export function useGenerateFlashcardDeck(notebookId: string) {
  const queryClient = useQueryClient()
  const { toast } = useToast()
  const { t } = useTranslation()

  return useMutation({
    mutationFn: (payload: FlashcardGenerateRequest) =>
      flashcardsApi.generate(notebookId, payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: QUERY_KEYS.flashcardDecks(notebookId),
      })
      toast({
        title: t('flashcards.generationStarted'),
        description: t('flashcards.generationStartedDesc'),
      })
    },
    onError: (error: unknown) => {
      toast({
        title: t('flashcards.failedToGenerate'),
        description: getApiErrorKey(error, t('common.error')),
        variant: 'destructive',
      })
    },
  })
}

export function useDeleteFlashcardDeck(notebookId: string) {
  const queryClient = useQueryClient()
  const { toast } = useToast()
  const { t } = useTranslation()

  return useMutation({
    mutationFn: (deckId: string) => flashcardsApi.delete(deckId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.flashcardDecks(notebookId) })
      toast({
        title: t('flashcards.deckDeleted'),
      })
    },
    onError: (error: unknown) => {
      toast({
        title: t('flashcards.failedToDelete'),
        description: getApiErrorKey(error, t('common.error')),
        variant: 'destructive',
      })
    },
  })
}
