import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export type FocusableColumn = 'sources' | 'notes' | 'study'

interface NotebookColumnsState {
  sourcesCollapsed: boolean
  notesCollapsed: boolean
  studyCollapsed: boolean
  // When set, that panel is "maximized": it takes the majority of the width and
  // the other collapsible panels shrink to slim strips for a cleaner, focused view.
  focusedColumn: FocusableColumn | null
  toggleSources: () => void
  toggleNotes: () => void
  toggleStudy: () => void
  setSources: (collapsed: boolean) => void
  setNotes: (collapsed: boolean) => void
  setStudy: (collapsed: boolean) => void
  toggleFocus: (col: FocusableColumn) => void
  clearFocus: () => void
}

export const useNotebookColumnsStore = create<NotebookColumnsState>()(
  persist(
    (set) => ({
      sourcesCollapsed: false,
      notesCollapsed: false,
      studyCollapsed: true,
      focusedColumn: null,
      // Manually collapsing/expanding a panel exits focus mode to avoid ambiguous states.
      toggleSources: () =>
        set((state) => ({ sourcesCollapsed: !state.sourcesCollapsed, focusedColumn: null })),
      toggleNotes: () =>
        set((state) => ({ notesCollapsed: !state.notesCollapsed, focusedColumn: null })),
      toggleStudy: () =>
        set((state) => ({ studyCollapsed: !state.studyCollapsed, focusedColumn: null })),
      setSources: (collapsed) => set({ sourcesCollapsed: collapsed }),
      setNotes: (collapsed) => set({ notesCollapsed: collapsed }),
      setStudy: (collapsed) => set({ studyCollapsed: collapsed }),
      toggleFocus: (col) =>
        set((state) => {
          if (state.focusedColumn === col) {
            return { focusedColumn: null }
          }
          // Focusing a panel also un-collapses it so its content is visible.
          const patch: Partial<NotebookColumnsState> = { focusedColumn: col }
          if (col === 'sources') patch.sourcesCollapsed = false
          if (col === 'notes') patch.notesCollapsed = false
          if (col === 'study') patch.studyCollapsed = false
          return patch
        }),
      clearFocus: () => set({ focusedColumn: null }),
    }),
    {
      name: 'notebook-columns-storage',
    }
  )
)
