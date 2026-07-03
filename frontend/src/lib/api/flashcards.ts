import apiClient from './client'
import { FlashcardDeck, FlashcardGenerateRequest } from '@/lib/types/flashcards'

export const flashcardsApi = {
  generate: async (notebookId: string, payload: FlashcardGenerateRequest) => {
    const response = await apiClient.post<FlashcardDeck>(
      `/notebooks/${notebookId}/flashcard-decks`,
      payload
    )
    return response.data
  },

  list: async (notebookId: string) => {
    const response = await apiClient.get<FlashcardDeck[]>(
      `/notebooks/${notebookId}/flashcard-decks`
    )
    return response.data
  },

  get: async (deckId: string) => {
    const response = await apiClient.get<FlashcardDeck>(
      `/flashcard-decks/${deckId}`
    )
    return response.data
  },

  delete: async (deckId: string) => {
    await apiClient.delete(`/flashcard-decks/${deckId}`)
  },
}
