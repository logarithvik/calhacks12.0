import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { trialsAPI } from '../services/api';
import { Plus, FileText, Trash2, Eye } from 'lucide-react';
import Navbar from '../components/Navbar';

const Dashboard = () => {
  const [trials, setTrials] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    loadTrials();
  }, []);

  const loadTrials = async () => {
    try {
      const data = await trialsAPI.getAll();
      setTrials(data);
    } catch (error) {
      console.error('Error loading trials:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this trial?')) {
      return;
    }

    try {
      await trialsAPI.delete(id);
      setTrials(trials.filter(t => t.id !== id));
    } catch (error) {
      alert('Error deleting trial');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      
      <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="flex justify-between items-center mb-6">
            <h1 className="text-3xl font-bold text-gray-900">My Clinical Trials</h1>
            <button
              onClick={() => setShowUploadModal(true)}
              className="flex items-center space-x-2 px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
            >
              <Plus className="w-5 h-5" />
              <span>New Trial</span>
            </button>
          </div>

          {loading ? (
            <div className="text-center py-12">
              <div className="text-xl text-gray-600">Loading trials...</div>
            </div>
          ) : trials.length === 0 ? (
            <div className="text-center py-12 bg-white rounded-lg shadow">
              <FileText className="w-16 h-16 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No trials yet</h3>
              <p className="text-gray-600 mb-4">Upload your first clinical trial protocol to get started</p>
              <button
                onClick={() => setShowUploadModal(true)}
                className="inline-flex items-center space-x-2 px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
              >
                <Plus className="w-5 h-5" />
                <span>Upload Protocol</span>
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {trials.map((trial) => (
                <div key={trial.id} className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
                  <div className="flex justify-between items-start mb-4">
                    <h3 className="text-lg font-semibold text-gray-900 flex-1">{trial.title}</h3>
                    <span className={`px-2 py-1 text-xs rounded-full ${
                      trial.status === 'completed' ? 'bg-green-100 text-green-800' :
                      trial.status === 'processing' ? 'bg-yellow-100 text-yellow-800' :
                      trial.status === 'error' ? 'bg-red-100 text-red-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>
                      {trial.status}
                    </span>
                  </div>

                  {trial.original_filename && (
                    <p className="text-sm text-gray-600 mb-2">
                      📄 {trial.original_filename}
                    </p>
                  )}

                  <p className="text-xs text-gray-500 mb-4">
                    Created: {new Date(trial.created_at).toLocaleDateString()}
                  </p>

                  {trial.generated_content && trial.generated_content.length > 0 && (
                    <div className="mb-4 text-sm text-gray-600">
                      <p>Generated content:</p>
                      <div className="flex flex-wrap gap-2 mt-1">
                        {trial.generated_content.map((content) => (
                          <span key={content.id} className="px-2 py-1 bg-indigo-50 text-indigo-700 rounded text-xs">
                            {content.content_type}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  <div className="flex space-x-2">
                    <button
                      onClick={() => navigate(`/trial/${trial.id}`)}
                      className="flex-1 flex items-center justify-center space-x-1 px-3 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 text-sm"
                    >
                      <Eye className="w-4 h-4" />
                      <span>View</span>
                    </button>
                    <button
                      onClick={() => handleDelete(trial.id)}
                      className="px-3 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {showUploadModal && (
        <UploadModal
          onClose={() => setShowUploadModal(false)}
          onSuccess={() => {
            setShowUploadModal(false);
            loadTrials();
          }}
        />
      )}
    </div>
  );
};

const UploadModal = ({ onClose, onSuccess }) => {
  const [title, setTitle] = useState('');
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setUploading(true);

    try {
      await trialsAPI.create(title, file);
      onSuccess();
    } catch (err) {
      setError(err.response?.data?.detail || 'Error uploading trial');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg max-w-md w-full p-6">
        <h2 className="text-2xl font-bold mb-4">Upload Clinical Trial Protocol</h2>
        
        {error && (
          <div className="mb-4 p-3 bg-red-50 text-red-800 rounded">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Trial Title
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
              placeholder="e.g., Phase II Study of Drug X"
            />
          </div>

          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Protocol File (PDF or TXT)
            </label>
            <input
              type="file"
              accept=".pdf,.txt"
              onChange={(e) => setFile(e.target.files[0])}
              className="w-full"
            />
            <p className="mt-1 text-xs text-gray-500">
              Upload your clinical trial protocol document
            </p>
          </div>

          <div className="flex space-x-3">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={uploading}
              className="flex-1 px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-50"
            >
              {uploading ? 'Uploading...' : 'Upload'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default Dashboard;
