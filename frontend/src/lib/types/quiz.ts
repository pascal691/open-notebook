export interface QuizQuestion {
  question: string
  options: string[]
  correct_answer_index: number
  explanation: string
}

export interface Quiz {
  id: string
  title: string
  questions: QuizQuestion[]
  created: string
  updated: string
}

export interface QuizGenerateRequest {
  num_questions?: number
  model_id?: string | null
}
