import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface NotebookColumnsState {
  sourcesCollapsed: boolean
  notesCollapsed: boolean
  studyCollapsed: boolean
  toggleSources: () => void
  toggleNotes: () => void
  toggleStudy: () => void
  setSources: (collapsed: boolean) => void
  setNotes: (collapsed: boolean) => void
  setStudy: (collapsed: boolean) => void
}

export const useNotebookColumnsStore = create<NotebookColumnsState>()(
  persist(
    (set) => ({
      sourcesCollapsed: false,
      notesCollapsed: false,
      studyCollapsed: true,
      toggleSources: () => set((state) => ({ sourcesCollapsed: !state.sourcesCollapsed })),
      toggleNotes: () => set((state) => ({ notesCollapsed: !state.notesCollapsed })),
      toggleStudy: () => set((state) => ({ studyCollapsed: !state.studyCollapsed })),
      setSources: (collapsed) => set({ sourcesCollapsed: collapsed }),
      setNotes: (collapsed) => set({ notesCollapsed: collapsed }),
      setStudy: (collapsed) => set({ studyCollapsed: collapsed }),
    }),
    {
      name: 'notebook-columns-storage',
    }
  )
)
