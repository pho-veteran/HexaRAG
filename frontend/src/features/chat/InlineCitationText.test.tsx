import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import type { Citation, InlineCitationAnchor } from '../../types/chat'
import { InlineCitationText } from './InlineCitationText'

const citations: Citation[] = [
  {
    sourceId: 'doc-ownership',
    title: 'ownership.md',
    excerpt: 'Notifications is owned by Team Mercury.',
  },
  {
    sourceId: 'doc-escalation',
    title: 'escalation.md',
    excerpt: 'Mercury handles after-hours escalations.',
  },
]

function buildAnchors(content: string): InlineCitationAnchor[] {
  const firstClaim = 'Team Mercury owns Notifications.'
  const secondClaim = 'Mercury also handles escalations.'
  const firstStart = content.indexOf(firstClaim)
  const secondStart = content.indexOf(secondClaim)

  return [
    {
      start: firstStart,
      end: firstStart + firstClaim.length,
      sourceIds: ['doc-ownership'],
    },
    {
      start: secondStart,
      end: secondStart + secondClaim.length,
      sourceIds: ['doc-ownership', 'doc-escalation'],
    },
  ]
}

describe('InlineCitationText', () => {
  it('reuses the same number for repeated source references and renders multi-source markers', () => {
    const content = 'Team Mercury owns Notifications. Mercury also handles escalations.'

    render(
      <InlineCitationText
        content={content}
        citations={citations}
        inlineCitations={buildAnchors(content)}
        onCitationClick={() => undefined}
      />,
    )

    expect(screen.getAllByRole('button', { name: '[1]' })).toHaveLength(2)
    expect(screen.getAllByRole('button', { name: '[2]' })).toHaveLength(1)
  })

  it('calls back with the clicked source id', async () => {
    const content = 'Team Mercury owns Notifications. Mercury also handles escalations.'
    const handleCitationClick = vi.fn()
    const user = userEvent.setup()

    render(
      <InlineCitationText
        content={content}
        citations={citations}
        inlineCitations={buildAnchors(content)}
        onCitationClick={handleCitationClick}
      />,
    )

    await user.click(screen.getAllByRole('button', { name: '[1]' })[1])
    await user.click(screen.getByRole('button', { name: '[2]' }))

    expect(handleCitationClick).toHaveBeenNthCalledWith(1, 'doc-ownership')
    expect(handleCitationClick).toHaveBeenNthCalledWith(2, 'doc-escalation')
  })

  it('falls back to plain text when inline citations are absent', () => {
    render(
      <InlineCitationText
        content="Team Mercury owns Notifications."
        citations={citations}
        inlineCitations={[]}
        onCitationClick={() => undefined}
      />,
    )

    expect(screen.getByText('Team Mercury owns Notifications.')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: '[1]' })).not.toBeInTheDocument()
  })
})
