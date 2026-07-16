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
import { Textarea } from '@/components/ui/textarea'
import { Checkbox } from '@/components/ui/checkbox'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { useTranslation } from '@/lib/hooks/use-translation'
import { useNotebookSources } from '@/lib/hooks/use-sources'
import { useModels } from '@/lib/hooks/use-models'
import {
  ExamDifficulty,
  ExamQuestionType,
  GenerateExamRequest,
} from '@/lib/types/exams'

const NONE_REFERENCE = '__none__'
const DEFAULT_MODEL = '__default__'

interface GenerateExamDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  notebookId: string
  isGenerating: boolean
  onGenerate: (request: GenerateExamRequest) => void
}

const QUESTION_TYPES: ExamQuestionType[] = [
  'multiple_choice',
  'true_false',
  'short_answer',
  'open',
]

const DIFFICULTIES: ExamDifficulty[] = ['easy', 'medium', 'hard', 'mixed']

export function GenerateExamDialog({
  open,
  onOpenChange,
  notebookId,
  isGenerating,
  onGenerate,
}: GenerateExamDialogProps) {
  const { t } = useTranslation()
  const { sources } = useNotebookSources(notebookId)
  const { data: models } = useModels()
  const languageModels = (models || []).filter((m) => m.type === 'language')

  const [title, setTitle] = useState('')
  const [numQuestions, setNumQuestions] = useState(5)
  const [difficulty, setDifficulty] = useState<ExamDifficulty>('medium')
  const [questionTypes, setQuestionTypes] = useState<ExamQuestionType[]>(['open'])
  const [language, setLanguage] = useState('')
  const [referenceSourceId, setReferenceSourceId] = useState<string>(NONE_REFERENCE)
  const [modelId, setModelId] = useState<string>(DEFAULT_MODEL)
  const [instructions, setInstructions] = useState('')

  const toggleType = (type: ExamQuestionType, checked: boolean) => {
    setQuestionTypes((prev) =>
      checked ? [...new Set([...prev, type])] : prev.filter((tp) => tp !== type)
    )
  }

  const handleSubmit = () => {
    const request: GenerateExamRequest = {
      notebook_id: notebookId,
      num_questions: numQuestions,
      difficulty,
      question_types: questionTypes.length > 0 ? questionTypes : ['open'],
    }
    if (title.trim()) request.title = title.trim()
    if (language.trim()) request.language = language.trim()
    if (instructions.trim()) request.instructions = instructions.trim()
    if (referenceSourceId !== NONE_REFERENCE) request.reference_source_id = referenceSourceId
    if (modelId !== DEFAULT_MODEL) request.model_id = modelId
    onGenerate(request)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>{t('exams.generateTitle')}</DialogTitle>
          <DialogDescription>{t('exams.generateDescription')}</DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-2">
          <div className="space-y-2">
            <Label htmlFor="exam-title">{t('exams.titleLabel')}</Label>
            <Input
              id="exam-title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder={t('exams.titlePlaceholder')}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="exam-num">{t('exams.numQuestions')}</Label>
              <Input
                id="exam-num"
                type="number"
                min={1}
                max={50}
                value={numQuestions}
                onChange={(e) =>
                  setNumQuestions(Math.max(1, Math.min(50, Number(e.target.value) || 1)))
                }
              />
            </div>
            <div className="space-y-2">
              <Label>{t('exams.difficulty')}</Label>
              <Select
                value={difficulty}
                onValueChange={(v) => setDifficulty(v as ExamDifficulty)}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {DIFFICULTIES.map((d) => (
                    <SelectItem key={d} value={d}>
                      {t(`exams.difficultyOptions.${d}`)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="space-y-2">
            <Label>{t('exams.questionTypes')}</Label>
            <div className="grid grid-cols-2 gap-2">
              {QUESTION_TYPES.map((type) => (
                <label
                  key={type}
                  className="flex items-center gap-2 rounded-md border p-2 text-sm cursor-pointer"
                >
                  <Checkbox
                    checked={questionTypes.includes(type)}
                    onCheckedChange={(checked) => toggleType(type, checked === true)}
                  />
                  {t(`exams.questionTypeOptions.${type}`)}
                </label>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="exam-language">{t('exams.language')}</Label>
              <Input
                id="exam-language"
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                placeholder={t('exams.languagePlaceholder')}
              />
            </div>
            <div className="space-y-2">
              <Label>{t('exams.referenceExam')}</Label>
              <Select value={referenceSourceId} onValueChange={setReferenceSourceId}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={NONE_REFERENCE}>{t('exams.referenceNone')}</SelectItem>
                  {sources.map((source) => (
                    <SelectItem key={source.id} value={source.id}>
                      {source.title || t('exams.untitledSource')}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="space-y-2">
            <Label>{t('exams.model')}</Label>
            <Select value={modelId} onValueChange={setModelId}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={DEFAULT_MODEL}>{t('exams.modelDefault')}</SelectItem>
                {languageModels.map((model) => (
                  <SelectItem key={model.id} value={model.id}>
                    {model.name}
                    <span className="text-xs text-muted-foreground ml-2">
                      {model.provider}
                    </span>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="exam-instructions">{t('exams.instructions')}</Label>
            <Textarea
              id="exam-instructions"
              value={instructions}
              onChange={(e) => setInstructions(e.target.value)}
              placeholder={t('exams.instructionsPlaceholder')}
              rows={3}
            />
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={isGenerating}>
            {t('common.cancel')}
          </Button>
          <Button onClick={handleSubmit} disabled={isGenerating}>
            {isGenerating && <LoadingSpinner size="sm" className="mr-2" />}
            {t('exams.generate')}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
