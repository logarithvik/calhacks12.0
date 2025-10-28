import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { trialsAPI } from '../services/api';
import { Plus, FileText, Trash2, Eye, Loader, Upload, Sparkles, Clock, CheckCircle2, AlertCircle } from 'lucide-react';
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
    if (!window.confirm('Are you sure you want to delete this trial? This action cannot be undone.')) {
      return;
    }

    try {
      await trialsAPI.delete(id);
      setTrials(trials.filter(t => t.id !== id));
    } catch (error) {
      alert('Error deleting trial');
    }
  };

  // Stats calculations
  const stats = {
    total: trials.length,
    completed: trials.filter(t => t.status === 'completed').length,
    processing: trials.filter(t => t.status === 'processing').length,
    withContent: trials.filter(t => t.generated_content && t.generated_content.length > 0).length
  };

  return (
    <div className="min-h-screen bg-premium">
      <Navbar />
      
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Hero Section */}
        <div className="mb-12 animate-fadeIn">
          <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-6">
            <div>
              <div className="flex items-center space-x-2 mb-3">
                <Sparkles className="w-6 h-6 text-purple-600" />
                <span className="text-sm font-semibold text-purple-600 uppercase tracking-wide">
                  Welcome Back
                </span>
              </div>
              <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-3">
                My Clinical Trials
              </h1>
              <p className="text-lg text-gray-600 max-w-2xl">
                Transform complex trial protocols into patient-friendly educational content with AI
              </p>
            </div>
            <button
              onClick={() => setShowUploadModal(true)}
              className="btn-hero group flex items-center justify-center space-x-2"
            >
              <Plus className="w-6 h-6 transition-transform group-hover:rotate-90 duration-300" />
              <span>New Trial</span>
            </button>
          </div>
        </div>

        {/* Stats Cards */}
        {trials.length > 0 && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-12 stagger-children">
            <div className="premium-card p-6">
              <div className="flex items-center justify-between mb-2">
                <div className="icon-ocean">
                  <FileText className="w-5 h-5" />
                </div>
                <span className="text-2xl font-bold text-gray-900">{stats.total}</span>
              </div>
              <div className="text-sm font-semibold text-gray-600">Total Trials</div>
            </div>

            <div className="premium-card p-6">
              <div className="flex items-center justify-between mb-2">
                <div className="icon-green">
                  <CheckCircle2 className="w-5 h-5" />
                </div>
                <span className="text-2xl font-bold text-emerald-600">{stats.completed}</span>
              </div>
              <div className="text-sm font-semibold text-gray-600">Completed</div>
            </div>

            <div className="premium-card p-6">
              <div className="flex items-center justify-between mb-2">
                <div className="icon-amber">
                  <Clock className="w-5 h-5" />
                </div>
                <span className="text-2xl font-bold text-amber-600">{stats.processing}</span>
              </div>
              <div className="text-sm font-semibold text-gray-600">Processing</div>
            </div>

            <div className="premium-card p-6">
              <div className="flex items-center justify-between mb-2">
                <div className="icon-purple">
                  <Sparkles className="w-5 h-5" />
                </div>
                <span className="text-2xl font-bold text-purple-600">{stats.withContent}</span>
              </div>
              <div className="text-sm font-semibold text-gray-600">With Content</div>
            </div>
          </div>
        )}

        {/* Trials Grid */}
        {loading ? (
          <div className="text-center py-20">
            <Loader className="w-12 h-12 text-purple-600 animate-spin mx-auto mb-4" />
            <div className="text-lg font-medium text-gray-600">Loading trials...</div>
          </div>
        ) : trials.length === 0 ? (
          <div className="text-center py-20 animate-scaleIn">
            <div className="max-w-md mx-auto">
              <div className="glass-card p-12">
                <div className="icon-ocean inline-flex mb-6 scale-150">
                  <FileText className="w-8 h-8" />
                </div>
                <h3 className="text-2xl font-bold text-gray-900 mb-3">Start Your First Trial</h3>
                <p className="text-gray-600 mb-8 leading-relaxed">
                  Upload a clinical trial protocol and let AI generate patient-friendly summaries and educational videos
                </p>
                <button
                  onClick={() => setShowUploadModal(true)}
                  className="btn-hero inline-flex items-center space-x-2"
                >
                  <Upload className="w-5 h-5" />
                  <span>Upload Protocol</span>
                </button>
              </div>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 stagger-children">
            {trials.map((trial) => (
              <div key={trial.id} className="premium-card card-hover p-6 group">
                {/* Status Badge */}
                <div className="flex justify-between items-start mb-4">
                  <div className="flex-1 pr-3">
                    <h3 className="text-lg font-bold text-gray-900 mb-1 group-hover:text-purple-700 transition-colors">
                      {trial.title}
                    </h3>
                  </div>
                  {trial.status === 'completed' ? (
                    <span className="inline-flex items-center px-3 py-1.5 bg-gradient-to-r from-emerald-100 to-green-100 text-emerald-800 rounded-full text-xs font-bold border border-emerald-200 shadow-sm shrink-0">
                      <CheckCircle2 className="w-3 h-3 mr-1" />
                      Completed
                    </span>
                  ) : trial.status === 'processing' ? (
                    <span className="inline-flex items-center px-3 py-1.5 bg-gradient-to-r from-amber-100 to-yellow-100 text-amber-800 rounded-full text-xs font-bold border border-amber-200 shadow-sm shrink-0">
                      <Clock className="w-3 h-3 mr-1" />
                      Processing
                    </span>
                  ) : trial.status === 'error' ? (
                    <span className="inline-flex items-center px-3 py-1.5 bg-gradient-to-r from-red-100 to-rose-100 text-red-800 rounded-full text-xs font-bold border border-red-200 shadow-sm shrink-0">
                      <AlertCircle className="w-3 h-3 mr-1" />
                      Error
                    </span>
                  ) : (
                    <span className="inline-flex items-center px-3 py-1.5 bg-gradient-to-r from-blue-100 to-indigo-100 text-blue-800 rounded-full text-xs font-bold border border-blue-200 shadow-sm shrink-0">
                      {trial.status}
                    </span>
                  )}
                </div>

                {/* File Info */}
                {trial.original_filename && (
                  <div className="flex items-center space-x-2 text-sm text-gray-600 mb-3 bg-gray-50/80 px-3 py-2.5 rounded-lg border border-gray-100">
                    <FileText className="w-4 h-4 text-blue-600 shrink-0" />
                    <span className="truncate font-medium">{trial.original_filename}</span>
                  </div>
                )}

                {/* Date */}
                <div className="flex items-center space-x-2 text-xs text-gray-500 mb-4">
                  <Clock className="w-3.5 h-3.5" />
                  <span>Created {new Date(trial.created_at).toLocaleDateString('en-US', {
                    year: 'numeric',
                    month: 'short',
                    day: 'numeric'
                  })}</span>
                </div>

                {/* Generated Content Tags */}
                {trial.generated_content && trial.generated_content.length > 0 && (
                  <div className="mb-5">
                    <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
                      Generated Content
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {trial.generated_content.map((content) => (
                        <span 
                          key={content.id} 
                          className="px-3 py-1.5 bg-gradient-to-br from-purple-50 to-violet-50 text-purple-700 rounded-full text-xs font-bold border border-purple-100 shadow-sm"
                        >
                          {content.content_type}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Actions */}
                <div className="flex space-x-2 pt-4 border-t border-gray-100">
                  <button
                    onClick={() => navigate(`/trial/${trial.id}`)}
                    className="flex-1 flex items-center justify-center space-x-2 px-4 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:from-blue-700 hover:to-purple-700 transition-all duration-300 font-semibold shadow-md hover:shadow-xl transform hover:scale-105 active:scale-100"
                  >
                    <Eye className="w-4 h-4" />
                    <span>View Details</span>
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDelete(trial.id);
                    }}
                    className="p-3 bg-gradient-to-r from-red-50 to-rose-50 text-red-600 rounded-lg hover:from-red-100 hover:to-rose-100 transition-all duration-300 border border-red-200 hover:border-red-300"
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
  const [dragActive, setDragActive] = useState(false);

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

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFile(e.dataTransfer.files[0]);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 z-50 animate-fadeIn">
      <div className="glass-card max-w-lg w-full p-8 animate-scaleIn">
        {/* Header */}
        <div className="mb-8">
          <div className="icon-purple inline-flex mb-4">
            <Upload className="w-6 h-6" />
          </div>
          <h2 className="text-3xl font-bold text-gray-900 mb-2">
            Upload Trial Protocol
          </h2>
          <p className="text-gray-600">
            Add a new clinical trial and generate AI-powered educational content
          </p>
        </div>
        
        {error && (
          <div className="mb-6 p-4 bg-red-50 border-l-4 border-red-500 rounded-lg animate-slideIn">
            <div className="flex items-center space-x-2">
              <AlertCircle className="w-5 h-5 text-red-600" />
              <p className="text-red-800 text-sm font-semibold">{error}</p>
            </div>
          </div>
        )}

        <form onSubmit={handleSubmit}>
          {/* Title Input */}
          <div className="mb-6">
            <label className="block text-sm font-bold text-gray-900 mb-3">
              Trial Title
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
              className="input-field"
              placeholder="e.g., Phase II Study of Drug X for Diabetes"
            />
          </div>

          {/* File Upload */}
          <div className="mb-8">
            <label className="block text-sm font-bold text-gray-900 mb-3">
              Protocol Document
            </label>
            
            <div
              className={`relative border-2 border-dashed rounded-xl p-8 text-center transition-all duration-200 ${
                dragActive
                  ? 'border-purple-500 bg-purple-50'
                  : file
                  ? 'border-green-500 bg-green-50'
                  : 'border-gray-300 bg-gray-50 hover:border-gray-400'
              }`}
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
            >
              <input
                type="file"
                accept=".pdf,.txt"
                onChange={(e) => setFile(e.target.files[0])}
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              />
              
              <div className="pointer-events-none">
                {file ? (
                  <>
                    <CheckCircle2 className="w-12 h-12 text-green-600 mx-auto mb-3" />
                    <p className="text-sm font-semibold text-green-900 mb-1">
                      {file.name}
                    </p>
                    <p className="text-xs text-green-700">
                      {(file.size / 1024).toFixed(2)} KB
                    </p>
                  </>
                ) : (
                  <>
                    <Upload className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                    <p className="text-sm font-semibold text-gray-900 mb-1">
                      Drop file here or click to upload
                    </p>
                    <p className="text-xs text-gray-500">
                      PDF or TXT files accepted
                    </p>
                  </>
                )}
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="flex space-x-3">
            <button
              type="button"
              onClick={onClose}
              className="btn-secondary flex-1"
              disabled={uploading}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={uploading || !file}
              className="btn-hero flex-1 flex items-center justify-center space-x-2"
            >
              {uploading ? (
                <>
                  <Loader className="w-5 h-5 animate-spin" />
                  <span>Uploading...</span>
                </>
              ) : (
                <>
                  <Upload className="w-5 h-5" />
                  <span>Upload & Start</span>
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
