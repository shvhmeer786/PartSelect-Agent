import React, { useState, useRef, useEffect } from 'react';
import { v4 as uuidv4 } from 'uuid';
import ChatWindow from './components/ChatWindow';
import ProductCard from './components/ProductCard';
import QuickActions from './components/QuickActions';
import './App.css';

export interface Message {
    id: string;
    content: string;
    timestamp: Date;
    type: 'user' | 'agent' | 'system';
    actions?: string[];
    productData?: ProductData;
}

export interface ProductData {
    imageUrl?: string;
    partNumber: string;
    name: string;
    price?: number;
}

const App: React.FC = () => {
    const [messages, setMessages] = useState<Message[]>([]);
    const [inputValue, setInputValue] = useState('');
    const [isConnected, setIsConnected] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const websocketRef = useRef<WebSocket | null>(null);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    // Create WebSocket connection when component mounts
    useEffect(() => {
        const connectWebSocket = () => {
            const ws = new WebSocket('ws://localhost:9000/chat');

            ws.onopen = () => {
                setIsConnected(true);
                addSystemMessage('Connected to the agent. How can I help you?');
            };

            ws.onmessage = (event) => {
                handleAgentResponse(event.data);
                setIsLoading(false);
            };

            ws.onerror = () => {
                setIsConnected(false);
                addSystemMessage('Connection error. Please try again later.');
                setIsLoading(false);
            };

            ws.onclose = (event) => {
                setIsConnected(false);
                if (event.wasClean) {
                    addSystemMessage(`Connection closed: ${event.reason}`);
                } else {
                    addSystemMessage('Connection lost. Trying to reconnect...');
                    setTimeout(connectWebSocket, 3000);
                }
                setIsLoading(false);
            };

            websocketRef.current = ws;
        };

        connectWebSocket();

        const handleVisibilityChange = () => {
            if (document.visibilityState === 'visible' &&
                (!websocketRef.current || websocketRef.current.readyState !== WebSocket.OPEN)) {
                connectWebSocket();
            }
        };

        document.addEventListener('visibilitychange', handleVisibilityChange);

        return () => {
            document.removeEventListener('visibilitychange', handleVisibilityChange);
            if (websocketRef.current) {
                websocketRef.current.close();
            }
        };
    }, []);

    // Auto-scroll to bottom when messages change
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    // Add a system message
    const addSystemMessage = (content: string) => {
        setMessages((prev) => [
            ...prev,
            {
                id: uuidv4(),
                content,
                timestamp: new Date(),
                type: 'system'
            }
        ]);
    };

    // Handle response from the agent
    const handleAgentResponse = (data: string) => {
        try {
            const response = JSON.parse(data);

            const newMessage: Message = {
                id: uuidv4(),
                content: response.message,
                timestamp: new Date(),
                type: 'agent'
            };

            // Add quick actions if available
            if (response.suggested_actions && response.suggested_actions.length > 0) {
                newMessage.actions = response.suggested_actions;
            }

            // Add product data if available
            if (response.product_data) {
                newMessage.productData = response.product_data;
            }

            setMessages((prev) => [...prev, newMessage]);
        } catch (e) {
            // Fallback for non-JSON responses
            setMessages((prev) => [
                ...prev,
                {
                    id: uuidv4(),
                    content: data,
                    timestamp: new Date(),
                    type: 'agent'
                }
            ]);
        }
    };

    // Send message through WebSocket
    const sendMessage = (content: string) => {
        if (!content.trim()) return;

        const newMessage: Message = {
            id: uuidv4(),
            content,
            timestamp: new Date(),
            type: 'user'
        };

        setMessages((prev) => [...prev, newMessage]);

        if (websocketRef.current && websocketRef.current.readyState === WebSocket.OPEN) {
            setIsLoading(true);
            websocketRef.current.send(content);
        } else {
            addSystemMessage('Not connected to the agent. Please wait while we reconnect...');
        }

        setInputValue('');
    };

    // Handle form submission
    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        sendMessage(inputValue);
    };

    // Handle quick action clicks
    const handleQuickActionClick = (action: string) => {
        sendMessage(action);
    };

    // Handle check compatibility button click
    const handleCheckCompatibility = (partNumber: string) => {
        sendMessage(`Is part number ${partNumber} compatible with my appliance?`);
    };

    return (
        <div className="app-container">
            <header className="app-header">
                <div className="logo">
                    <h1>PartSelect Agent</h1>
                </div>
                <div className="connection-status">
                    <div className={`status-indicator ${isConnected ? 'connected' : 'disconnected'}`}></div>
                    {isConnected ? 'Connected' : 'Disconnected'}
                </div>
            </header>

            <div className="main-content">
                <ChatWindow
                    messages={messages}
                    isLoading={isLoading}
                    messagesEndRef={messagesEndRef}
                    onQuickActionClick={handleQuickActionClick}
                    onCheckCompatibility={handleCheckCompatibility}
                />

                <div className="default-actions-container">
                    <QuickActions
                        showDefaultActions={true}
                        onClick={handleQuickActionClick}
                    />
                </div>

                <form className="input-form" onSubmit={handleSubmit}>
                    <input
                        type="text"
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        placeholder="Ask about appliance parts, installation, or compatibility..."
                        disabled={!isConnected || isLoading}
                    />
                    <button type="submit" disabled={!isConnected || isLoading || !inputValue.trim()}>
                        Send
                    </button>
                </form>
            </div>
        </div>
    );
};

export default App; 