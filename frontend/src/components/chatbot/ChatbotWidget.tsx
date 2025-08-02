"use client"

import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { 
  MessageCircle,
  X,
  Send,
  Bot,
  User,
  Clock,
  Calendar,
  Heart,
  Pill,
  Stethoscope,
  AlertTriangle,
  Info,
  ChevronUp,
  ChevronDown,
  Sparkles,
  Zap,
  Shield,
  Activity,
  TrendingUp,
  FileText,
  Phone,
  MapPin,
  Star,
  CheckCircle,
  XCircle,
  HelpCircle,
  BookOpen,
  Microscope,
  Thermometer,
  Activity as ActivityIcon,
  Heart as HeartIcon,
  Pill as PillIcon,
  Stethoscope as StethoscopeIcon,
  AlertTriangle as AlertTriangleIcon,
  Info as InfoIcon,
  ChevronUp as ChevronUpIcon,
  ChevronDown as ChevronDownIcon,
  Sparkles as SparklesIcon,
  Zap as ZapIcon,
  Shield as ShieldIcon,
  Activity as ActivityIcon2,
  TrendingUp as TrendingUpIcon,
  FileText as FileTextIcon,
  Phone as PhoneIcon,
  MapPin as MapPinIcon,
  Star as StarIcon,
  CheckCircle as CheckCircleIcon,
  XCircle as XCircleIcon,
  HelpCircle as HelpCircleIcon,
  BookOpen as BookOpenIcon,
  Microscope as MicroscopeIcon,
  Thermometer as ThermometerIcon
} from 'lucide-react'
import { toast } from 'react-hot-toast'

interface Message {
  id: string
  text: string
  sender: 'user' | 'bot'
  timestamp: Date
  type?: 'text' | 'quick_action' | 'appointment_suggestion' | 'health_tip' | 'emergency'
  data?: any
}

interface QuickAction {
  id: string
  label: string
  icon: React.ReactNode
  action: string
  color: string
}

interface HealthTip {
  title: string
  content: string
  category: string
  icon: React.ReactNode
}

export default function ChatbotWidget() {
  const [isOpen, setIsOpen] = useState(false)
  const [isMinimized, setIsMinimized] = useState(false)
  const [messages, setMessages] = useState<Message[]>([])
  const [inputValue, setInputValue] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const [userRole, setUserRole] = useState<'patient' | 'doctor' | 'admin' | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Quick actions based on user role
  const quickActions: QuickAction[] = [
    {
      id: 'book_appointment',
      label: 'Book Appointment',
      icon: <Calendar className="w-4 h-4" />,
      action: 'I would like to book an appointment',
      color: 'bg-blue-500 hover:bg-blue-600'
    },
    {
      id: 'emergency',
      label: 'Emergency Help',
      icon: <AlertTriangleIcon className="w-4 h-4" />,
      action: 'I need emergency medical assistance',
      color: 'bg-red-500 hover:bg-red-600'
    },
    {
      id: 'health_tips',
      label: 'Health Tips',
      icon: <HeartIcon className="w-4 h-4" />,
      action: 'Show me some health tips',
      color: 'bg-green-500 hover:bg-green-600'
    },
    {
      id: 'medication_info',
      label: 'Medication Info',
      icon: <PillIcon className="w-4 h-4" />,
      action: 'Tell me about my medications',
      color: 'bg-purple-500 hover:bg-purple-600'
    },
    {
      id: 'symptoms_check',
      label: 'Symptoms Check',
      icon: <StethoscopeIcon className="w-4 h-4" />,
      action: 'I want to check my symptoms',
      color: 'bg-orange-500 hover:bg-orange-600'
    },
    {
      id: 'find_doctor',
      label: 'Find Doctor',
      icon: <User className="w-4 h-4" />,
      action: 'Help me find a doctor',
      color: 'bg-indigo-500 hover:bg-indigo-600'
    }
  ]

  // Healthcare-specific knowledge base
  const healthTips: HealthTip[] = [
    {
      title: 'Stay Hydrated',
      content: 'Drink at least 8 glasses of water daily to maintain good health and support your body\'s functions.',
      category: 'General Health',
      icon: <ActivityIcon2 className="w-5 h-5 text-blue-500" />
    },
    {
      title: 'Regular Exercise',
      content: 'Aim for at least 150 minutes of moderate exercise per week to improve cardiovascular health.',
      category: 'Fitness',
      icon: <TrendingUpIcon className="w-5 h-5 text-green-500" />
    },
    {
      title: 'Healthy Diet',
      content: 'Include plenty of fruits, vegetables, whole grains, and lean proteins in your daily meals.',
      category: 'Nutrition',
      icon: <HeartIcon className="w-5 h-5 text-red-500" />
    },
    {
      title: 'Sleep Well',
      content: 'Get 7-9 hours of quality sleep each night to support immune function and mental health.',
      category: 'Wellness',
      icon: <ActivityIcon className="w-5 h-5 text-purple-500" />
    }
  ]

  const medicalConditions = {
    'diabetes': {
      symptoms: ['Increased thirst', 'Frequent urination', 'Fatigue', 'Blurred vision'],
      recommendations: ['Monitor blood sugar regularly', 'Follow a balanced diet', 'Exercise regularly', 'Take medications as prescribed'],
      emergency: false
    },
    'hypertension': {
      symptoms: ['Headaches', 'Shortness of breath', 'Nosebleeds', 'Chest pain'],
      recommendations: ['Reduce salt intake', 'Exercise regularly', 'Manage stress', 'Take blood pressure medication'],
      emergency: false
    },
    'asthma': {
      symptoms: ['Wheezing', 'Shortness of breath', 'Chest tightness', 'Coughing'],
      recommendations: ['Avoid triggers', 'Use inhaler as prescribed', 'Monitor symptoms', 'Keep rescue inhaler handy'],
      emergency: true
    }
  }

  useEffect(() => {
    // Get user role from localStorage
    const userData = localStorage.getItem('user')
    if (userData) {
      const user = JSON.parse(userData)
      setUserRole(user.role)
    }

    // Add welcome message
    if (messages.length === 0) {
      addBotMessage(
        `Hello! I'm your AI healthcare assistant. I can help you with:\n\n` +
        `• Booking appointments\n` +
        `• Health information and tips\n` +
        `• Symptom checking\n` +
        `• Medication information\n` +
        `• Emergency assistance\n\n` +
        `How can I help you today?`,
        'text'
      )
    }
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const addUserMessage = (text: string) => {
    const message: Message = {
      id: Date.now().toString(),
      text,
      sender: 'user',
      timestamp: new Date()
    }
    setMessages(prev => [...prev, message])
  }

  const addBotMessage = (text: string, type: Message['type'] = 'text', data?: any) => {
    const message: Message = {
      id: Date.now().toString(),
      text,
      sender: 'bot',
      timestamp: new Date(),
      type,
      data
    }
    setMessages(prev => [...prev, message])
  }

  const handleQuickAction = (action: QuickAction) => {
    addUserMessage(action.action)
    processUserInput(action.action)
  }

  const processUserInput = async (input: string) => {
    setIsTyping(true)
    
    // Simulate API call delay
    await new Promise(resolve => setTimeout(resolve, 1000))

    const lowerInput = input.toLowerCase()

    // Emergency detection
    if (lowerInput.includes('emergency') || lowerInput.includes('chest pain') || lowerInput.includes('can\'t breathe')) {
      addBotMessage(
        '🚨 EMERGENCY ALERT 🚨\n\n' +
        'If you are experiencing a medical emergency, please:\n\n' +
        '1. Call 911 immediately\n' +
        '2. Go to the nearest emergency room\n' +
        '3. Do not wait for online assistance\n\n' +
        'For non-emergency concerns, I can help you schedule an appointment.',
        'emergency'
      )
      setIsTyping(false)
      return
    }

    // Appointment booking
    if (lowerInput.includes('book') || lowerInput.includes('appointment') || lowerInput.includes('schedule')) {
      addBotMessage(
        'I can help you book an appointment! Here are your options:\n\n' +
        '• **Regular Checkup** - Routine health examination\n' +
        '• **Specialist Consultation** - See a specific doctor\n' +
        '• **Follow-up Visit** - Post-treatment check\n' +
        '• **Emergency Visit** - Urgent care needs\n\n' +
        'What type of appointment would you like to schedule?',
        'appointment_suggestion'
      )
      setIsTyping(false)
      return
    }

    // Health tips
    if (lowerInput.includes('health tip') || lowerInput.includes('wellness') || lowerInput.includes('healthy')) {
      const randomTip = healthTips[Math.floor(Math.random() * healthTips.length)]
      addBotMessage(
        `💡 **${randomTip.title}**\n\n${randomTip.content}\n\n*Category: ${randomTip.category}*`,
        'health_tip',
        randomTip
      )
      setIsTyping(false)
      return
    }

    // Symptom checking
    if (lowerInput.includes('symptom') || lowerInput.includes('feel') || lowerInput.includes('pain')) {
      addBotMessage(
        'I can help you understand your symptoms. Please describe:\n\n' +
        '• What symptoms you\'re experiencing\n' +
        '• How long you\'ve had them\n' +
        '• Any triggers or patterns\n' +
        '• Severity level (1-10)\n\n' +
        '**Note:** This is for informational purposes only. Always consult a healthcare professional for proper diagnosis.',
        'text'
      )
      setIsTyping(false)
      return
    }

    // Medication information
    if (lowerInput.includes('medication') || lowerInput.includes('medicine') || lowerInput.includes('pill')) {
      addBotMessage(
        'I can provide general information about medications. Please specify:\n\n' +
        '• The name of the medication\n' +
        '• What you\'d like to know (side effects, interactions, etc.)\n\n' +
        '**Important:** Always consult your doctor or pharmacist for personalized medical advice.',
        'text'
      )
      setIsTyping(false)
      return
    }

    // Doctor search
    if (lowerInput.includes('doctor') || lowerInput.includes('physician') || lowerInput.includes('specialist')) {
      addBotMessage(
        'I can help you find a doctor! We have specialists in:\n\n' +
        '• **Cardiology** - Heart and cardiovascular health\n' +
        '• **Orthopedics** - Bones and joints\n' +
        '• **Neurology** - Brain and nervous system\n' +
        '• **Pediatrics** - Children\'s health\n' +
        '• **Dermatology** - Skin conditions\n' +
        '• **Psychiatry** - Mental health\n\n' +
        'What specialty are you looking for?',
        'text'
      )
      setIsTyping(false)
      return
    }

    // General response
    const responses = [
      'I understand you\'re asking about that. Let me help you find the right information.',
      'That\'s a great question! I\'d be happy to assist you with that.',
      'I can help you with that. Could you provide more details?',
      'Thank you for your question. Let me guide you to the right resources.',
      'I\'m here to help! What specific information are you looking for?'
    ]
    
    const randomResponse = responses[Math.floor(Math.random() * responses.length)]
    addBotMessage(randomResponse)
    setIsTyping(false)
  }

  const handleSendMessage = () => {
    if (!inputValue.trim()) return
    
    addUserMessage(inputValue)
    processUserInput(inputValue)
    setInputValue('')
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }

  const renderMessage = (message: Message) => {
    const isUser = message.sender === 'user'

    return (
      <motion.div
        key={message.id}
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}
      >
        <div className={`flex items-start gap-2 max-w-[80%] ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
          <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
            isUser ? 'bg-blue-500' : 'bg-green-500'
          }`}>
            {isUser ? (
              <User className="w-4 h-4 text-white" />
            ) : (
              <Bot className="w-4 h-4 text-white" />
            )}
          </div>
          
          <div className={`rounded-lg p-3 ${
            isUser 
              ? 'bg-blue-500 text-white' 
              : 'bg-gray-100 text-gray-900'
          }`}>
            <div className="whitespace-pre-wrap text-sm">{message.text}</div>
            
            {message.type === 'health_tip' && message.data && (
              <div className="mt-2 p-2 bg-white/10 rounded">
                {message.data.icon}
              </div>
            )}
            
            <div className={`text-xs mt-1 ${
              isUser ? 'text-blue-100' : 'text-gray-500'
            }`}>
              {formatTime(message.timestamp)}
            </div>
          </div>
        </div>
      </motion.div>
    )
  }

  return (
    <>
      {/* Chatbot Toggle Button */}
      <motion.div
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        className="fixed bottom-6 right-6 z-50"
      >
        <Button
          onClick={() => setIsOpen(!isOpen)}
          className="w-14 h-14 rounded-full bg-blue-500 hover:bg-blue-600 shadow-lg"
        >
          <MessageCircle className="w-6 h-6" />
        </Button>
      </motion.div>

      {/* Chatbot Widget */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, scale: 0.8, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.8, y: 20 }}
            className="fixed bottom-24 right-6 z-50 w-96 h-[500px] bg-white rounded-lg shadow-2xl border border-gray-200"
          >
            {/* Header */}
            <div className="bg-gradient-to-r from-blue-500 to-purple-600 text-white p-4 rounded-t-lg">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 bg-white/20 rounded-full flex items-center justify-center">
                    <Bot className="w-4 h-4" />
                  </div>
                  <div>
                    <h3 className="font-semibold">AI Health Assistant</h3>
                    <p className="text-xs text-blue-100">Powered by Advanced AI</p>
                  </div>
                </div>
                <div className="flex items-center gap-1">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setIsMinimized(!isMinimized)}
                    className="text-white hover:bg-white/20"
                  >
                    {isMinimized ? <ChevronUpIcon className="w-4 h-4" /> : <ChevronDownIcon className="w-4 h-4" />}
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setIsOpen(false)}
                    className="text-white hover:bg-white/20"
                  >
                    <X className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </div>

            {!isMinimized && (
              <>
                {/* Messages */}
                <div className="flex-1 p-4 overflow-y-auto h-[350px]">
                  <div className="space-y-4">
                    {messages.map(renderMessage)}
                    
                    {isTyping && (
                      <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="flex justify-start mb-4"
                      >
                        <div className="flex items-start gap-2">
                          <div className="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center">
                            <Bot className="w-4 h-4 text-white" />
                          </div>
                          <div className="bg-gray-100 rounded-lg p-3">
                            <div className="flex space-x-1">
                              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                            </div>
                          </div>
                        </div>
                      </motion.div>
                    )}
                  </div>
                  <div ref={messagesEndRef} />
                </div>

                {/* Quick Actions */}
                {messages.length <= 1 && (
                  <div className="p-4 border-t border-gray-200">
                    <h4 className="text-sm font-medium text-gray-700 mb-3">Quick Actions</h4>
                    <div className="grid grid-cols-2 gap-2">
                      {quickActions.slice(0, 4).map((action) => (
                        <Button
                          key={action.id}
                          onClick={() => handleQuickAction(action)}
                          className={`${action.color} text-white text-xs h-8`}
                          size="sm"
                        >
                          {action.icon}
                          <span className="ml-1">{action.label}</span>
                        </Button>
                      ))}
                    </div>
                  </div>
                )}

                {/* Input */}
                <div className="p-4 border-t border-gray-200">
                  <div className="flex gap-2">
                    <Input
                      value={inputValue}
                      onChange={(e) => setInputValue(e.target.value)}
                      onKeyPress={handleKeyPress}
                      placeholder="Type your message..."
                      className="flex-1"
                      disabled={isTyping}
                    />
                    <Button
                      onClick={handleSendMessage}
                      disabled={!inputValue.trim() || isTyping}
                      className="bg-blue-500 hover:bg-blue-600"
                    >
                      <Send className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </>
  )
} 