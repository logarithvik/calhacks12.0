import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { trialsAPI, generationAPI } from '../services/api';
import { ArrowLeft, Save, Loader, Download } from 'lucide-react';
import Navbar from '../components/Navbar';

const SummaryEdit = () => {
  const { id } = useParams(); // trial ID
  const navigate = useNavigate();
  const [trial, setTrial] = useState(null);
  const [summaryContent, setSummaryContent] = useState(null);
  const [editedText, setEditedText] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadSummary();
  }, [id]);

  const loadSummary = async () => {
    try {
      // Load trial data
      const trialData = await trialsAPI.getById(id);
      setTrial(trialData);

      // Find summary content
      const summary = trialData.generated_content?.find(c => c.content_type === 'summary');
      
      if (!summary) {
        alert('No summary found for this trial');
        navigate(`/trial/${id}`);
        return;
      }

      setSummaryContent(summary);
      
      // Load the actual summary text
      // The summary text is stored in content_text field
      setEditedText(summary.content_text || '');
      
    } catch (error) {
      console.error('Error loading summary:', error);
      alert('Error loading summary');
      navigate(`/trial/${id}`);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      // Call API to update the summary
      await generationAPI.updateSummary(summaryContent.id, editedText);
      alert('Summary saved successfully!');
      navigate(`/trial/${id}`);
    } catch (error) {
      console.error('Error saving summary:', error);
      alert(error.response?.data?.detail || 'Error saving summary');
    } finally {
      setSaving(false);
    }
  };

  const handleDownload = () => {
    // Create a blob from the text and download it
    const blob = new Blob([editedText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${trial?.title || 'trial'}_summary.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <div className="flex items-center justify-center h-96">
          <Loader className="w-8 h-8 animate-spin text-indigo-600" />
          <span className="ml-2 text-xl">Loading summary...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      
      <div className="max-w-5xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <button
            onClick={() => navigate(`/trial/${id}`)}
            className="flex items-center space-x-2 text-indigo-600 hover:text-indigo-700 mb-6"
          >
            <ArrowLeft className="w-5 h-5" />
            <span>Back to Trial</span>
          </button>

          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <div className="flex justify-between items-start mb-4">
              <div>
                <h1 className="text-3xl font-bold text-gray-900 mb-2">Edit Summary</h1>
                <p className="text-gray-600">{trial?.title}</p>
                <p className="text-sm text-gray-500 mt-1">
                  Version {summaryContent?.version} • Last updated: {new Date(summaryContent?.created_at).toLocaleString()}
                </p>
              </div>
              
              <div className="flex space-x-3">
                <button
                  onClick={handleDownload}
                  className="flex items-center space-x-2 px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 transition-colors"
                >
                  <Download className="w-5 h-5" />
                  <span>Download</span>
                </button>
                
                <button
                  onClick={handleSave}
                  disabled={saving}
                  className="flex items-center space-x-2 px-6 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition-colors disabled:bg-indigo-400"
                >
                  {saving ? (
                    <>
                      <Loader className="w-5 h-5 animate-spin" />
                      <span>Saving...</span>
                    </>
                  ) : (
                    <>
                      <Save className="w-5 h-5" />
                      <span>Save Changes</span>
                    </>
                  )}
                </button>
              </div>
            </div>

            <div className="border-t pt-6">
              <label htmlFor="summary-editor" className="block text-sm font-medium text-gray-700 mb-2">
                Summary Text
              </label>
              <textarea
                id="summary-editor"
                value={editedText}
                onChange={(e) => setEditedText(e.target.value)}
                className="w-full h-[600px] p-4 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent font-mono text-sm"
                placeholder="Enter summary text here..."
              />
              <p className="text-sm text-gray-500 mt-2">
                {editedText.length} characters
              </p>
            </div>
          </div>

          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h3 className="text-sm font-medium text-blue-900 mb-2">💡 Editing Tips</h3>
            <ul className="text-sm text-blue-800 space-y-1 list-disc list-inside">
              <li>Review the AI-generated summary for accuracy</li>
              <li>Simplify medical terminology for patient understanding</li>
              <li>Ensure all key information is clearly presented</li>
              <li>Save your changes before leaving this page</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SummaryEdit;
