'use client'

import { useState } from 'react'

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useGenerateQuiz } from '@/lib/hooks/use-quiz'
import { useTranslation } from '@/lib/hooks/use-translation'

interface GenerateQuizDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  notebookId: string
}

export function GenerateQuizDialog({
  open,
  onOpenChange,
  notebookId,
}: GenerateQuizDialogProps) {
  const { t } = useTranslation()
  const [numQuestions, setNumQuestions] = useState(10)
  const generateQuiz = useGenerateQuiz(notebookId)

  const closeDialog = () => onOpenChange(false)

  const handleSubmit = async () => {
    try {
      await generateQuiz.mutateAsync({ num_questions: numQuestions })
      closeDialog()
    } catch {
      // Error toast already shown by the mutation hook.
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[420px]">
        <DialogHeader>
          <DialogTitle>{t('quiz.generate')}</DialogTitle>
          <DialogDescription>{t('quiz.generateDesc')}</DialogDescription>
        </DialogHeader>

        <div className="space-y-2">
          <Label htmlFor="quiz-num-questions">{t('quiz.numQuestions')}</Label>
          <Input
            id="quiz-num-questions"
            type="number"
            min={3}
            max={20}
            value={numQuestions}
            onChange={(e) => setNumQuestions(Number(e.target.value))}
            autoComplete="off"
          />
        </div>

        <DialogFooter className="gap-2 sm:gap-0">
          <Button type="button" variant="outline" onClick={closeDialog}>
            {t('common.cancel')}
          </Button>
          <Button onClick={handleSubmit} disabled={generateQuiz.isPending}>
            {generateQuiz.isPending ? t('quiz.generating') : t('quiz.generate')}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
