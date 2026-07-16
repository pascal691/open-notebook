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
import { useGenerateFlashcardDeck } from '@/lib/hooks/use-flashcards'
import { useTranslation } from '@/lib/hooks/use-translation'

interface GenerateFlashcardsDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  notebookId: string
}

export function GenerateFlashcardsDialog({
  open,
  onOpenChange,
  notebookId,
}: GenerateFlashcardsDialogProps) {
  const { t } = useTranslation()
  const [numCards, setNumCards] = useState(15)
  const generateDeck = useGenerateFlashcardDeck(notebookId)

  const closeDialog = () => onOpenChange(false)

  const handleSubmit = async () => {
    try {
      await generateDeck.mutateAsync({ num_cards: numCards })
      closeDialog()
    } catch {
      // Error toast already shown by the mutation hook.
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[420px]">
        <DialogHeader>
          <DialogTitle>{t('flashcards.generate')}</DialogTitle>
          <DialogDescription>{t('flashcards.generateDesc')}</DialogDescription>
        </DialogHeader>

        <div className="space-y-2">
          <Label htmlFor="flashcards-num-cards">{t('flashcards.numCards')}</Label>
          <Input
            id="flashcards-num-cards"
            type="number"
            min={3}
            max={30}
            value={numCards}
            onChange={(e) => setNumCards(Number(e.target.value))}
            autoComplete="off"
          />
        </div>

        <DialogFooter className="gap-2 sm:gap-0">
          <Button type="button" variant="outline" onClick={closeDialog}>
            {t('common.cancel')}
          </Button>
          <Button onClick={handleSubmit} disabled={generateDeck.isPending}>
            {generateDeck.isPending
              ? t('flashcards.generating')
              : t('flashcards.generate')}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
