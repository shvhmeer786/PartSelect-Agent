import React from 'react';
import './QuickActions.css';

interface QuickActionsProps {
    actions?: string[];
    onClick: (action: string) => void;
    showDefaultActions?: boolean;
}

const QuickActions: React.FC<QuickActionsProps> = ({
    actions = [],
    onClick,
    showDefaultActions = false
}) => {
    // Standard actions that can be shown by default
    const defaultActions = [
        "Installation Help",
        "Order Status"
    ];

    // Combine default actions with provided actions if showDefaultActions is true
    const displayActions = showDefaultActions
        ? [...defaultActions, ...actions]
        : actions;

    // Limit number of displayed actions to prevent UI clutter
    const displayedActions = displayActions.slice(0, 4);

    return (
        <div className="quick-actions">
            {displayedActions.map((action, index) => (
                <button
                    key={index}
                    className="action-button"
                    onClick={() => onClick(action)}
                >
                    {action}
                </button>
            ))}
        </div>
    );
};

export default QuickActions; 