export const sampleQuestions = [
  {
    level: 'L1',
    title: 'Single-source retrieval',
    prompt: 'Who owns the Notifications service?',
  },
  {
    level: 'L2',
    title: 'Contradiction handling',
    prompt: 'What changed in the on-call escalation policy, and which document is newer?',
  },
  {
    level: 'L3',
    title: 'Live operational metrics',
    prompt: 'What is PaymentGW current latency right now?',
  },
  {
    level: 'L4',
    title: 'Recent-turn continuity',
    prompt: 'Why did its costs spike last month?',
  },
  {
    level: 'L5',
    title: 'Launch-readiness investigation',
    prompt: 'Investigate whether Checkout is healthy enough for a product launch today.',
  },
] as const
