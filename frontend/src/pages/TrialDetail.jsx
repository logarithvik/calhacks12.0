import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { trialsAPI, generationAPI } from '../services/api';
import { ArrowLeft, FileText, Image, Video, Loader, CheckCircle, Play } from 'lucide-react';
import Navbar from '../components/Navbar';

const TrialDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [trial, setTrial] = useState(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState({});
  const [summaryData, setSummaryData] = useState(null);

  useEffect(() => {
    loadTrial();
  }, [id]);

  const loadTrial = async () => {
    try {
      const data = await trialsAPI.getById(id);
      setTrial(data);
      
      // Load summary data if exists
      const summaryContent = data.generated_content?.find(c => c.content_type === 'summary');
      if (summaryContent) {
        const contentData = await generationAPI.getContentData(summaryContent.id);
        setSummaryData(contentData.data);
      }
    } catch (error) {
      console.error('Error loading trial:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerate = async (type) => {
    setGenerating({ ...generating, [type]: true });

    try {
      let result;
      
      switch (type) {
        case 'summary':
          result = await generationAPI.generateSummary(id);
          // Redirect to edit page after summary generation
          navigate(`/trial/${id}/summary/edit`);
          return;
        case 'video':
          result = await generationAPI.generateVideo(id);
          break;
      }
      
      // Reload trial to show updated content
      await loadTrial();
      
      alert(`${type.charAt(0).toUpperCase() + type.slice(1)} generated successfully!`);
    } catch (error) {
      alert(error.response?.data?.detail || `Error generating ${type}`);
    } finally {
      setGenerating({ ...generating, [type]: false });
    }
  };

  const getContent = (type) => {
    return trial?.generated_content?.find(c => c.content_type === type);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <div className="flex items-center justify-center h-96">
          <div className="text-xl">Loading trial...</div>
        </div>
      </div>
    );
  }

  if (!trial) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <div className="flex items-center justify-center h-96">
          <div className="text-xl text-red-600">Trial not found</div>
        </div>
      </div>
    );
  }

  const summaryContent = getContent('summary');
  const videoContent = getContent('video');

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-indigo-50 to-purple-50">
      <Navbar />
      
      <div className="max-w-7xl mx-auto py-8 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <button
            onClick={() => navigate('/dashboard')}
            className="flex items-center space-x-2 text-indigo-600 hover:text-indigo-700 mb-6 font-medium transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
            <span>Back to Dashboard</span>
          </button>

          <div className="soft-card mb-8">
            <h1 className="text-4xl font-bold bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 bg-clip-text text-transparent mb-3">
              {trial.title}
            </h1>
            {trial.original_filename && (
              <div className="flex items-center space-x-2 text-gray-600 mb-2 bg-gray-50 px-4 py-2 rounded-lg inline-flex">
                <FileText className="w-5 h-5 text-indigo-500" />
                <span className="font-medium">{trial.original_filename}</span>
              </div>
            )}
            <p className="text-sm text-gray-500 mt-3">
              Created {new Date(trial.created_at).toLocaleDateString()}
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
            {/* Summary Card */}
            <GenerationCard
              title="Summary"
              icon={<FileText className="w-8 h-8" />}
              iconColor="indigo"
              description="Extract key information from the protocol"
              hasContent={!!summaryContent}
              isGenerating={generating.summary}
              onGenerate={() => handleGenerate('summary')}
              onEdit={() => navigate(`/trial/${id}/summary/edit`)}
              contentId={summaryContent?.id}
            />

            {/* Video Card */}
            <GenerationCard
              title="Video"
              icon={<Video className="w-8 h-8" />}
              iconColor="purple"
              description="Generate educational video"
              hasContent={!!videoContent}
              isGenerating={generating.video}
              onGenerate={() => handleGenerate('video')}
              onView={() => navigate(`/trial/${id}/video/${videoContent.id}`)}
              contentId={videoContent?.id}
              disabled={!summaryContent}
              disabledMessage="Generate summary first"
            />
          </div>

          {/* Summary Display */}
          {summaryData && (
            <div className="soft-card mb-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">Trial Summary</h2>
              
              {summaryData.simple_summary && (
                <div className="prose max-w-none mb-6 bg-gradient-to-br from-indigo-50 to-purple-50 p-6 rounded-xl">
                  <pre className="whitespace-pre-wrap font-sans text-gray-700">{summaryData.simple_summary}</pre>
                </div>
              )}

              {summaryData.structured_data && (
                <div className="space-y-4">
                  <DetailSection title="Study Information" data={summaryData.structured_data} />
                </div>
              )}
            </div>
          )}

          {/* Video Display */}
          {videoContent && (
            <div className="soft-card">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">Educational Video</h2>
              <div className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-xl p-8 text-center">
                <div className="icon-purple inline-flex mb-4">
                  <Video className="w-12 h-12" />
                </div>
                <p className="text-gray-700 mb-3 font-medium">
                  Video generated successfully!
                </p>
                <p className="text-sm text-gray-600 mb-4">
                  {videoContent.file_path}
                </p>
                <button
                  onClick={() => navigate(`/trial/${id}/video/${videoContent.id}`)}
                  className="btn-gradient inline-flex items-center space-x-2"
                >
                  <Play className="w-5 h-5" />
                  <span>Watch Video</span>
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

const GenerationCard = ({ 
  title, 
  icon,
  iconColor = 'indigo',
  description, 
  hasContent, 
  isGenerating, 
  onGenerate, 
  onEdit,
  onView,
  contentId,
  disabled,
  disabledMessage 
}) => {
  const iconClass = `icon-${iconColor}`;
  
  return (
    <div className="soft-card card-hover">
      <div className="flex items-center space-x-3 mb-4">
        <div className={iconClass}>
          {icon}
        </div>
        <h3 className="text-xl font-bold text-gray-900">{title}</h3>
      </div>
      
      <p className="text-gray-600 mb-4">{description}</p>
      
      {hasContent && (
        <div className="flex items-center space-x-2 badge-success mb-4">
          <CheckCircle className="w-4 h-4" />
          <span className="text-sm font-semibold">Generated Successfully</span>
        </div>
      )}
      
      {hasContent && (onEdit || onView) ? (
        <div className="space-y-3">
          {onEdit && (
            <button
              onClick={onEdit}
              className="w-full flex items-center justify-center space-x-2 px-4 py-3 bg-gradient-to-r from-indigo-600 to-indigo-700 text-white rounded-lg hover:from-indigo-700 hover:to-indigo-800 transition-all duration-300 font-semibold shadow-md hover:shadow-lg"
            >
              <FileText className="w-5 h-5" />
              <span>Edit Summary</span>
            </button>
          )}
          {onView && (
            <button
              onClick={onView}
              className="w-full flex items-center justify-center space-x-2 px-4 py-3 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg hover:from-purple-700 hover:to-pink-700 transition-all duration-300 font-semibold shadow-md hover:shadow-lg"
            >
              <Video className="w-5 h-5" />
              <span>View Video</span>
            </button>
          )}
          <button
            onClick={onGenerate}
            disabled={isGenerating}
            className="w-full flex items-center justify-center space-x-2 px-4 py-3 bg-gradient-to-r from-gray-100 to-gray-200 text-gray-700 rounded-lg hover:from-gray-200 hover:to-gray-300 transition-all duration-300 font-medium border border-gray-300"
          >
            {isGenerating ? (
              <>
                <Loader className="w-5 h-5 animate-spin" />
                <span>Generating...</span>
              </>
            ) : (
              <span>Regenerate</span>
            )}
          </button>
        </div>
      ) : (
        <button
          onClick={onGenerate}
          disabled={isGenerating || disabled}
          className={`w-full flex items-center justify-center space-x-2 px-4 py-3 rounded-lg transition-all duration-300 font-semibold shadow-md ${
            disabled
              ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
              : hasContent
              ? 'bg-gradient-to-r from-gray-100 to-gray-200 text-gray-700 hover:from-gray-200 hover:to-gray-300 border border-gray-300'
              : 'bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 text-white hover:from-indigo-700 hover:via-purple-700 hover:to-pink-700 hover:shadow-lg'
          }`}
          title={disabled ? disabledMessage : ''}
        >
          {isGenerating ? (
            <>
              <Loader className="w-5 h-5 animate-spin" />
              <span>Generating...</span>
            </>
          ) : (
            <span>{hasContent ? 'Regenerate' : 'Generate'}</span>
          )}
        </button>
      )}
      
      {disabled && disabledMessage && (
        <p className="text-sm text-gray-600 mt-3 text-center bg-amber-50 px-3 py-2 rounded-lg border border-amber-200">
          {disabledMessage}
        </p>
      )}
    </div>
  );
};

const DetailSection = ({ title, data }) => {
  return (
    <div className="border-t border-gray-200 pt-6">
      <h3 className="text-xl font-bold text-gray-900 mb-4">{title}</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {Object.entries(data).map(([key, value]) => {
          if (typeof value === 'object' && !Array.isArray(value)) {
            return null; // Skip nested objects for simplicity
          }
          
          return (
            <div key={key} className="bg-gradient-to-br from-indigo-50 to-purple-50 p-4 rounded-lg border border-indigo-100">
              <dt className="text-sm font-semibold text-indigo-700 capitalize mb-2">
                {key.replace(/_/g, ' ')}
              </dt>
              <dd className="text-sm text-gray-900">
                {Array.isArray(value) ? (
                  <ul className="list-disc list-inside space-y-1">
                    {value.map((item, i) => (
                      <li key={i} className="text-gray-700">
                        {typeof item === 'object' ? JSON.stringify(item) : item}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <span className="font-medium">{value?.toString() || 'N/A'}</span>
                )}
              </dd>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default TrialDetail;
