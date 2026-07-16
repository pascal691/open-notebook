// Types for the practice-exam feature. Mirrors the Pydantic schemas in
// api/models.py.

export type ExamQuestionType =
  | 'multiple_choice'
  | 'true_false'
  | 'short_answer'
  | 'open'

export type ExamDifficulty = 'easy' | 'medium' | 'hard' | 'mixed'

export interface ExamQuestion {
  number: number
  question: string
  question_type: ExamQuestionType
  options: string[]
  points: number
  // Only present when solutions are requested (after grading).
  model_answer?: string | null
  rubric?: string | null
}

export interface Exam {
  id: string
  notebook_id: string
  title: string
  description?: string | null
  status: string
  num_questions: number
  difficulty: string
  question_types: string[]
  language?: string | null
  instructions?: string | null
  reference_source_id?: string | null
  total_points: number
  questions: ExamQuestion[]
  created: string
  updated: string
}

export interface ExamListItem {
  id: string
  notebook_id: string
  title: string
  description?: string | null
  status: string
  num_questions: number
  difficulty: string
  total_points: number
  created: string
  updated: string
}

export interface GenerateExamRequest {
  notebook_id: string
  title?: string
  description?: string
  num_questions: number
  difficulty: ExamDifficulty
  question_types: ExamQuestionType[]
  language?: string
  instructions?: string
  reference_source_id?: string
  model_id?: string
}

export interface UpdateExamRequest {
  title?: string
  description?: string
}

export interface QuestionResult {
  number: number
  awarded_points: number
  max_points: number
  correct: boolean
  feedback: string
}

export interface ExamSubmission {
  id: string
  exam_id: string
  answers: Record<string, string>
  status: string
  graded: boolean
  total_score: number
  max_score: number
  percentage: number
  overall_feedback: string
  results: QuestionResult[]
  created: string
  updated: string
}

export interface SubmitExamRequest {
  answers: Record<string, string>
  model_id?: string
}
