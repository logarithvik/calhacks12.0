import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { trialsAPI, generationAPI } from '../services/api';
import { ArrowLeft, FileText, Image, Video, Loader, CheckCircle } from 'lucide-react';
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
        case 'infographic':
          result = await generationAPI.generateInfographic(id);
          break;
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
  const infographicContent = getContent('infographic');
  const videoContent = getContent('video');

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      
      <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <button
            onClick={() => navigate('/dashboard')}
            className="flex items-center space-x-2 text-indigo-600 hover:text-indigo-700 mb-6"
          >
            <ArrowLeft className="w-5 h-5" />
            <span>Back to Dashboard</span>
          </button>

          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">{trial.title}</h1>
            {trial.original_filename && (
              <p className="text-gray-600 mb-2">📄 {trial.original_filename}</p>
            )}
            <p className="text-sm text-gray-500">
              Created: {new Date(trial.created_at).toLocaleDateString()}
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            {/* Summary Card */}
            <GenerationCard
              title="Summary"
              icon={<FileText className="w-8 h-8 text-indigo-600" />}
              description="Extract key information from the protocol"
              hasContent={!!summaryContent}
              isGenerating={generating.summary}
              onGenerate={() => handleGenerate('summary')}
              onEdit={() => navigate(`/trial/${id}/summary/edit`)}
              contentId={summaryContent?.id}
            />

            {/* Infographic Card */}
            <GenerationCard
              title="Infographic"
              icon={<Image className="w-8 h-8 text-green-600" />}
              description="Create visual summary for patients"
              hasContent={!!infographicContent}
              isGenerating={generating.infographic}
              onGenerate={() => handleGenerate('infographic')}
              contentId={infographicContent?.id}
              disabled={!summaryContent}
              disabledMessage="Generate summary first"
            />

            {/* Video Card */}
            <GenerationCard
              title="Video"
              icon={<Video className="w-8 h-8 text-purple-600" />}
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
            <div className="bg-white rounded-lg shadow-md p-6 mb-6">
              <h2 className="text-2xl font-bold mb-4">Trial Summary</h2>
              
              {summaryData.simple_summary && (
                <div className="prose max-w-none mb-6">
                  <pre className="whitespace-pre-wrap font-sans">{summaryData.simple_summary}</pre>
                </div>
              )}

              {summaryData.structured_data && (
                <div className="space-y-4">
                  <DetailSection title="Study Information" data={summaryData.structured_data} />
                </div>
              )}
            </div>
          )}

          {/* Infographic Display */}
          {infographicContent && (
            <div className="bg-white rounded-lg shadow-md p-6 mb-6">
              <h2 className="text-2xl font-bold mb-4">Infographic</h2>
              <div className="bg-gray-100 rounded-lg p-8 text-center">
                <Image className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-600">
                  Infographic placeholder - In production, this would display the generated image
                </p>
                <p className="text-sm text-gray-500 mt-2">
                  File: {infographicContent.file_path}
                </p>
              </div>
            </div>
          )}

          {/* Video Display */}
          {videoContent && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-2xl font-bold mb-4">Educational Video</h2>
              <div className="bg-gray-100 rounded-lg p-8 text-center">
                <Video className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-600">
                  Video placeholder - In production, this would be an embedded video player
                </p>
                <p className="text-sm text-gray-500 mt-2">
                  File: {videoContent.file_path}
                </p>
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
  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex items-center space-x-3 mb-4">
        {icon}
        <h3 className="text-xl font-semibold">{title}</h3>
      </div>
      
      <p className="text-gray-600 mb-4">{description}</p>
      
      {hasContent && (
        <div className="flex items-center space-x-2 text-green-600 mb-3">
          <CheckCircle className="w-5 h-5" />
          <span className="text-sm font-medium">Generated</span>
        </div>
      )}
      
      {hasContent && (onEdit || onView) ? (
        <div className="space-y-2">
          {onEdit && (
            <button
              onClick={onEdit}
              className="w-full flex items-center justify-center space-x-2 px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition-colors"
            >
              <FileText className="w-5 h-5" />
              <span>Edit Summary</span>
            </button>
          )}
          {onView && (
            <button
              onClick={onView}
              className="w-full flex items-center justify-center space-x-2 px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 transition-colors"
            >
              <Video className="w-5 h-5" />
              <span>View Video</span>
            </button>
          )}
          <button
            onClick={onGenerate}
            disabled={isGenerating}
            className="w-full flex items-center justify-center space-x-2 px-4 py-2 bg-indigo-100 text-indigo-700 rounded-md hover:bg-indigo-200 transition-colors"
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
          className={`w-full flex items-center justify-center space-x-2 px-4 py-2 rounded-md transition-colors ${
            disabled
              ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
              : hasContent
              ? 'bg-indigo-100 text-indigo-700 hover:bg-indigo-200'
              : 'bg-indigo-600 text-white hover:bg-indigo-700'
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
        <p className="text-xs text-gray-500 mt-2 text-center">{disabledMessage}</p>
      )}
    </div>
  );
};

const DetailSection = ({ title, data }) => {
  return (
    <div className="border-t pt-4">
      <h3 className="text-lg font-semibold mb-3">{title}</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {Object.entries(data).map(([key, value]) => {
          if (typeof value === 'object' && !Array.isArray(value)) {
            return null; // Skip nested objects for simplicity
          }
          
          return (
            <div key={key} className="bg-gray-50 p-3 rounded">
              <dt className="text-sm font-medium text-gray-500 capitalize mb-1">
                {key.replace(/_/g, ' ')}
              </dt>
              <dd className="text-sm text-gray-900">
                {Array.isArray(value) ? (
                  <ul className="list-disc list-inside">
                    {value.map((item, i) => (
                      <li key={i}>{typeof item === 'object' ? JSON.stringify(item) : item}</li>
                    ))}
                  </ul>
                ) : (
                  value?.toString() || 'N/A'
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
