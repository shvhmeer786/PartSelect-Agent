import React from 'react';
import ReactMarkdown from 'react-markdown';
import QuickActions from './QuickActions';
import ProductCard from './ProductCard';
import './ChatWindow.css';

interface Message {
    id: string;
    content: string;
    timestamp: Date;
    type: 'user' | 'agent' | 'system';
    actions?: string[];
    productData?: {
        imageUrl?: string;
        partNumber: string;
        name: string;
        price?: number;
    };
}

interface ChatWindowProps {
    messages: Message[];
    isLoading: boolean;
    messagesEndRef: React.RefObject<HTMLDivElement>;
    onQuickActionClick: (action: string) => void;
    onCheckCompatibility: (partNumber: string) => void;
}

const ChatWindow: React.FC<ChatWindowProps> = ({
    messages,
    isLoading,
    messagesEndRef,
    onQuickActionClick,
    onCheckCompatibility
}) => {
    // Format timestamp to HH:MM format
    const formatTime = (date: Date): string => {
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    };

    // Determine if the message is JSON data
    const isJsonString = (str: string): boolean => {
        try {
            const json = JSON.parse(str);
            return typeof json === 'object' && json !== null;
        } catch (e) {
            return false;
        }
    };

    // Format JSON for display
    const formatJsonContent = (content: string): string => {
        try {
            const jsonObj = JSON.parse(content);
            // Handle special cases for part information
            if (jsonObj.name && jsonObj.partNumber) {
                return `
## ${jsonObj.name}
**Part Number**: ${jsonObj.partNumber}
${jsonObj.price ? `**Price**: $${jsonObj.price}` : ''}
${jsonObj.imageUrl ? `![${jsonObj.name}](${jsonObj.imageUrl})` : ''}
${jsonObj.description ? `\n${jsonObj.description}` : ''}
        `;
            }
            // Return formatted JSON
            return '```json\n' + JSON.stringify(jsonObj, null, 2) + '\n```';
        } catch (e) {
            return content;
        }
    };

    // Render each message
    const renderMessage = (message: Message) => {
        // Determine message content to display
        let displayContent = message.content;

        // Format JSON responses
        if (message.type === 'agent' && isJsonString(message.content)) {
            displayContent = formatJsonContent(message.content);
        }

        return (
            <div
                key={message.id}
                className={`message-container ${message.type}-container`}
            >
                <div className={`message ${message.type}-message`}>
                    {message.type === 'agent' || message.type === 'system' ? (
                        <ReactMarkdown className="markdown-content">
                            {displayContent}
                        </ReactMarkdown>
                    ) : (
                        <p>{displayContent}</p>
                    )}

                    <div className="message-timestamp">
                        {formatTime(message.timestamp)}
                    </div>
                </div>

                {/* Show product card if product data is available */}
                {message.type === 'agent' && message.productData && (
                    <ProductCard
                        {...message.productData}
                        onCheckCompatibility={onCheckCompatibility}
                    />
                )}

                {/* Show quick actions for agent messages */}
                {message.type === 'agent' && message.actions && message.actions.length > 0 && (
                    <QuickActions actions={message.actions} onClick={onQuickActionClick} />
                )}
            </div>
        );
    };

    return (
        <div className="chat-window">
            <div className="messages-container">
                {messages.map(renderMessage)}

                {/* Loading indicator */}
                {isLoading && (
                    <div className="message-container agent-container">
                        <div className="message agent-message loading">
                            <div className="typing-indicator">
                                <span></span>
                                <span></span>
                                <span></span>
                            </div>
                        </div>
                    </div>
                )}

                {/* Reference for scrolling to the bottom */}
                <div ref={messagesEndRef} />
            </div>
        </div>
    );
};

export default ChatWindow; 