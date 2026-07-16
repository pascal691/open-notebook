'use client'

import { useMemo, useState } from 'react'
import { GraduationCap, HelpCircle, Layers, Plus } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { EmptyState } from '@/components/common/EmptyState'
import { ConfirmDialog } from '@/components/common/ConfirmDialog'
import { CollapsibleColumn, createCollapseButton, createFocusButton } from '@/components/notebooks/CollapsibleColumn'
import { useNotebookColumnsStore } from '@/lib/stores/notebook-columns-store'
import { useTranslation } from '@/lib/hooks/use-translation'
import { useQuizzes, useDeleteQuiz } from '@/lib/hooks/use-quiz'
import { useFlashcardDecks, useDeleteFlashcardDeck } from '@/lib/hooks/use-flashcards'
import { GenerateQuizDialog } from '@/components/quiz/GenerateQuizDialog'
import { QuizListItem } from '@/components/quiz/QuizListItem'
import { QuizPlayer } from '@/components/quiz/QuizPlayer'
import { GenerateFlashcardsDialog } from '@/components/flashcards/GenerateFlashcardsDialog'
import { FlashcardDeckListItem } from '@/components/flashcards/FlashcardDeckListItem'
import { FlashcardStudySession } from '@/components/flashcards/FlashcardStudySession'
import type { Quiz } from '@/lib/types/quiz'
import type { FlashcardDeck } from '@/lib/types/flashcards'

interface StudyColumnProps {
  notebookId: string
}

export function StudyColumn({ notebookId }: StudyColumnProps) {
  const { t } = useTranslation()
  const { studyCollapsed, toggleStudy, focusedColumn, toggleFocus, clearFocus } =
    useNotebookColumnsStore()
  const studyLabel = t('study.title')
  const collapsedByFocus = focusedColumn !== null && focusedColumn !== 'study'
  const effectiveCollapsed = studyCollapsed || collapsedByFocus
  const collapseButton = useMemo(
    () => createCollapseButton(toggleStudy, studyLabel),
    [toggleStudy, studyLabel]
  )
  const focusButton = useMemo(
    () => createFocusButton(() => toggleFocus('study'), focusedColumn === 'study', studyLabel),
    [toggleFocus, focusedColumn, studyLabel]
  )

  const { quizzes, isLoading: quizzesLoading } = useQuizzes(notebookId)
  const deleteQuiz = useDeleteQuiz(notebookId)
  const { decks, isLoading: decksLoading } = useFlashcardDecks(notebookId)
  const deleteDeck = useDeleteFlashcardDeck(notebookId)

  const [showGenerateQuiz, setShowGenerateQuiz] = useState(false)
  const [showGenerateFlashcards, setShowGenerateFlashcards] = useState(false)
  const [activeQuiz, setActiveQuiz] = useState<Quiz | null>(null)
  const [activeDeck, setActiveDeck] = useState<FlashcardDeck | null>(null)
  const [quizToDelete, setQuizToDelete] = useState<string | null>(null)
  const [deckToDelete, setDeckToDelete] = useState<string | null>(null)

  const handleDeleteQuizConfirm = async () => {
    if (!quizToDelete) return
    await deleteQuiz.mutateAsync(quizToDelete)
    setQuizToDelete(null)
  }

  const handleDeleteDeckConfirm = async () => {
    if (!deckToDelete) return
    await deleteDeck.mutateAsync(deckToDelete)
    setDeckToDelete(null)
  }

  return (
    <>
      <CollapsibleColumn
        isCollapsed={effectiveCollapsed}
        onToggle={collapsedByFocus ? clearFocus : toggleStudy}
        collapsedIcon={GraduationCap}
        collapsedLabel={studyLabel}
      >
        <Card className="h-full flex flex-col flex-1 overflow-hidden">
          <CardHeader className="pb-3 flex-shrink-0">
            <div className="flex items-center justify-between gap-2">
              <CardTitle className="text-lg">{studyLabel}</CardTitle>
              <div className="flex items-center gap-1">
                {focusButton}
                {collapseButton}
              </div>
            </div>
          </CardHeader>

          <CardContent className="flex-1 overflow-y-auto min-h-0">
            <Tabs defaultValue="quiz">
              <TabsList className="grid w-full grid-cols-2 mb-3">
                <TabsTrigger value="quiz" className="gap-2">
                  <HelpCircle className="h-4 w-4" />
                  {t('quiz.title')}
                </TabsTrigger>
                <TabsTrigger value="flashcards" className="gap-2">
                  <Layers className="h-4 w-4" />
                  {t('flashcards.title')}
                </TabsTrigger>
              </TabsList>

              <TabsContent value="quiz" className="space-y-3">
                {activeQuiz ? (
                  <QuizPlayer quiz={activeQuiz} onExit={() => setActiveQuiz(null)} />
                ) : (
                  <>
                    <Button size="sm" onClick={() => setShowGenerateQuiz(true)}>
                      <Plus className="h-4 w-4 mr-2" />
                      {t('quiz.generate')}
                    </Button>

                    {quizzesLoading ? (
                      <div className="flex items-center justify-center py-8">
                        <LoadingSpinner />
                      </div>
                    ) : quizzes.length === 0 ? (
                      <EmptyState
                        icon={HelpCircle}
                        title={t('quiz.noQuizzesYet')}
                        description={t('quiz.noQuizzesYetDesc')}
                      />
                    ) : (
                      <div className="space-y-3">
                        {quizzes.map((quiz) => (
                          <QuizListItem
                            key={quiz.id}
                            quiz={quiz}
                            onStart={setActiveQuiz}
                            onDelete={setQuizToDelete}
                          />
                        ))}
                      </div>
                    )}
                  </>
                )}
              </TabsContent>

              <TabsContent value="flashcards" className="space-y-3">
                {activeDeck ? (
                  <FlashcardStudySession
                    deck={activeDeck}
                    onExit={() => setActiveDeck(null)}
                  />
                ) : (
                  <>
                    <Button size="sm" onClick={() => setShowGenerateFlashcards(true)}>
                      <Plus className="h-4 w-4 mr-2" />
                      {t('flashcards.generate')}
                    </Button>

                    {decksLoading ? (
                      <div className="flex items-center justify-center py-8">
                        <LoadingSpinner />
                      </div>
                    ) : decks.length === 0 ? (
                      <EmptyState
                        icon={Layers}
                        title={t('flashcards.noDecksYet')}
                        description={t('flashcards.noDecksYetDesc')}
                      />
                    ) : (
                      <div className="space-y-3">
                        {decks.map((deck) => (
                          <FlashcardDeckListItem
                            key={deck.id}
                            deck={deck}
                            onStart={setActiveDeck}
                            onDelete={setDeckToDelete}
                          />
                        ))}
                      </div>
                    )}
                  </>
                )}
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
      </CollapsibleColumn>

      <GenerateQuizDialog
        open={showGenerateQuiz}
        onOpenChange={setShowGenerateQuiz}
        notebookId={notebookId}
      />

      <GenerateFlashcardsDialog
        open={showGenerateFlashcards}
        onOpenChange={setShowGenerateFlashcards}
        notebookId={notebookId}
      />

      <ConfirmDialog
        open={Boolean(quizToDelete)}
        onOpenChange={(open) => !open && setQuizToDelete(null)}
        title={t('quiz.deleteQuiz')}
        description={t('quiz.deleteQuizConfirm')}
        confirmText={t('common.delete')}
        onConfirm={handleDeleteQuizConfirm}
        isLoading={deleteQuiz.isPending}
        confirmVariant="destructive"
      />

      <ConfirmDialog
        open={Boolean(deckToDelete)}
        onOpenChange={(open) => !open && setDeckToDelete(null)}
        title={t('flashcards.deleteDeck')}
        description={t('flashcards.deleteDeckConfirm')}
        confirmText={t('common.delete')}
        onConfirm={handleDeleteDeckConfirm}
        isLoading={deleteDeck.isPending}
        confirmVariant="destructive"
      />
    </>
  )
}
