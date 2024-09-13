import { useState, useRef, useEffect } from 'react'
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardFooter, CardHeader } from "@/components/ui/card"
import { Pencil, Send, Trash2 } from 'lucide-react'
import { v4 as randomUUID } from 'uuid'
import { useNavigate } from 'react-router-dom'

type BackendMessage = {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  sender: string;
  timestamp: string;
}

type Message = {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  isEditing?: boolean;
}


const API_BASE_URL = 'http://localhost:8000';

const fetchWithAuth = (url: string, options: RequestInit = {}) => {
  const token = localStorage.getItem('jwt_token'); // Assume token is stored in localStorage after login
  return fetch(`${API_BASE_URL}${url}`, {
    ...options,
    headers: {
      ...options.headers,
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  });
};

export default function ChatWidget() {
  const [messages, setMessages] = useState<Message[]>([
    { id: '0', role: 'assistant', content: "Hey👋, I'm Ava\nAsk me anything or pick a place to start" },
  ])
  const [input, setInput] = useState('')
  const [editingInput, setEditingInput] = useState('')

  const messagesEndRef = useRef<HTMLDivElement>(null)

  const navigate = useNavigate();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    const token = localStorage.getItem('jwt_token');
    if (!token) {
      navigate('/login');
    } else {
      fetchAllMessages();
    }
  }, []);
  
  const fetchAllMessages = async () => {
    try {
      const response = await fetchWithAuth('/messages');
      if (response.status === 401) {
        navigate('/login');
        return;
      }
      if (!response.ok) {
        throw new Error('Failed to fetch messages');
      }
      const data: BackendMessage[] = await response.json();
      const fetchedMessages: Message[] = data.map((msg) => ({
        id: msg.id,
        role: msg.role,
        content: msg.content
      }));
      setMessages(fetchedMessages);
    } catch (error) {
      console.error('Error fetching messages:', error);
    }
  };


  useEffect(scrollToBottom, [messages])

  const handleSendMessage = async () => {
    if (input.trim() === '') return;

    const newUserMessage: Message = { id: randomUUID(), role: 'user', content: input };
    setMessages((prevMessages) => [...prevMessages, newUserMessage]);
    setInput('');

    try {
      const response = await fetchWithAuth('/messages', {
        method: 'POST',
        body: JSON.stringify({ content: input, id: newUserMessage.id }),
      });

      if (response.status === 401) {
        navigate('/login');
        return;
      }

      if (!response.ok) {
        throw new Error('Failed to send message');
      }

      const data = await response.json();
      
      const botMessage: Message = {
        id: data.id,
        role: data.role,
        content: data.content
      };

      setMessages((prevMessages) => [...prevMessages, botMessage]);

    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage: Message = { id: randomUUID(), role: 'assistant', content: 'Sorry, there was an error processing your request.' };
      setMessages((prevMessages) => [...prevMessages, errorMessage]);
    }
  };

  const handleDeleteMessage = async (id: string) => {
    try {
      const response = await fetchWithAuth(`/messages/${id}`, {
        method: 'DELETE',
      });
      if (!response.ok) {
        throw new Error('Failed to delete message');
      }
      // After successful deletion, fetch all messages
      await fetchAllMessages();
    } catch (error) {
      console.error('Error deleting message:', error);
    }
  };

  const handleEditMessage = (id: string, content: string) => {
    setEditingInput(content)
    setMessages(prev => prev.map(message => 
      message.id === id ? { ...message, isEditing: true } : message
    ))
  }

  const handleSaveEdit = async (id: string, newContent: string) => {
    if (newContent.trim()) {
      try {
        const response = await fetchWithAuth(`/messages/${id}`, {
          method: 'PUT',
          body: JSON.stringify({ content: newContent }),
        });
        if (!response.ok) {
          throw new Error('Failed to update message');
        }
        const updatedMessages = messages.map(message => 
          message.id === id ? { ...message, content: newContent, isEditing: false } : message
        );
        setMessages(updatedMessages);
        setEditingInput('');
      } catch (error) {
        console.error('Error updating message:', error);
      }
    } else {
      handleCancelEdit(id);
    }
  }

  const handleCancelEdit = (id: string) => {
    setMessages(prev => prev.map(message => 
      message.id === id ? { ...message, isEditing: false } : message
    ))
    setEditingInput('')
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
              <div className={`max-w-[70%] ${message.role === 'user' ? 'bg-purple-500 text-white group relative' : 'bg-gray-100'} rounded-lg p-3`}>
               
                {message.isEditing ? (
                  <div className="flex flex-col space-y-2">
                    <Input
                      value={editingInput}
                      onChange={(e) => setEditingInput(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && handleSaveEdit(message.id, editingInput)}
                      autoFocus
                    />
                    <div className="flex justify-end space-x-2">
                      <Button size="sm" variant="ghost" onClick={() => handleCancelEdit(message.id)}>
                        Cancel
                      </Button>
                      <Button size="sm" onClick={() => handleSaveEdit(message.id, editingInput)}>
                        Save
                      </Button>
                    </div>
                  </div>
                ) : (
                  <p className="text-sm">{message.content}</p>
                )}
                {message.role === 'user' && !message.isEditing && (
                  <div className="absolute top-0 right-0 mt-1 mr-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  <Button variant="ghost" size="icon" onClick={() => handleEditMessage(message.id, message.content)}>
                    <Pencil className="h-4 w-4" />
                  </Button>
                  <Button variant="ghost" size="icon" onClick={() => handleDeleteMessage(message.id)}>
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
                )}
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