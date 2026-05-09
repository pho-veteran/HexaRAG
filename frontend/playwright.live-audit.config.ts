import { defineConfig } from '@playwright/test'

const baseURL = process.env.HEXARAG_LIVE_FRONTEND_URL ?? 'http://localhost:5173'

export default defineConfig({
  testDir: './tests',
  reporter: [['json', { outputFile: 'playwright-live-audit-report.json' }]],
  use: {
    baseURL,
  },
})
