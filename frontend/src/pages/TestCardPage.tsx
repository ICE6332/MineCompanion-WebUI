import { useState } from "react"

import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

const TestCardPage = () => {
  const [jsonText, setJsonText] = useState<string>(
    JSON.stringify(
      {
        type: "conversation_message",
        data: {
          companionName: "AICompanion",
          text: "你好，这是从 Web UI 发送的测试消息。",
        },
      },
      null,
      2,
    ),
  )
  const [sendStatus, setSendStatus] = useState<string | null>(null)
  const [sending, setSending] = useState(false)

  const handleSendJson = async () => {
    setSendStatus(null)

    let payload: unknown
    try {
      payload = JSON.parse(jsonText)
    } catch {
      setSendStatus("JSON 格式错误，请检查后重试")
      return
    }

    setSending(true)
    try {
      const res = await fetch("/api/ws/send-json", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      })

      if (!res.ok) {
        const text = await res.text()
        setSendStatus(`发送失败：${res.status} ${text || ""}`.trim())
      } else {
        setSendStatus("发送成功，请在游戏内聊天栏查看效果")
      }
    } catch {
      setSendStatus("发送失败：网络或服务异常")
    } finally {
      setSending(false)
    }
  }

  return (
    <main className="space-y-6 p-6">
      <header className="space-y-3">
        <h1 className="text-3xl md:text-4xl font-bold">WebSocket 测试工具</h1>
        <p className="text-muted-foreground max-w-3xl">
          从 Web UI 直接向 AI 服务发送自定义 JSON 消息，用于测试 Mod ↔ Service 通信链路。
        </p>
      </header>

      <section aria-labelledby="ws-json-test" className="max-w-4xl">
        <Card>
          <CardHeader>
            <CardTitle>发送自定义 JSON 消息</CardTitle>
            <CardDescription>
              编辑 JSON 负载并通过服务端转发给当前已连接的模组实例。建议先使用
              <code className="mx-1 text-xs bg-muted px-1 py-0.5 rounded">conversation_message</code>
              类型验证通信是否正常。
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Textarea
              rows={14}
              value={jsonText}
              onChange={(event) => setJsonText(event.target.value)}
              placeholder='在此粘贴要发送的 JSON，例如 { "type": "conversation_message", "data": { ... } }'
              className="font-mono text-sm"
            />
            <div className="flex items-center gap-3">
              <Button type="button" onClick={handleSendJson} disabled={sending}>
                {sending ? "发送中..." : "发送 JSON 消息到模组"}
              </Button>
              {sendStatus ? (
                <span className="text-sm text-muted-foreground">{sendStatus}</span>
              ) : null}
            </div>
          </CardContent>
        </Card>
      </section>
    </main>
  )
}

export default TestCardPage
export { TestCardPage }
