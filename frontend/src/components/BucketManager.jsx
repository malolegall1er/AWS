import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';

const API_URL = 'http://<IP_DE_TON_EC2>:8000'; // N'oublie pas de remplacer l'IP !

function BucketManager({ showNotification }) {
  const [buckets, setBuckets] = useState([]);
  const [newBucketName, setNewBucketName] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadBucket, setUploadBucket] = useState('');
  const [loading, setLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const fileInputRef = useRef(null);

  const fetchBuckets = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_URL}/api/buckets`);
      setBuckets(response.data);
    } catch (err) {
      showNotification('Impossible de charger les buckets S3.', 'error');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBuckets();
  }, []);

  const handleCreateBucket = async (e) => {
    e.preventDefault();
    if (!newBucketName) return;
    setIsSubmitting(true);
    try {
      await axios.post(`${API_URL}/api/buckets/${newBucketName}`);
      showNotification(`Bucket "${newBucketName}" créé avec succès !`, 'success');
      setNewBucketName('');
      fetchBuckets(); // Refresh list
    } catch (err) {
      showNotification(err.response?.data?.detail || 'Erreur lors de la création du bucket.', 'error');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeleteBucket = async (bucketName) => {
    if (window.confirm(`Êtes-vous sûr de vouloir supprimer le bucket "${bucketName}" ?`)) {
      try {
        await axios.delete(`${API_URL}/api/buckets/${bucketName}`);
        showNotification(`Bucket "${bucketName}" supprimé !`, 'success');
        fetchBuckets(); // Refresh list
      } catch (err) {
        showNotification(err.response?.data?.detail || 'Erreur: le bucket n\'est probablement pas vide.', 'error');
      }
    }
  };
  
  const handleUpload = async () => {
    if (!selectedFile || !uploadBucket) {
      showNotification("Veuillez sélectionner un bucket et un fichier.", 'error');
      return;
    }
    const formData = new FormData();
    formData.append('file', selectedFile);
    setIsSubmitting(true);

    try {
      await axios.post(`${API_URL}/api/buckets/${uploadBucket}/upload`, formData);
      showNotification(`Fichier "${selectedFile.name}" uploadé dans "${uploadBucket}" !`, 'success');
      setSelectedFile(null);
      setUploadBucket('');
      if (fileInputRef.current) fileInputRef.current.value = "";
    } catch (err) {
      showNotification(err.response?.data?.detail || "Erreur lors de l'upload.", 'error');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="card">
          <h2>🪣 Buckets S3</h2>
          <form onSubmit={handleCreateBucket} className="form-group" autoComplete="off">
            <input
              type="text"
              placeholder="Nom du nouveau bucket"
              value={newBucketName}
              onChange={e => setNewBucketName(e.target.value)}
              disabled={isSubmitting}
              aria-label="Nom du nouveau bucket"
            />
            <button type="submit" disabled={isSubmitting || !newBucketName} style={{ minWidth: '100px' }}>
              Créer
            </button>
          </form>
          <hr />
          <div className="upload-group form-group">
            <select
              value={uploadBucket}
              onChange={e => setUploadBucket(e.target.value)}
              aria-label="Choisir un bucket pour uploader"
            >
              <option value="">Choisir un bucket pour uploader</option>
              {buckets.map(bucket => (
                <option key={bucket} value={bucket}>{bucket}</option>
              ))}
            </select>
            <input
              type="file"
              ref={fileInputRef}
              onChange={e => setSelectedFile(e.target.files[0])}
              aria-label="Fichier à uploader"
            />
            <button
              type="button"
              onClick={handleUpload}
              disabled={!selectedFile || !uploadBucket}
              style={{ minWidth: '100px' }}
            >
              Uploader
            </button>
          </div>
          <hr />
          <ul>
            {loading ? (
              <div className="spinner-container"><div className="spinner"></div></div>
            ) : (
              buckets.length > 0 ? (
                buckets.map(bucket => (
                  <li key={bucket}>
                    <span>{bucket}</span>
                    <button className="delete-btn" onClick={() => handleDeleteBucket(bucket)} style={{ minWidth: '100px' }}>
                      Supprimer
                    </button>
                  </li>
                ))
              ) : (
                <p className="empty-state">Aucun bucket S3 trouvé.</p>
              )
            )}
      </ul>
    </div>
  );
}

export default BucketManager;