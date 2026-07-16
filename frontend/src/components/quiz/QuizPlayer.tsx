'use client'

import { useState } from 'react'
import { CheckCircle2, XCircle } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { cn } from '@/lib/utils'
import { useTranslation } from '@/lib/hooks/use-translation'
import { Quiz } from '@/lib/types/quiz'

interface QuizPlayerProps {
  quiz: Quiz
  onExit: () => void
}

export function QuizPlayer({ quiz, onExit }: QuizPlayerProps) {
  const { t } = useTranslation()
  const [currentIndex, setCurrentIndex] = useState(0)
  const [selectedOption, setSelectedOption] = useState<number | null>(null)
  const [revealed, setRevealed] = useState(false)
  const [correctCount, setCorrectCount] = useState(0)
  const [finished, setFinished] = useState(false)

  const totalQuestions = quiz.questions.length
  const currentQuestion = quiz.questions[currentIndex]

  const handleSelectOption = (index: number) => {
    if (revealed) return
    setSelectedOption(index)
  }

  const handleCheckAnswer = () => {
    if (selectedOption === null) return
    setRevealed(true)
    if (selectedOption === currentQuestion.correct_answer_index) {
      setCorrectCount((count) => count + 1)
    }
  }

  const handleNext = () => {
    if (currentIndex + 1 >= totalQuestions) {
      setFinished(true)
      return
    }
    setCurrentIndex((index) => index + 1)
    setSelectedOption(null)
    setRevealed(false)
  }

  const handleRetake = () => {
    setCurrentIndex(0)
    setSelectedOption(null)
    setRevealed(false)
    setCorrectCount(0)
    setFinished(false)
  }

  if (finished) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>{quiz.title}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-lg font-medium">
            {t('quiz.score')
              .replace('{correct}', String(correctCount))
              .replace('{total}', String(totalQuestions))}
          </p>
          <div className="flex gap-2">
            <Button onClick={handleRetake}>{t('quiz.retake')}</Button>
            <Button variant="outline" onClick={onExit}>
              {t('common.close')}
            </Button>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between gap-2">
          <CardTitle className="text-base">{quiz.title}</CardTitle>
          <span className="text-sm text-muted-foreground">
            {t('quiz.questionProgress')
              .replace('{current}', String(currentIndex + 1))
              .replace('{total}', String(totalQuestions))}
          </span>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="font-medium">{currentQuestion.question}</p>

        <div className="space-y-2">
          {currentQuestion.options.map((option, index) => {
            const isSelected = selectedOption === index
            const isCorrectOption = index === currentQuestion.correct_answer_index

            return (
              <button
                key={index}
                type="button"
                onClick={() => handleSelectOption(index)}
                disabled={revealed}
                className={cn(
                  'w-full text-left p-3 border rounded-lg transition-colors',
                  !revealed && isSelected && 'border-primary bg-accent/50',
                  !revealed && !isSelected && 'hover:bg-accent/30',
                  revealed && isCorrectOption && 'border-green-600 bg-green-600/10',
                  revealed &&
                    isSelected &&
                    !isCorrectOption &&
                    'border-red-600 bg-red-600/10'
                )}
              >
                <div className="flex items-center justify-between gap-2">
                  <span>{option}</span>
                  {revealed && isCorrectOption && (
                    <CheckCircle2 className="h-4 w-4 text-green-600 flex-shrink-0" />
                  )}
                  {revealed && isSelected && !isCorrectOption && (
                    <XCircle className="h-4 w-4 text-red-600 flex-shrink-0" />
                  )}
                </div>
              </button>
            )
          })}
        </div>

        {revealed && (
          <div
            className={cn(
              'p-3 rounded-lg text-sm',
              selectedOption === currentQuestion.correct_answer_index
                ? 'bg-green-600/10 text-green-800 dark:text-green-400'
                : 'bg-red-600/10 text-red-800 dark:text-red-400'
            )}
          >
            <p className="font-medium mb-1">
              {selectedOption === currentQuestion.correct_answer_index
                ? t('quiz.correct')
                : t('quiz.incorrect')}
            </p>
            <p>{currentQuestion.explanation}</p>
          </div>
        )}

        <div className="flex justify-between gap-2 pt-2">
          <Button variant="outline" onClick={onExit}>
            {t('common.close')}
          </Button>
          {revealed ? (
            <Button onClick={handleNext}>
              {currentIndex + 1 >= totalQuestions
                ? t('quiz.finish')
                : t('quiz.nextQuestion')}
            </Button>
          ) : (
            <Button onClick={handleCheckAnswer} disabled={selectedOption === null}>
              {t('quiz.checkAnswer')}
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
