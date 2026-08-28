/**
 * Types for jurisdictions and country selection.
 * See context.md §2 rule 2: never conflate jurisdictions.
 */

export type JurisdictionMode = 'INDIA' | 'INTERNATIONAL'

export type InternationalCountry =
  | 'USA'
  | 'EU'
  | 'UK'
  | 'JAPAN'
  | 'AUSTRALIA'
  | 'CANADA'
  | 'UAE'
  | 'WHO'
  | 'WIPO'

export interface JurisdictionState {
  mode: JurisdictionMode
  internationalCountry: InternationalCountry
}
