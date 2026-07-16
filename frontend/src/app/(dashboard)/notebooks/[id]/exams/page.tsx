'use client'

import { useState } from 'react'
import { useParams } from 'next/navigation'
import Link from 'next/link'
import { AppShell } from '@/components/layout/AppShell'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { ArrowLeft, GraduationCap, Plus, Trash2, PlayCircle } from 'lucide-react'
import { useTranslation } from '@/lib/hooks/use-translation'
import { useNotebook } from '@/lib/hooks/use-notebooks'
import {
  useExams,
  useGenerateExam,
  useDeleteExam,
} from '@/lib/hooks/use-exams'
import { GenerateExamDialog } from './components/GenerateExamDialog'
import { ExamRunner } from './components/ExamRunner'
import { GenerateExamRequest } from '@/lib/types/exams'

export default function NotebookExamsPage() {
  const { t } = useTranslation()
  const params = useParams()
  const notebookId = params?.id ? decodeURIComponent(params.id as string) : ''

  const { data: notebook } = useNotebook(notebookId)
  const { data: exams, isLoading } = useExams(notebookId)
  const generateExam = useGenerateExam()
  const deleteExam = useDeleteExam()

  const [dialogOpen, setDialogOpen] = useState(false)
  const [activeExamId, setActiveExamId] = useState<string | null>(null)

  // Literal keys (not built dynamically) so the i18n key-usage checker can see them.
  const difficultyLabels: Record<string, string> = {
    easy: t('exams.difficultyOptions.easy'),
    medium: t('exams.difficultyOptions.medium'),
    hard: t('exams.difficultyOptions.hard'),
    mixed: t('exams.difficultyOptions.mixed'),
  }

  const handleGenerate = async (request: GenerateExamRequest) => {
    const exam = await generateExam.mutateAsync(request)
    setDialogOpen(false)
    setActiveExamId(exam.id)
  }

  const handleDelete = async (id: string) => {
    if (!window.confirm(t('exams.deleteConfirm'))) return
    await deleteExam.mutateAsync(id)
    if (activeExamId === id) setActiveExamId(null)
  }

  if (activeExamId) {
    return (
      <AppShell>
        <div className="flex-1 min-h-0 overflow-y-auto">
          <div className="mx-auto w-full max-w-3xl p-6">
            <ExamRunner examId={activeExamId} onBack={() => setActiveExamId(null)} />
          </div>
        </div>
      </AppShell>
    )
  }

  return (
    <AppShell>
      <div className="flex-1 min-h-0 overflow-y-auto">
        <div className="mx-auto w-full max-w-4xl p-6 space-y-6">
        <div className="flex items-center justify-between gap-4 border-b pb-4">
          <div className="flex items-center gap-3">
            <Link href={`/notebooks/${encodeURIComponent(notebookId)}`}>
              <Button variant="ghost" size="sm">
                <ArrowLeft className="h-4 w-4 mr-2" />
                {t('exams.backToNotebook')}
              </Button>
            </Link>
            <div className="flex items-center gap-2">
              <GraduationCap className="h-5 w-5" />
              <h1 className="text-2xl font-bold">{t('exams.title')}</h1>
            </div>
          </div>
          <Button onClick={() => setDialogOpen(true)}>
            <Plus className="h-4 w-4 mr-2" />
            {t('exams.newExam')}
          </Button>
        </div>

        {notebook && (
          <p className="text-sm text-muted-foreground">
            {t('exams.subtitle').replace('{notebook}', notebook.name)}
          </p>
        )}

        {isLoading ? (
          <div className="flex justify-center py-12">
            <LoadingSpinner size="lg" />
          </div>
        ) : !exams || exams.length === 0 ? (
          <Card>
            <CardContent className="flex flex-col items-center gap-3 py-12 text-center">
              <GraduationCap className="h-10 w-10 text-muted-foreground" />
              <p className="text-muted-foreground">{t('exams.emptyState')}</p>
              <Button onClick={() => setDialogOpen(true)}>
                <Plus className="h-4 w-4 mr-2" />
                {t('exams.newExam')}
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2">
            {exams.map((exam) => (
              <Card key={exam.id} className="flex flex-col">
                <CardHeader>
                  <CardTitle className="text-base">{exam.title}</CardTitle>
                  {exam.description && (
                    <p className="text-sm text-muted-foreground line-clamp-2">
                      {exam.description}
                    </p>
                  )}
                </CardHeader>
                <CardContent className="mt-auto space-y-3">
                  <div className="flex flex-wrap gap-2">
                    <Badge variant="secondary">
                      {t('exams.questionCount').replace(
                        '{count}',
                        String(exam.num_questions)
                      )}
                    </Badge>
                    <Badge variant="outline">
                      {difficultyLabels[exam.difficulty] || exam.difficulty}
                    </Badge>
                    <Badge variant="outline">
                      {t('exams.pointsTotal').replace('{points}', String(exam.total_points))}
                    </Badge>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      className="flex-1"
                      onClick={() => setActiveExamId(exam.id)}
                    >
                      <PlayCircle className="h-4 w-4 mr-2" />
                      {t('exams.startExam')}
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleDelete(exam.id)}
                      className="text-red-600 hover:text-red-700"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
        </div>
      </div>

      <GenerateExamDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        notebookId={notebookId}
        isGenerating={generateExam.isPending}
        onGenerate={handleGenerate}
      />
    </AppShell>
  )
}
