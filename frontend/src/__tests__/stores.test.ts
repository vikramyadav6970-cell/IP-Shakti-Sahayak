import { describe, it, expect, beforeEach } from 'vitest'
import { useIntentStore } from '../store/useIntentStore'
import { useJurisdictionStore } from '../store/useJurisdictionStore'
import { useAuthStore } from '../store/useAuthStore'

describe('Zustand Stores Suite', () => {
  beforeEach(() => {
    useIntentStore.getState().reset()
    useAuthStore.getState().logout()
  })

  describe('useIntentStore', () => {
    it('initializes with null domain_intent and empty session state', () => {
      const state = useIntentStore.getState()
      expect(state.domain_intent).toBeNull()
      expect(state.context_questions).toEqual([])
      expect(state.context_answers).toEqual({})
      expect(state.context_object).toBeNull()
      expect(state.entity_set).toBeNull()
    })

    it('updates domain intent correctly', () => {
      useIntentStore.getState().setDomainIntent('PATENT')
      expect(useIntentStore.getState().domain_intent).toBe('PATENT')
    })

    it('updates context answer per question ID', () => {
      useIntentStore.getState().setContextAnswer('pat_novel', 'Novel extraction of curcumin')
      expect(useIntentStore.getState().context_answers['pat_novel']).toBe('Novel extraction of curcumin')
    })

    it('resets full session on reset()', () => {
      useIntentStore.getState().setDomainIntent('MEDICINAL')
      useIntentStore.getState().setContextAnswer('q1', 'ans1')
      useIntentStore.getState().reset()

      const state = useIntentStore.getState()
      expect(state.domain_intent).toBeNull()
      expect(state.context_answers).toEqual({})
    })
  })

  describe('useJurisdictionStore', () => {
    it('defaults to India jurisdiction mode', () => {
      const state = useJurisdictionStore.getState()
      expect(state.mode).toBe('INDIA')
      expect(state.internationalCountry).toBeDefined()
    })

    it('toggles to International mode and allows setting destination country', () => {
      useJurisdictionStore.getState().setMode('INTERNATIONAL')
      useJurisdictionStore.getState().setInternationalCountry('EU')

      const state = useJurisdictionStore.getState()
      expect(state.mode).toBe('INTERNATIONAL')
      expect(state.internationalCountry).toBe('EU')
    })
  })

  describe('useAuthStore', () => {
    it('handles login and logout correctly', () => {
      expect(useAuthStore.getState().isAuthenticated).toBe(false)
      expect(useAuthStore.getState().user).toBeNull()

      useAuthStore.getState().login(
        {
          id: 'user_1',
          email: 'test@ayush.gov.in',
          name: 'Test Innovator',
          role: 'USER',
        },
        'mock-token'
      )

      expect(useAuthStore.getState().isAuthenticated).toBe(true)
      expect(useAuthStore.getState().user?.email).toBe('test@ayush.gov.in')
      expect(useAuthStore.getState().token).toBe('mock-token')

      useAuthStore.getState().logout()
      expect(useAuthStore.getState().isAuthenticated).toBe(false)
      expect(useAuthStore.getState().user).toBeNull()
    })
  })
})
