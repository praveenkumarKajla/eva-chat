import { useState, useRef, useEffect } from 'react'
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardFooter, CardHeader } from "@/components/ui/card"
import { Send } from 'lucide-react'

type Message = {
  id: string;
  role: 'user' | 'assistant';
  content: string;
}

export default function ChatWidget() {
  const [messages, setMessages] = useState<Message[]>([
    { id: '0', role: 'assistant', content: "Hey👋, I'm Ava\nAsk me anything or pick a place to start" },
  ])
  const [input, setInput] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(scrollToBottom, [messages])

  const handleSendMessage = () => {
    if (input.trim() === '') return;

    const newUserMessage: Message = { id: Date.now().toString(), role: 'user', content: input };
    setMessages((prevMessages) => [...prevMessages, newUserMessage]);
    setInput('');

    // TODO: Implement actual message sending logic
  }

  return (
    <div className="flex items-center justify-center h-screen">
      <Card className="w-[450px] h-[700px] flex flex-col">
        <CardHeader className="flex flex-col items-center text-center p-4">
          <Avatar className="mb-2">
            <AvatarFallback>AVA</AvatarFallback>
          </Avatar>
          <p className="text-sm text-gray-500">Hey 👋, I'm Ava <br/> Ask me anything or pick a place to start</p>
        </CardHeader>
        <CardContent className="flex-grow overflow-auto p-4">
          {messages.map((message) => (
            <div key={message.id} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'} mb-4`}>
              <div className={`max-w-[70%] ${message.role === 'user' ? 'bg-purple-500 text-white' : 'bg-gray-100'} rounded-lg p-3`}>
                <p className="text-sm">{message.content}</p>
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </CardContent>
        <CardFooter className="p-4">
          <div className="flex items-center w-full space-x-2">
            <Input
              placeholder="Type your message..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
            />
            <Button onClick={handleSendMessage}><Send className="h-4 w-4" /></Button>
          </div>
        </CardFooter>
      </Card>
    </div>
  )
}