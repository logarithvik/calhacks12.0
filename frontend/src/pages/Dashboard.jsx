import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { trialsAPI } from '../services/api';
import { 
  Plus, 
  FileText, 
  Upload, 
  Sparkles, 
  TrendingUp,
  Clock,
  CheckCircle2,
  ArrowRight,
  Zap,
  Trash2
} from 'lucide-react';
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

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'bg-emerald-100 text-emerald-700 border-emerald-200';
      case 'processing': return 'bg-amber-100 text-amber-700 border-amber-200';
      case 'error': return 'bg-rose-100 text-rose-700 border-rose-200';
      default: return 'bg-slate-100 text-slate-700 border-slate-200';
    }
  };

  const getContentCount = (trial) => {
    return trial.generated_content?.length || 0;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50/30 to-indigo-50/20">
      <Navbar />
      
      {/* Hero Section */}
      <div className="relative overflow-hidden bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 text-white">
        <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZGVmcz48cGF0dGVybiBpZD0iZ3JpZCIgd2lkdGg9IjQwIiBoZWlnaHQ9IjQwIiBwYXR0ZXJuVW5pdHM9InVzZXJTcGFjZU9uVXNlIj48cGF0aCBkPSJNIDQwIDAgTCAwIDAgMCA0MCIgZmlsbD0ibm9uZSIgc3Ryb2tlPSJ3aGl0ZSIgc3Ryb2tlLW9wYWNpdHk9IjAuMSIgc3Ryb2tlLXdpZHRoPSIxIi8+PC9wYXR0ZXJuPjwvZGVmcz48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSJ1cmwoI2dyaWQpIi8+PC9zdmc+')] opacity-20"></div>
        
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
          <div className="flex items-center justify-between">
            <div className="space-y-4 animate-fade-in">
              <div className="flex items-center space-x-2">
                <Sparkles className="w-6 h-6 animate-pulse" />
                <span className="text-sm font-medium tracking-wide uppercase opacity-90">Clinical Trial Education</span>
              </div>
              <h1 className="text-5xl font-bold font-dm-sans leading-tight">
                Transform Complex Trials<br />
                <span className="bg-gradient-to-r from-yellow-200 to-pink-200 bg-clip-text text-transparent">
                  Into Clear Stories
                </span>
              </h1>
              <p className="text-xl text-indigo-100 max-w-2xl">
                AI-powered distillation of clinical trial protocols into patient-friendly summaries, infographics, and videos.
              </p>
            </div>
            
            <button
              onClick={() => setShowUploadModal(true)}
              className="group relative px-8 py-4 bg-white text-indigo-600 rounded-2xl font-semibold shadow-2xl hover:shadow-glow-lg transform hover:-translate-y-1 transition-all duration-300 flex items-center space-x-3"
            >
              <Plus className="w-6 h-6 group-hover:rotate-90 transition-transform duration-300" />
              <span>New Trial</span>
              <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </button>
          </div>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 -mt-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="soft-card p-6 group hover:scale-105 transition-transform duration-300">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 mb-1">Total Trials</p>
                <p className="text-3xl font-bold text-gray-900 font-dm-sans">{trials.length}</p>
              </div>
              <div className="icon-badge bg-gradient-to-br from-blue-500 to-cyan-500 text-white group-hover:scale-110 transition-transform">
                <FileText className="w-6 h-6" />
              </div>
            </div>
          </div>
          
          <div className="soft-card p-6 group hover:scale-105 transition-transform duration-300">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 mb-1">Content Generated</p>
                <p className="text-3xl font-bold text-gray-900 font-dm-sans">
                  {trials.reduce((acc, t) => acc + getContentCount(t), 0)}
                </p>
              </div>
              <div className="icon-badge bg-gradient-to-br from-purple-500 to-pink-500 text-white group-hover:scale-110 transition-transform">
                <Zap className="w-6 h-6" />
              </div>
            </div>
          </div>
          
          <div className="soft-card p-6 group hover:scale-105 transition-transform duration-300">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 mb-1">Completed</p>
                <p className="text-3xl font-bold text-gray-900 font-dm-sans">
                  {trials.filter(t => t.status === 'completed').length}
                </p>
              </div>
              <div className="icon-badge bg-gradient-to-br from-emerald-500 to-teal-500 text-white group-hover:scale-110 transition-transform">
                <TrendingUp className="w-6 h-6" />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Trials Grid */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-gray-900 font-dm-sans">Your Trials</h2>
          {trials.length > 0 && (
            <span className="text-sm text-gray-500">{trials.length} {trials.length === 1 ? 'trial' : 'trials'}</span>
          )}
        </div>

        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[1, 2, 3].map(i => (
              <div key={i} className="soft-card p-6 animate-pulse">
                <div className="h-6 bg-slate-200 rounded w-3/4 mb-4"></div>
                <div className="h-4 bg-slate-200 rounded w-1/2 mb-2"></div>
                <div className="h-4 bg-slate-200 rounded w-2/3"></div>
              </div>
            ))}
          </div>
        ) : trials.length === 0 ? (
          <div className="glass-card p-12 text-center animate-fade-in">
            <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-gradient-to-br from-indigo-100 to-purple-100 mb-6 animate-float">
              <FileText className="w-10 h-10 text-indigo-600" />
            </div>
            <h3 className="text-2xl font-bold text-gray-900 mb-3 font-dm-sans">No trials yet</h3>
            <p className="text-gray-600 mb-8 max-w-md mx-auto">
              Get started by uploading your first clinical trial protocol. Our AI will transform it into easy-to-understand content.
            </p>
            <button
              onClick={() => setShowUploadModal(true)}
              className="btn-gradient inline-flex items-center space-x-2"
            >
              <Plus className="w-5 h-5" />
              <span>Upload Your First Trial</span>
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 animate-fade-in">
            {trials.map((trial) => (
              <div
                key={trial.id}
                onClick={() => navigate(`/trial/${trial.id}`)}
                className="soft-card p-6 cursor-pointer group hover:scale-105 hover:-translate-y-1 transition-all duration-300 animated-border"
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="icon-badge bg-gradient-to-br from-indigo-500 to-purple-500 text-white group-hover:rotate-6 transition-transform">
                    <FileText className="w-6 h-6" />
                  </div>
                  <span className={`text-xs font-medium px-3 py-1 rounded-full border ${getStatusColor(trial.status)}`}>
                    {trial.status}
                  </span>
                </div>

                <h3 className="text-lg font-semibold text-gray-900 mb-2 line-clamp-2 font-dm-sans group-hover:text-indigo-600 transition-colors">
                  {trial.title}
                </h3>

                {trial.original_filename && (
                  <p className="text-sm text-gray-500 mb-3 truncate flex items-center">
                    <Upload className="w-4 h-4 mr-1" />
                    {trial.original_filename}
                  </p>
                )}

                <div className="flex items-center justify-between pt-4 border-t border-gray-100">
                  <div className="flex items-center space-x-4 text-sm text-gray-600">
                    <div className="flex items-center space-x-1">
                      <Sparkles className="w-4 h-4" />
                      <span>{getContentCount(trial)} content</span>
                    </div>
                    <div className="flex items-center space-x-1">
                      <Clock className="w-4 h-4" />
                      <span>{new Date(trial.created_at).toLocaleDateString()}</span>
                    </div>
                  </div>
                  <ArrowRight className="w-5 h-5 text-indigo-600 group-hover:translate-x-2 transition-transform" />
                </div>

                {/* Delete button - visible on hover */}
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDelete(trial.id);
                  }}
                  className="absolute top-4 right-4 opacity-0 group-hover:opacity-100 p-2 bg-rose-500 text-white rounded-lg hover:bg-rose-600 transition-all duration-200 shadow-lg"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Upload Modal */}
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
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50 animate-fade-in">
      <div className="glass-card p-8 max-w-lg w-full animate-slide-in">
        <div className="flex items-center space-x-3 mb-6">
          <div className="icon-badge bg-gradient-to-br from-indigo-500 to-purple-500 text-white">
            <Upload className="w-6 h-6" />
          </div>
          <h2 className="text-2xl font-bold text-gray-900 font-dm-sans">Upload New Trial</h2>
        </div>
        
        {error && (
          <div className="mb-6 p-4 bg-rose-50 border border-rose-200 text-rose-800 rounded-lg flex items-start space-x-2">
            <CheckCircle2 className="w-5 h-5 flex-shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Trial Title *
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
              className="w-full px-4 py-3 border border-gray-300 rounded-lg input-focus font-inter"
              placeholder="e.g., Phase III Alzheimer's Treatment Study"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Protocol File (PDF or TXT)
            </label>
            <div className="relative border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-indigo-400 transition-colors group">
              <input
                type="file"
                accept=".pdf,.txt"
                onChange={(e) => setFile(e.target.files[0])}
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              />
              <Upload className="w-12 h-12 text-gray-400 mx-auto mb-3 group-hover:text-indigo-600 transition-colors" />
              <p className="text-sm text-gray-600">
                {file ? (
                  <span className="text-indigo-600 font-medium flex items-center justify-center space-x-2">
                    <CheckCircle2 className="w-5 h-5" />
                    <span>{file.name}</span>
                  </span>
                ) : (
                  <>Click to upload or drag and drop</>
                )}
              </p>
              <p className="text-xs text-gray-500 mt-2">PDF or TXT files only</p>
            </div>
          </div>

          <div className="flex space-x-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-6 py-3 border border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={uploading}
              className="flex-1 btn-gradient disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
            >
              {uploading ? (
                <>
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  <span>Uploading...</span>
                </>
              ) : (
                <>
                  <Upload className="w-5 h-5" />
                  <span>Upload Trial</span>
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
