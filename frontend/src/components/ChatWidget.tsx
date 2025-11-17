import React, { useState, useRef, useEffect } from 'react';
import { apiService } from '../services/apiClient';
import { MessageSquare, X, Send, Loader2 } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/Card';
import { Button } from './ui/Button';
import { Input } from './ui/Input';

interface ChatMessage {
  id: string;
  type: 'user' | 'bot';
  content: string;
  timestamp: Date;
  contextUsed?: string[];
}

const ChatWidget: React.FC = () => {
    const [isOpen, setIsOpen] = useState(false);
    const [currentMessage, setCurrentMessage] = useState("");
    const [messageHistory, setMessageHistory] = useState<ChatMessage[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    // Auto-scroll para a última mensagem
    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messageHistory]);

    const handleSend = async () => {
        if (!currentMessage.trim()) return;

        // Adiciona a mensagem do usuário ao histórico
        const userMessage: ChatMessage = {
            id: `user-${Date.now()}`,
            type: 'user',
            content: currentMessage,
            timestamp: new Date(),
        };

        setMessageHistory((prev) => [...prev, userMessage]);
        setCurrentMessage('');
        setIsLoading(true);
        setError(null);

        try {
            // Chama a API de chat
            const response = await apiService.sendChatQuery(currentMessage);

            // Adiciona a resposta do bot ao histórico
            const botMessage: ChatMessage = {
                id: `bot-${Date.now()}`,
                type: 'bot',
                content: response.response,
                timestamp: new Date(),
                contextUsed: response.context_used,
            };

            setMessageHistory((prev) => [...prev, botMessage]);
        } catch (err: any) {
            console.error('Erro ao enviar mensagem:', err);
            setError(err.message || 'Erro ao enviar mensagem. Tente novamente.');

            // Adiciona mensagem de erro ao histórico
            const errorMessage: ChatMessage = {
                id: `error-${Date.now()}`,
                type: 'bot',
                content: '❌ Desculpe, ocorreu um erro ao processar sua pergunta. Tente novamente.',
                timestamp: new Date(),
            };

            setMessageHistory((prev) => [...prev, errorMessage]);
        } finally {
            setIsLoading(false);
        }
    };

    const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    const clearHistory = () => {
        setMessageHistory([]);
        setError(null);
    };

    return (
        <div className="fixed bottom-6 right-6 z-50">
            {/* Botão Flutuante */}
            {!isOpen && (
                <Button
                    onClick={() => setIsOpen(true)}
                    size="icon"
                    className="rounded-full h-14 w-14 shadow-lg hover:shadow-xl transition-shadow bg-blue-600 hover:bg-blue-700"
                    title="Abrir Chat"
                >
                    <MessageSquare className="h-6 w-6" />
                </Button>
            )}

            {/* Janela de Chat */}
            {isOpen && (
                <Card className="absolute bottom-0 right-0 w-96 h-[600px] shadow-2xl border border-gray-200 dark:border-gray-700 flex flex-col">
                    {/* Header */}
                    <CardHeader className="border-b flex-row items-center justify-between p-4">
                        <CardTitle className="text-lg font-semibold">FlowMaster Chat</CardTitle>
                        <div className="flex items-center gap-2">
                            {messageHistory.length > 0 && (
                                <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={clearHistory}
                                    title="Limpar histórico"
                                    className="text-xs"
                                >
                                    Limpar
                                </Button>
                            )}
                            <Button
                                variant="ghost"
                                size="icon"
                                onClick={() => setIsOpen(false)}
                                className="h-8 w-8"
                                title="Fechar chat"
                            >
                                <X className="h-4 w-4" />
                            </Button>
                        </div>
                    </CardHeader>

                    {/* Mensagens */}
                    <CardContent className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50 dark:bg-gray-900">
                        {messageHistory.length === 0 ? (
                            <div className="flex items-center justify-center h-full">
                                <div className="text-center text-gray-500 dark:text-gray-400">
                                    <MessageSquare className="h-8 w-8 mx-auto mb-2 opacity-50" />
                                    <p className="text-sm">Olá! 👋</p>
                                    <p className="text-xs mt-2">Faça uma pergunta sobre seu contexto de trabalho.</p>
                                </div>
                            </div>
                        ) : (
                            <>
                                {messageHistory.map((message) => (
                                    <div
                                        key={message.id}
                                        className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
                                    >
                                        <div
                                            className={`max-w-xs px-4 py-2 rounded-lg ${
                                                message.type === 'user'
                                                    ? 'bg-blue-600 text-white rounded-br-none'
                                                    : 'bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded-bl-none'
                                            }`}
                                        >
                                            <p className="text-sm wrap-break-word">{message.content}</p>
                                            {message.contextUsed && message.contextUsed.length > 0 && (
                                                <div className="mt-2 pt-2 border-t border-opacity-50 border-current">
                                                    <p className="text-xs opacity-75 font-semibold">Contexto usado:</p>
                                                    <ul className="text-xs list-disc list-inside opacity-75">
                                                        {message.contextUsed.slice(0, 2).map((ctx, idx) => (
                                                            <li key={idx} className="truncate">
                                                                {ctx}
                                                            </li>
                                                        ))}
                                                        {message.contextUsed.length > 2 && (
                                                            <li>+{message.contextUsed.length - 2} mais</li>
                                                        )}
                                                    </ul>
                                                </div>
                                            )}
                                            <p className="text-xs opacity-70 mt-1">
                                                {message.timestamp.toLocaleTimeString('pt-BR', {
                                                    hour: '2-digit',
                                                    minute: '2-digit',
                                                })}
                                            </p>
                                        </div>
                                    </div>
                                ))}

                                {isLoading && (
                                    <div className="flex justify-start">
                                        <div className="bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-gray-100 px-4 py-2 rounded-lg rounded-bl-none">
                                            <div className="flex items-center gap-2">
                                                <Loader2 className="h-4 w-4 animate-spin" />
                                                <p className="text-sm">Processando...</p>
                                            </div>
                                        </div>
                                    </div>
                                )}

                                {error && (
                                    <div className="flex justify-center">
                                        <div className="bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-100 px-4 py-2 rounded-lg text-sm">
                                            {error}
                                        </div>
                                    </div>
                                )}

                                <div ref={messagesEndRef} />
                            </>
                        )}
                    </CardContent>

                    {/* Input */}
                    <div className="border-t p-4 bg-white dark:bg-gray-800 space-y-2">
                        <div className="flex gap-2">
                            <Input
                                type="text"
                                placeholder="Digite sua pergunta..."
                                value={currentMessage}
                                onChange={(e) => setCurrentMessage(e.target.value)}
                                onKeyPress={handleKeyPress}
                                disabled={isLoading}
                                className="flex-1 text-sm"
                            />
                            <Button
                                onClick={handleSend}
                                disabled={isLoading || !currentMessage.trim()}
                                size="icon"
                                className="h-10 w-10"
                                title="Enviar mensagem (Enter)"
                            >
                                {isLoading ? (
                                    <Loader2 className="h-4 w-4 animate-spin" />
                                ) : (
                                    <Send className="h-4 w-4" />
                                )}
                            </Button>
                        </div>
                        <p className="text-xs text-gray-500 dark:text-gray-400 text-center">
                            Pressione Enter para enviar
                        </p>
                    </div>
                </Card>
            )}
        </div>
    );
};

export default ChatWidget;