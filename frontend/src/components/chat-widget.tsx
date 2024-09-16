import { useState, useRef, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardFooter, CardHeader } from "@/components/ui/card"
import { LogOut, Maximize2, Minimize2, Pencil, Send, Trash2, Settings } from 'lucide-react'
import { v4 as randomUUID } from 'uuid'
import { useNavigate } from 'react-router-dom'
import EVAIcon from "@/assets/after-ava-graphic.png"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import { Skeleton } from '@/components/ui/skeleton';
import { useAuth } from '@/contexts/useAuth'


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

type Settings = {
  isMaximized: boolean;
  // Add other settings here in the future
}

const defaultSettings: Settings = {
  isMaximized: false,
}

const loadSettings = (): Settings => {
  const storedSettings = localStorage.getItem('chatWidgetSettings')
  return storedSettings ? JSON.parse(storedSettings) : defaultSettings
}

const saveSettings = (settings: Settings) => {
  localStorage.setItem('chatWidgetSettings', JSON.stringify(settings))
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
  const { user, logout } = useAuth();
  const [messages, setMessages] = useState<Message[]>([]);
  const [isInitialLoading, setIsInitialLoading] = useState(true);
  const [input, setInput] = useState('')
  const [editingInput, setEditingInput] = useState('')
  const [isLoading, setIsLoading] = useState(false);
  const [context, setContext] = useState('Onboarding')
  const [settings, setSettings] = useState<Settings>(loadSettings())
  const [isFirstLoad, setIsFirstLoad] = useState(true);


  const messagesEndRef = useRef<HTMLDivElement>(null)

  const navigate = useNavigate();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    if (!user) {
      navigate('/login');
    } else if (user) {
      fetchAllMessages();
    }
  }, [user, navigate]);

  useEffect(() => {
    saveSettings(settings);
  }, [settings]);
  
  const fetchAllMessages = async () => {
    try {
      setIsInitialLoading(true);
      const response = await fetchWithAuth('/messages');
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
      // Show error message to user
    } finally {
      setIsInitialLoading(false);
    }
  };


  useEffect(() => {
    if (isFirstLoad && messages.length > 0) {
      scrollToBottom();
      setIsFirstLoad(false);
    }
  }, [messages, isFirstLoad]);

  const handleSendMessage = async () => {
    if (input.trim() === '') return;

    const newUserMessage: Message = { id: randomUUID(), role: 'user', content: input };
    setMessages((prevMessages) => [...prevMessages, newUserMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await fetchWithAuth('/messages', {
        method: 'POST',
        body: JSON.stringify({ content: input, id: newUserMessage.id }),
      });

      if (!response.ok) {
        throw new Error('Failed to send message');
      }

      const reader = response.body!.getReader();
      const decoder = new TextDecoder();

      let botMessageId: string | null = null;
      let botMessageContent = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const jsonStr = line.slice(5).trim();
              if (jsonStr) {
                const data = JSON.parse(jsonStr);
                if (!botMessageId) {
                  botMessageId = data.id;
                  setMessages((prevMessages) => [
                    ...prevMessages,
                    { id: botMessageId!, role: 'assistant', content: '' }
                  ]);
                }
                botMessageContent += data.content;
                setMessages((prevMessages) =>
                  prevMessages.map((msg) =>
                    msg.id === botMessageId
                      ? { ...msg, content: botMessageContent }
                      : msg
                  )
                );
              }
            } catch (error) {
              console.error('Error parsing JSON:', error);
            }
          }
        }
        scrollToBottom();
      }

    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage: Message = { 
        id: randomUUID(), 
        role: 'assistant', 
        content: 'Sorry, there was an error processing your request. Please try again.' 
      };
      setMessages((prevMessages) => [...prevMessages, errorMessage]);
    } finally {
      setIsLoading(false);
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

  const handleLogout = () => {
    logout();
    navigate('/login');
 
  }

  const toggleMaximize = () => {
    setSettings(prevSettings => ({
      ...prevSettings,
      isMaximized: !prevSettings.isMaximized
    }));
  }

  const cardClassName = settings.isMaximized 
    ? "w-full h-full fixed top-0 left-0 z-50 m-0 rounded-none"
    : "w-[450px] h-[700px] flex flex-col";

  return (
    <div className={`flex items-center justify-center ${settings.isMaximized ? 'min-h-screen bg-gray-100' : 'h-screen'}`}>
      <Card className={`${cardClassName} flex flex-col`}>
        <CardHeader className="flex flex-row justify-between items-start p-4">
          <Button variant="ghost" size="icon" onClick={toggleMaximize}>
            {settings.isMaximized ? <Minimize2 className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
          </Button>
          <div className="flex flex-col items-center text-center">
            <Avatar className="mb-2">
              <AvatarImage src={EVAIcon} alt="Eva" />
              <AvatarFallback>EVA</AvatarFallback>
            </Avatar>
            <p className="text-sm text-gray-500">Hey 👋, I'm Eva <br/> Ask me anything or pick a place to start</p>
          </div>
          <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button variant="ghost" size="icon" onClick={handleLogout}>
                    <LogOut className="h-4 w-4" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  <p>Logout</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
        </CardHeader>
        <CardContent className="flex-grow overflow-auto p-4">
          {isInitialLoading ? (
            <MessageSkeleton />
          ) : (
            messages.map((message) => (
              <div key={message.id} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'} mb-4`}>
                {message.role === 'assistant' && (
                  <Avatar className="mr-2">
                    <AvatarImage src={EVAIcon} alt="Ava" />
                    <AvatarFallback>EVA</AvatarFallback>
                  </Avatar>
                )}
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
                    <ReactMarkdown className={"text-sm"}>{message.content}</ReactMarkdown>
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
            ))
          )}
          {isLoading && (
            <div className="flex justify-start mb-4">
              <Avatar className="mr-2">
                <AvatarImage src={EVAIcon} alt="Ava" />
                <AvatarFallback>EVA</AvatarFallback>
              </Avatar>
              <div className="max-w-[70%] bg-gray-100 rounded-lg p-3">
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                  <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></div>
                </div>
              </div>
            </div>
          )}
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
        <div className="flex justify-between items-center px-4 py-2 bg-gray-100">
          <div className="flex items-center space-x-2">
            <span className="text-sm text-gray-500">Context</span>
            <select
              value={context}
              onChange={(e) => setContext(e.target.value)}
              className="bg-transparent text-sm"
            >
              <option>Onboarding</option>
              <option>Support</option>
              <option>Sales</option>
            </select>
          </div>
          <div className="flex items-center space-x-2">
            <Button variant="ghost" size="icon">
              <Settings className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </Card>
    </div>
  )
}

function MessageSkeleton() {
  return (
    <div className="flex items-center space-x-4 mb-4">
      <Skeleton className="h-10 w-10 rounded-full" />
      <div className="space-y-2">
        <Skeleton className="h-4 w-[250px]" />
        <Skeleton className="h-4 w-[200px]" />
      </div>
    </div>
  )
}