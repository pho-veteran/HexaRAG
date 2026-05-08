async function main() {
  const targets = await fetch('http://127.0.0.1:9222/json/list').then((response) => response.json())
  const target = targets.find((entry) => entry.url === 'https://d1utyuhmju4jzn.cloudfront.net/')

  if (!target) {
    throw new Error('CloudFront target not found in DevTools target list.')
  }

  const socket = new WebSocket(target.webSocketDebuggerUrl)
  await new Promise((resolve, reject) => {
    socket.addEventListener('open', resolve, { once: true })
    socket.addEventListener('error', reject, { once: true })
  })

  let nextId = 0
  const pending = new Map()
  const requests = []
  const responses = []

  socket.addEventListener('message', (message) => {
    const payload = JSON.parse(message.data)

    if (payload.id) {
      const handler = pending.get(payload.id)
      if (!handler) return
      pending.delete(payload.id)
      if (payload.error) {
        handler.reject(new Error(payload.error.message))
      } else {
        handler.resolve(payload.result)
      }
      return
    }

    if (payload.method === 'Network.requestWillBeSent') {
      requests.push({
        url: payload.params.request.url,
        method: payload.params.request.method,
        type: payload.params.type ?? null,
      })
    }

    if (payload.method === 'Network.responseReceived') {
      responses.push({
        url: payload.params.response.url,
        status: payload.params.response.status,
        mimeType: payload.params.response.mimeType,
      })
    }
  })

  function send(method, params = {}) {
    const id = ++nextId
    socket.send(JSON.stringify({ id, method, params }))
    return new Promise((resolve, reject) => {
      pending.set(id, { resolve, reject })
      setTimeout(() => {
        if (!pending.has(id)) return
        pending.delete(id)
        reject(new Error(`Timed out waiting for ${method}`))
      }, 15000)
    })
  }

  async function evaluate(expression) {
    const result = await send('Runtime.evaluate', {
      expression,
      awaitPromise: true,
      returnByValue: true,
    })
    if (result.exceptionDetails) {
      throw new Error(result.exceptionDetails.text || 'Runtime.evaluate failed')
    }
    return result.result.value
  }

  const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms))

  await send('Network.enable')
  await send('Page.enable')
  await send('Runtime.enable')
  await send('Page.navigate', { url: 'https://d1utyuhmju4jzn.cloudfront.net/' })
  await sleep(3000)

  const initial = await evaluate(`(() => ({
    title: document.title,
    textareaPresent: !!document.querySelector('textarea#chat-message'),
    inspectionConsolePresent: !!Array.from(document.querySelectorAll('h2')).find((heading) => heading.textContent.includes('Inspection console')),
    sendButtonDisabled: Array.from(document.querySelectorAll('button')).find((button) => button.textContent.trim() === 'Send')?.disabled ?? null,
    bodyText: document.body.innerText
  }))()`)

  await evaluate(`(() => {
    if (!window.__hexaragFetchWrapped) {
      window.__hexaragFetchWrapped = true
      window.__hexaragFetchCalls = []
      const originalFetch = window.fetch.bind(window)
      window.fetch = async (...args) => {
        const [input, init] = args
        const url = typeof input === 'string' ? input : input.url
        const method = init?.method ?? (typeof input === 'object' && input.method ? input.method : 'GET')
        const entry = { url, method, status: 'pending' }
        window.__hexaragFetchCalls.push(entry)
        try {
          const response = await originalFetch(...args)
          entry.status = 'resolved'
          entry.responseUrl = response.url
          entry.httpStatus = response.status
          return response
        } catch (error) {
          entry.status = 'rejected'
          entry.error = error?.message ?? String(error)
          throw error
        }
      }
    }

    const textarea = document.querySelector('textarea#chat-message')
    const setter = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value').set
    setter.call(textarea, 'What is PaymentGW current latency right now?')
    textarea.dispatchEvent(new InputEvent('input', { bubbles: true, data: 'What is PaymentGW current latency right now?' }))
    return true
  })()`)

  await sleep(1000)

  const afterInput = await evaluate(`(() => ({
    textareaValue: document.querySelector('textarea#chat-message')?.value ?? null,
    sendButtonDisabled: Array.from(document.querySelectorAll('button')).find((button) => button.textContent.trim() === 'Send')?.disabled ?? null,
    sendButtonText: Array.from(document.querySelectorAll('button')).find((button) => button.textContent.trim() === 'Send')?.textContent?.trim() ?? null
  }))()`)

  await evaluate(`(() => {
    const form = document.querySelector('form.composer')
    form.requestSubmit()
    return true
  })()`)

  await sleep(15000)

  const finalState = await evaluate(`(() => ({
    bodyText: document.body.innerText,
    traceSections: Array.from(document.querySelectorAll('.trace-section h3')).map((node) => node.textContent.trim()),
    traceHeader: document.querySelector('.trace-header p')?.textContent ?? null,
    assistantCards: Array.from(document.querySelectorAll('.message-card--assistant')).length,
    inspectButtons: Array.from(document.querySelectorAll('button')).filter((button) => button.textContent.trim() === 'Inspect response').length,
    toolSummaryVisible: document.body.innerText.includes('/get-metrics returned data.'),
    responseVisible: document.body.innerText.includes('Response 1'),
    errorVisible: document.body.innerText.includes('Error details') || document.body.innerText.includes('Failed to fetch')
  }))()`)

  const pageFetchCalls = await evaluate(`(() => window.__hexaragFetchCalls ?? [])()`)
  const filteredRequests = requests.filter((entry) => entry.url.includes('execute-api') || entry.url.includes('localhost'))
  const filteredResponses = responses.filter((entry) => entry.url.includes('execute-api') || entry.url.includes('localhost'))

  console.log(JSON.stringify({ initial, afterInput, pageFetchCalls, finalState, filteredRequests, filteredResponses }, null, 2))
  socket.close()
}

main().catch((error) => {
  console.error(error)
  process.exit(1)
})
