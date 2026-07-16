export interface Flashcard {
  front: string
  back: string
}

export interface FlashcardDeck {
  id: string
  title: string
  cards: Flashcard[]
  created: string
  updated: string
}

export interface FlashcardGenerateRequest {
  num_cards?: number
  model_id?: string | null
}
