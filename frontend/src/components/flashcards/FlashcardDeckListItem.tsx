'use client'

import { Trash2 } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { formatDistanceToNow } from 'date-fns'
import { getDateLocale } from '@/lib/utils/date-locale'
import { useTranslation } from '@/lib/hooks/use-translation'
import { FlashcardDeck } from '@/lib/types/flashcards'

interface FlashcardDeckListItemProps {
  deck: FlashcardDeck
  onStart: (deck: FlashcardDeck) => void
  onDelete: (deckId: string) => void
}

export function FlashcardDeckListItem({
  deck,
  onStart,
  onDelete,
}: FlashcardDeckListItemProps) {
  const { t, language } = useTranslation()

  return (
    <div className="p-3 border rounded-lg card-hover group relative">
      <div className="flex items-start justify-between gap-2 mb-2">
        <h4 className="text-sm font-medium">{deck.title}</h4>
        <Button
          variant="ghost"
          size="sm"
          className="h-8 w-8 p-0 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0"
          onClick={() => deck.id && onDelete(deck.id)}
        >
          <Trash2 className="h-4 w-4" />
        </Button>
      </div>
      <div className="flex items-center justify-between gap-2">
        <span className="text-xs text-muted-foreground">
          {t('flashcards.cardsCount').replace('{count}', String(deck.cards.length))}
          {' · '}
          {formatDistanceToNow(new Date(deck.created), {
            addSuffix: true,
            locale: getDateLocale(language),
          })}
        </span>
        <Button size="sm" onClick={() => onStart(deck)}>
          {t('flashcards.study')}
        </Button>
      </div>
    </div>
  )
}
