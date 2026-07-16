'use client'

import { useMemo, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import {
  RadioGroup,
  RadioGroupItem,
} from '@/components/ui/radio-group'
import { Label } from '@/components/ui/label'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { MarkdownRenderer } from '@/components/ui/markdown-renderer'
import { ArrowLeft, CheckCircle2, XCircle } from 'lucide-react'
import { useTranslation } from '@/lib/hooks/use-translation'
import { useExam, useSubmitExam } from '@/lib/hooks/use-exams'
import { ExamQuestion, ExamSubmission } from '@/lib/types/exams'

interface ExamRunnerProps {
  examId: string
  onBack: () => void
}

export function ExamRunner({ examId, onBack }: ExamRunnerProps) {
  const { t } = useTranslation()
  const [answers, setAnswers] = useState<Record<string, string>>({})
  const [submission, setSubmission] = useState<ExamSubmission | null>(null)

  // While taking the exam, model answers stay hidden. Once graded, we re-fetch
  // with solutions so the review can show the correct answer per question.
  const { data: exam, isLoading } = useExam(examId, submission !== null)
  const submit = useSubmitExam()

  const resultByNumber = useMemo(() => {
    const map: Record<number, ExamSubmission['results'][number]> = {}
    submission?.results.forEach((r) => {
      map[r.number] = r
    })
    return map
  }, [submission])

  if (isLoading || !exam) {
    return (
      <div className="flex justify-center py-12">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  const graded = submission !== null

  const handleSubmit = async () => {
    const result = await submit.mutateAsync({ id: examId, data: { answers } })
    setSubmission(result)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const setAnswer = (num: number, value: string) => {
    setAnswers((prev) => ({ ...prev, [String(num)]: value }))
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="sm" onClick={onBack}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            {t('exams.backToList')}
          </Button>
          <h2 className="text-xl font-semibold">{exam.title}</h2>
        </div>
        <Badge variant="secondary">
          {t('exams.pointsTotal').replace('{points}', String(exam.total_points))}
        </Badge>
      </div>

      {graded && submission && (
        <Card className="border-primary">
          <CardHeader>
            <CardTitle>{t('exams.resultTitle')}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-center gap-4">
              <div className="text-3xl font-bold">
                {submission.total_score} / {submission.max_score}
              </div>
              <div className="flex-1">
                <Progress value={submission.percentage} />
              </div>
              <div className="text-lg font-semibold">{submission.percentage}%</div>
            </div>
            {submission.overall_feedback && (
              <div className="text-sm text-muted-foreground">
                <MarkdownRenderer>{submission.overall_feedback}</MarkdownRenderer>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      <div className="space-y-4">
        {exam.questions.map((question) => (
          <QuestionCard
            key={question.number}
            question={question}
            answer={answers[String(question.number)] || ''}
            onAnswer={(value) => setAnswer(question.number, value)}
            disabled={graded}
            result={graded ? resultByNumber[question.number] : undefined}
          />
        ))}
      </div>

      {!graded && (
        <div className="flex justify-end">
          <Button onClick={handleSubmit} disabled={submit.isPending}>
            {submit.isPending && <LoadingSpinner size="sm" className="mr-2" />}
            {t('exams.submitForGrading')}
          </Button>
        </div>
      )}

      {graded && (
        <div className="flex justify-end">
          <Button variant="outline" onClick={onBack}>
            {t('exams.backToList')}
          </Button>
        </div>
      )}
    </div>
  )
}

interface QuestionCardProps {
  question: ExamQuestion
  answer: string
  onAnswer: (value: string) => void
  disabled: boolean
  result?: ExamSubmission['results'][number]
}

function QuestionCard({ question, answer, onAnswer, disabled, result }: QuestionCardProps) {
  const { t } = useTranslation()
  const hasOptions = question.options && question.options.length > 0

  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between gap-4">
          <CardTitle className="text-base font-medium">
            {question.number}. {question.question}
          </CardTitle>
          <div className="flex items-center gap-2 shrink-0">
            {result && (
              result.correct ? (
                <CheckCircle2 className="h-5 w-5 text-green-600" />
              ) : (
                <XCircle className="h-5 w-5 text-red-500" />
              )
            )}
            <Badge variant="outline">
              {result
                ? `${result.awarded_points} / ${result.max_points}`
                : t('exams.pointsBadge').replace('{points}', String(question.points))}
            </Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {hasOptions ? (
          <RadioGroup value={answer} onValueChange={onAnswer} disabled={disabled}>
            {question.options.map((option, idx) => (
              <div key={idx} className="flex items-center gap-2">
                <RadioGroupItem value={option} id={`q${question.number}-o${idx}`} />
                <Label htmlFor={`q${question.number}-o${idx}`} className="font-normal">
                  {option}
                </Label>
              </div>
            ))}
          </RadioGroup>
        ) : (
          <Textarea
            value={answer}
            onChange={(e) => onAnswer(e.target.value)}
            disabled={disabled}
            placeholder={t('exams.answerPlaceholder')}
            rows={3}
          />
        )}

        {result && (
          <div className="space-y-2 rounded-md bg-muted/50 p-3 text-sm">
            {result.feedback && (
              <div>
                <span className="font-medium">{t('exams.feedback')}: </span>
                {result.feedback}
              </div>
            )}
            {question.model_answer && (
              <div>
                <span className="font-medium">{t('exams.modelAnswer')}: </span>
                {question.model_answer}
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
