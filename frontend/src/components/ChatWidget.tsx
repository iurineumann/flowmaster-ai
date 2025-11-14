import React, { useState } from 'react';
import { apiService } from '../services/apiClient';
import { MessageSquare, X, Send } from 'lucide-react';
import { Card } from './ui/Card';

const ChatWidget: React.FC = () => {
    const [isOpen, setIsOpen] = useState(false);
    const [message, setMessage] = useState("");
    const [history, setHistory] = useState<{role: 'user' | 'bot', text: string}[]>([]);
    const [loading, setLoading] = useState(false);

    const handleSend = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!message.trim()) return;

        const userMsg = message;
        setHistory(prev => [...prev, { role: 'user', text: userMsg }]);
        setMessage("");
        setLoading(true);

        try {
            const data = await apiService.sendChatQuery(userMsg);
            setHistory(prev => [...prev, { role: 'bot', text: data.response }]);
        } catch (error) {
            setHistory(prev => [...prev, { role: 'bot', text: "Erro ao conectar com o agente. Tente novamente." }]);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end">
            {/* Janela do Chat */}
            {isOpen && (
                <Card className="w-80 h-96 mb-4 flex flex-col shadow-2xl border-primary/20 animate-in slide-in-from-bottom-10">
                    <div className="p-3 bg-primary text-white rounded-t-lg flex justify-between items-center">
                        <span className="font-bold flex items-center gap-2"><MessageSquare size={18}/> FlowMaster AI</span>
                        <button onClick={() => setIsOpen(false)} className="hover:bg-white/20 rounded p-1"><X size={18}/></button>
                    </div>
                    
                    <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-gray-50 dark:bg-gray-900">
                        {history.length === 0 && <p className="text-sm text-gray-500 text-center mt-4">Olá! Como posso ajudar com seu contexto de hoje?</p>}
                        {history.map((msg, i) => (
                            <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                                <div className={`max-w-[85%] p-3 rounded-lg text-sm ${
                                    msg.role === 'user' 
                                    ? 'bg-primary text-white rounded-br-none' 
                                    : 'bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-bl-none'
                                }`}>
                                    {msg.text}
                                </div>
                            </div>
                        ))}
                        {loading && <div className="text-xs text-gray-400 ml-2">Digitando...</div>}
                    </div>

                    <form onSubmit={handleSend} className="p-3 border-t bg-white dark:bg-gray-900 rounded-b-lg flex gap-2">
                        <input 
                            className="flex-1 text-sm bg-transparent border rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary"
                            placeholder="Pergunte sobre o contexto..."
                            value={message}
                            onChange={(e) => setMessage(e.target.value)}
                        />
                        <button type="submit" disabled={loading} className="bg-primary text-white p-2 rounded hover:bg-primary/90 disabled:opacity-50">
                            <Send size={16} />
                        </button>
                    </form>
                </Card>
            )}

            {/* Botão Flutuante */}
            {!isOpen && (
                <button 
                    onClick={() => setIsOpen(true)}
                    className="bg-primary text-white p-4 rounded-full shadow-lg hover:scale-110 transition-transform duration-200 flex items-center justify-center"
                >
                    <MessageSquare size={24} />
                </button>
            )}
        </div>
    );
};

export default ChatWidget;