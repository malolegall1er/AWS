import React, { useState } from 'react';
import InstanceList from './components/InstanceList';
import BucketManager from './components/BucketManager';
import Notification from './components/Notification';
import './App.css';

function App() {
  const [activeTab, setActiveTab] = useState('instances');
  const [notification, setNotification] = useState({ message: '', type: '' });

  const showNotification = (message, type) => {
    setNotification({ message, type });
  };

  const clearNotification = () => {
    setNotification({ message: '', type: '' });
  };

  return (
    <div className="App">
      <Notification 
        message={notification.message} 
        type={notification.type} 
        onClear={clearNotification} 
      />
      <header className="App-header">
        <h1>☁️ AWS Simple Dashboard</h1>
      </header>
      
      <nav className="tab-nav">
        <button 
          className={activeTab === 'instances' ? 'active' : ''} 
          onClick={() => setActiveTab('instances')}
        >
          🖥️ Instances EC2
        </button>
        <button 
          className={activeTab === 'buckets' ? 'active' : ''} 
          onClick={() => setActiveTab('buckets')}
        >
          🪣 Buckets S3
        </button>
      </nav>

      <main className="content">
        {activeTab === 'instances' && <InstanceList />}
        {activeTab === 'buckets' && <BucketManager showNotification={showNotification} />}
      </main>
    </div>
  );
}

export default App;