'use client'

import { useMemo, useState } from 'react'
import { Shuffle } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { cn } from '@/lib/utils'
import { useTranslation } from '@/lib/hooks/use-translation'
import { Flashcard, FlashcardDeck } from '@/lib/types/flashcards'

function shuffle<T>(items: T[]): T[] {
  const shuffled = [...items]
  for (let i = shuffled.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1))
    ;[shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]]
  }
  return shuffled
}

interface FlashcardStudySessionProps {
  deck: FlashcardDeck
  onExit: () => void
}

export function FlashcardStudySession({ deck, onExit }: FlashcardStudySessionProps) {
  const { t } = useTranslation()
  const [cards, setCards] = useState<Flashcard[]>(deck.cards)
  const [currentIndex, setCurrentIndex] = useState(0)
  const [flipped, setFlipped] = useState(false)
  const [knownCount, setKnownCount] = useState(0)
  const [finished, setFinished] = useState(false)

  const totalCards = cards.length
  const currentCard = cards[currentIndex]

  const progressLabel = useMemo(
    () =>
      t('flashcards.cardProgress')
        .replace('{current}', String(currentIndex + 1))
        .replace('{total}', String(totalCards)),
    [t, currentIndex, totalCards]
  )

  const handleShuffle = () => {
    setCards(shuffle(deck.cards))
    setCurrentIndex(0)
    setFlipped(false)
  }

  const advance = () => {
    if (currentIndex + 1 >= totalCards) {
      setFinished(true)
      return
    }
    setCurrentIndex((index) => index + 1)
    setFlipped(false)
  }

  const handleKnown = () => {
    setKnownCount((count) => count + 1)
    advance()
  }

  const handleStillLearning = () => {
    advance()
  }

  const handleRestart = () => {
    setCards(deck.cards)
    setCurrentIndex(0)
    setFlipped(false)
    setKnownCount(0)
    setFinished(false)
  }

  if (finished) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>{deck.title}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-lg font-medium">
            {t('flashcards.studyComplete')
              .replace('{known}', String(knownCount))
              .replace('{total}', String(totalCards))}
          </p>
          <div className="flex gap-2">
            <Button onClick={handleRestart}>{t('flashcards.restart')}</Button>
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
          <CardTitle className="text-base">{deck.title}</CardTitle>
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">{progressLabel}</span>
            <Button variant="ghost" size="sm" onClick={handleShuffle} title={t('flashcards.shuffle')}>
              <Shuffle className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <button
          type="button"
          onClick={() => setFlipped((value) => !value)}
          className={cn(
            'w-full min-h-[200px] flex items-center justify-center text-center p-6',
            'border rounded-lg text-lg font-medium hover:bg-accent/30 transition-colors'
          )}
        >
          {flipped ? currentCard.back : currentCard.front}
        </button>
        <p className="text-center text-xs text-muted-foreground">
          {t('flashcards.flip')}
        </p>

        <div className="flex justify-between gap-2 pt-2">
          <Button variant="outline" onClick={onExit}>
            {t('common.close')}
          </Button>
          <div className="flex gap-2">
            <Button variant="outline" onClick={handleStillLearning}>
              {t('flashcards.stillLearning')}
            </Button>
            <Button onClick={handleKnown}>{t('flashcards.knowIt')}</Button>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
