// frontend/src/components/HeaderStatus.tsx
import React from 'react';

interface HeaderProps {
    status: string;
}

const HeaderStatus: React.FC<HeaderProps> = ({ status }) => {
    return (
        <header className="header">
            <h1>FlowMaster AI Dashboard</h1>
            <p className={`status ${status.includes('Online') ? 'online' : 'offline'}`}>
                Backend Status: {status}
            </p>
        </header>
    );
};

export default HeaderStatus;