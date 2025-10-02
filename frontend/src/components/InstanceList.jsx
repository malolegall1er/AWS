import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_URL = 'http://<IP_DE_TON_EC2>:8000'; // N'oublie pas de remplacer l'IP !

function InstanceList() {
  const [instances, setInstances] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchInstances = async () => {
      try {
        setLoading(true);
        const response = await axios.get(`${API_URL}/api/instances`);
        setInstances(response.data);
        setError('');
      } catch (err) {
        setError('Impossible de charger les instances EC2.');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchInstances();
  }, []);

  if (loading) {
    return (
      <div className="card">
        <h2>🖥️ Instances EC2</h2>
        <div className="spinner-container">
          <div className="spinner"></div>
        </div>
      </div>
    );
  }

  return (
      <div className="card">
        <h2>🖥️ Instances EC2</h2>
        {error && <p className="error">{error}</p>}
        {!error && (
          <ul>
            {instances.length > 0 ? (
              instances.map(instance => (
                <li key={instance.id}>
                  <div style={{ wordBreak: 'break-word' }}>
                    <strong>ID :</strong> {instance.id} <br />
                    <small>Type : {instance.type}</small>
                  </div>
                  <span className={`status status-${instance.state}`}>{instance.state}</span>
                </li>
              ))
            ) : (
              <p className="empty-state">Aucune instance EC2 trouvée.</p>
            )}
          </ul>
        )}
    </div>
  );
}

export default InstanceList;