/**
 * Logger utility — gated behind import.meta.env.DEV
 * Replaces console.log in all frontend code (coding_conventions.md rule 4)
 */
const isDev = import.meta.env.DEV

export const logger = {
  info: (...args: unknown[]) => {
    if (isDev) {
      // eslint-disable-next-line no-console
      console.info('[IP-SAKTI]', ...args)
    }
  },
  warn: (...args: unknown[]) => {
    if (isDev) {
      // eslint-disable-next-line no-console
      console.warn('[IP-SAKTI]', ...args)
    }
  },
  error: (...args: unknown[]) => {
    if (isDev) {
      // eslint-disable-next-line no-console
      console.error('[IP-SAKTI]', ...args)
    }
  },
} as const
