import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { InternationalCountry, JurisdictionMode } from '@/types'

interface JurisdictionState {
  mode: JurisdictionMode
  internationalCountry: InternationalCountry
  setMode: (mode: JurisdictionMode) => void
  setInternationalCountry: (country: InternationalCountry) => void
}

export const useJurisdictionStore = create<JurisdictionState>()(
  persist(
    (set) => ({
      mode: 'INDIA',
      internationalCountry: 'USA',

      setMode: (mode) => set({ mode }),
      setInternationalCountry: (country) =>
        set({ internationalCountry: country }),
    }),
    {
      name: 'ip-sakti-jurisdiction',
    }
  )
)
