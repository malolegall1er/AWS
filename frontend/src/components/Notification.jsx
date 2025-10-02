import React, { useEffect } from 'react';

function Notification({ message, type, onClear }) {
  useEffect(() => {
    if (!message) return;
    const timer = setTimeout(() => onClear(), 5000);
    return () => clearTimeout(timer);
  }, [message, onClear]);

  if (!message) {
    return null;
  }

  return (
    <div className={`notification ${type}`}>
      <p>{message}</p>
      <button onClick={onClear} className="close-btn">&times;</button>
    </div>
  );
}

export default Notification;