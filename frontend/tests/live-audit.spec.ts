import { expect, test } from '@playwright/test'

const cases = [
  {
    id: 'L1-01',
    prompt: 'What is the current API rate limit for PaymentGW?',
  },
  {
    id: 'L2-01',
    prompt: "What is PaymentGW's API rate limit?",
  },
  {
    id: 'L3-04',
    prompt: "Is PaymentGW's current error rate within its SLA target?",
  },
  {
    id: 'L4-01',
    prompt: 'Which service had the highest cost in March 2026?',
  },
  {
    id: 'L5-01',
    prompt: 'Assess whether PaymentGW is reliable and recommend improvements.',
  },
]

for (const auditCase of cases) {
  test(`${auditCase.id} renders a response with visible inspection details`, async ({ page }) => {
    await page.goto('/')
    await page.getByRole('textbox', { name: 'Question' }).fill(auditCase.prompt)
    await page.getByRole('button', { name: 'Send' }).click()

    const response = page.getByRole('article', { name: /Response/i }).last()
    await expect(response).toBeVisible()

    const inspectResponse = response.getByRole('button', { name: 'Inspect response' })
    await expect(inspectResponse).toBeVisible()
    await inspectResponse.click()

    const inspectionConsole = page.getByRole('complementary', { name: 'Inspection console' })
    await expect(inspectionConsole).toBeVisible()
    await expect(inspectionConsole.getByRole('tab', { name: 'Observability' })).toHaveAttribute('aria-selected', 'true')
    await expect(inspectionConsole.getByRole('heading', { name: 'Sources' })).toBeVisible()
    await expect(inspectionConsole.getByRole('heading', { name: 'Tool calls' })).toBeVisible()
    await expect(inspectionConsole.getByRole('heading', { name: 'Memory' })).toBeVisible()
    await expect(inspectionConsole.getByRole('heading', { name: 'Grounding' })).toBeVisible()

    await inspectionConsole.getByRole('tab', { name: 'Thinking process' }).click()
    await expect(inspectionConsole.getByRole('tab', { name: 'Thinking process' })).toHaveAttribute('aria-selected', 'true')
    await expect(inspectionConsole.getByRole('heading', { name: 'How the answer was formed' })).toBeVisible()
  })
}
