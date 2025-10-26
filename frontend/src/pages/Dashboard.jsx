import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { trialsAPI } from '../services/api';
import { Plus, FileText, Trash2, Eye, Loader } from 'lucide-react';
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
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-indigo-50 to-purple-50">
      <Navbar />
      
      <div className="max-w-7xl mx-auto py-8 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="flex justify-between items-center mb-8">
            <div>
              <h1 className="text-4xl font-bold bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 bg-clip-text text-transparent mb-2">
                My Clinical Trials
              </h1>
              <p className="text-gray-600">Manage and generate educational content from your protocols</p>
            </div>
            <button
              onClick={() => setShowUploadModal(true)}
              className="btn-gradient flex items-center space-x-2"
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
            <div className="text-center py-16 soft-card">
              <div className="icon-indigo inline-flex mb-4">
                <FileText className="w-12 h-12" />
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-2">No trials yet</h3>
              <p className="text-gray-600 mb-6 max-w-md mx-auto">
                Upload your first clinical trial protocol to start generating patient-friendly educational content
              </p>
              <button
                onClick={() => setShowUploadModal(true)}
                className="btn-gradient inline-flex items-center space-x-2"
              >
                <Plus className="w-5 h-5" />
                <span>Upload Protocol</span>
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {trials.map((trial) => (
                <div key={trial.id} className="soft-card card-hover">
                  <div className="flex justify-between items-start mb-4">
                    <h3 className="text-xl font-bold text-gray-900 flex-1 pr-2">{trial.title}</h3>
                    <span className={`badge ${
                      trial.status === 'completed' ? 'badge-success' :
                      trial.status === 'processing' ? 'badge-warning' :
                      trial.status === 'error' ? 'badge-error' :
                      'badge-info'
                    }`}>
                      {trial.status}
                    </span>
                  </div>

                  {trial.original_filename && (
                    <div className="flex items-center space-x-2 text-sm text-gray-600 mb-3 bg-gray-50 px-3 py-2 rounded-lg">
                      <FileText className="w-4 h-4 text-indigo-500" />
                      <span className="truncate">{trial.original_filename}</span>
                    </div>
                  )}

                  <p className="text-xs text-gray-500 mb-4">
                    Created {new Date(trial.created_at).toLocaleDateString()}
                  </p>

                  {trial.generated_content && trial.generated_content.length > 0 && (
                    <div className="mb-4">
                      <p className="text-xs font-semibold text-gray-500 mb-2">Generated Content:</p>
                      <div className="flex flex-wrap gap-2">
                        {trial.generated_content.map((content) => (
                          <span key={content.id} className="badge-info">
                            {content.content_type}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  <div className="flex space-x-2 pt-4 border-t border-gray-100">
                    <button
                      onClick={() => navigate(`/trial/${trial.id}`)}
                      className="flex-1 flex items-center justify-center space-x-2 px-4 py-2.5 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-lg hover:from-indigo-700 hover:to-purple-700 transition-all duration-300 font-medium shadow-md hover:shadow-lg"
                    >
                      <Eye className="w-4 h-4" />
                      <span>View Details</span>
                    </button>
                    <button
                      onClick={() => handleDelete(trial.id)}
                      className="p-2.5 bg-gradient-to-r from-red-500 to-red-600 text-white rounded-lg hover:from-red-600 hover:to-red-700 transition-all duration-300 shadow-md hover:shadow-lg"
                      title="Delete trial"
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
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50">
      <div className="glass-card max-w-md w-full p-8 animate-in fade-in duration-300">
        <div className="mb-6">
          <div className="icon-indigo inline-flex mb-4">
            <Plus className="w-8 h-8" />
          </div>
          <h2 className="text-3xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
            Upload Clinical Trial Protocol
          </h2>
          <p className="text-gray-600 mt-2">Add a new trial to generate educational content</p>
        </div>
        
        {error && (
          <div className="mb-4 p-4 bg-red-50 border-l-4 border-red-500 rounded-lg">
            <p className="text-red-800 text-sm font-medium">{error}</p>
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="mb-5">
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              Trial Title
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
              className="input-field"
              placeholder="e.g., Phase II Study of Drug X"
            />
          </div>

          <div className="mb-6">
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              Protocol File
            </label>
            <div className="relative">
              <input
                type="file"
                accept=".pdf,.txt"
                onChange={(e) => setFile(e.target.files[0])}
                className="w-full file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100 cursor-pointer"
              />
            </div>
            <p className="mt-2 text-xs text-gray-500 flex items-center space-x-1">
              <FileText className="w-3 h-3" />
              <span>Upload PDF or TXT file containing your clinical trial protocol</span>
            </p>
          </div>

          <div className="flex space-x-3">
            <button
              type="button"
              onClick={onClose}
              className="btn-secondary flex-1"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={uploading}
              className="btn-gradient flex-1 flex items-center justify-center space-x-2"
            >
              {uploading ? (
                <>
                  <Loader className="w-5 h-5 animate-spin" />
                  <span>Uploading...</span>
                </>
              ) : (
                <>
                  <Plus className="w-5 h-5" />
                  <span>Upload</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default Dashboard;
