import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { generationAPI } from '../services/api';
import { ArrowLeft, Download, Loader, Play, Pause, Volume2, VolumeX, Maximize } from 'lucide-react';
import Navbar from '../components/Navbar';

const VideoViewer = () => {
  const { id, contentId } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [contentData, setContentData] = useState(null);
  const [videoUrl, setVideoUrl] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [videoRef, setVideoRef] = useState(null);

  useEffect(() => {
    loadVideo();
  }, [contentId]);

  const loadVideo = async () => {
    try {
      const data = await generationAPI.getContentData(contentId);
      setContentData(data);
      
      // Construct video URL from file path
      if (data.data?.file_path) {
        // The file_path will be like: uploads/video_outputs/trial_1/20231026_123456/final_video.mp4
        // We need to serve this as: http://localhost:8000/uploads/video_outputs/...
        const videoPath = data.data.file_path.replace(/^uploads\//, '');
        setVideoUrl(`http://localhost:8000/uploads/${videoPath}`);
      }
    } catch (error) {
      console.error('Error loading video:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async () => {
    if (!videoUrl) return;
    
    try {
      const response = await fetch(videoUrl);
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `trial_${id}_video.mp4`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Error downloading video:', error);
      alert('Failed to download video');
    }
  };

  const togglePlay = () => {
    if (!videoRef) return;
    
    if (isPlaying) {
      videoRef.pause();
    } else {
      videoRef.play();
    }
    setIsPlaying(!isPlaying);
  };

  const toggleMute = () => {
    if (!videoRef) return;
    videoRef.muted = !isMuted;
    setIsMuted(!isMuted);
  };

  const toggleFullscreen = () => {
    if (!videoRef) return;
    
    if (videoRef.requestFullscreen) {
      videoRef.requestFullscreen();
    } else if (videoRef.webkitRequestFullscreen) {
      videoRef.webkitRequestFullscreen();
    } else if (videoRef.msRequestFullscreen) {
      videoRef.msRequestFullscreen();
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 via-indigo-50 to-purple-50">
        <Navbar />
        <div className="flex items-center justify-center h-96">
          <div className="flex flex-col items-center space-y-4">
            <Loader className="w-12 h-12 text-indigo-600 animate-spin" />
            <p className="text-xl text-gray-700">Loading video...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-indigo-50 to-purple-50">
      <Navbar />
      
      <div className="max-w-6xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={() => navigate(`/trial/${id}`)}
            className="flex items-center space-x-2 text-indigo-600 hover:text-indigo-700 mb-6 transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
            <span className="font-medium">Back to Trial</span>
          </button>
          
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-4xl font-bold bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 bg-clip-text text-transparent">
                Educational Video
              </h1>
              <p className="text-gray-600 mt-2">
                Patient-friendly video explanation of the clinical trial
              </p>
            </div>
            
            <button
              onClick={handleDownload}
              className="btn-gradient flex items-center space-x-2"
              disabled={!videoUrl}
            >
              <Download className="w-5 h-5" />
              <span>Download Video</span>
            </button>
          </div>
        </div>

        {/* Video Player */}
        <div className="glass-card overflow-hidden">
          {videoUrl ? (
            <div className="relative bg-black group">
              <video
                ref={setVideoRef}
                className="w-full aspect-video"
                src={videoUrl}
                onPlay={() => setIsPlaying(true)}
                onPause={() => setIsPlaying(false)}
                controls
                playsInline
                preload="metadata"
              >
                Your browser does not support the video tag.
              </video>
              
              {/* Custom Controls Overlay (optional - browser controls are already there) */}
              <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent opacity-0 group-hover:opacity-100 transition-opacity p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <button
                      onClick={togglePlay}
                      className="text-white hover:text-indigo-300 transition-colors"
                    >
                      {isPlaying ? (
                        <Pause className="w-8 h-8" />
                      ) : (
                        <Play className="w-8 h-8" />
                      )}
                    </button>
                    
                    <button
                      onClick={toggleMute}
                      className="text-white hover:text-indigo-300 transition-colors"
                    >
                      {isMuted ? (
                        <VolumeX className="w-6 h-6" />
                      ) : (
                        <Volume2 className="w-6 h-6" />
                      )}
                    </button>
                  </div>
                  
                  <button
                    onClick={toggleFullscreen}
                    className="text-white hover:text-indigo-300 transition-colors"
                  >
                    <Maximize className="w-6 h-6" />
                  </button>
                </div>
              </div>
            </div>
          ) : (
            <div className="aspect-video flex items-center justify-center bg-gray-100">
              <div className="text-center">
                <Video className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-600">Video not available</p>
              </div>
            </div>
          )}
        </div>

        {/* Video Metadata */}
        {contentData?.data?.metadata && (
          <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="soft-card">
              <h3 className="text-sm font-medium text-gray-500 mb-1">Segments</h3>
              <p className="text-2xl font-bold text-indigo-600">
                {contentData.data.metadata.segments_count || 0}
              </p>
            </div>
            
            <div className="soft-card">
              <h3 className="text-sm font-medium text-gray-500 mb-1">Visual Assets</h3>
              <p className="text-2xl font-bold text-purple-600">
                {contentData.data.metadata.images_count || 0}
              </p>
            </div>
            
            <div className="soft-card">
              <h3 className="text-sm font-medium text-gray-500 mb-1">Slides</h3>
              <p className="text-2xl font-bold text-pink-600">
                {contentData.data.metadata.slides_count || 0}
              </p>
            </div>
          </div>
        )}

        {/* Intermediate Outputs */}
        {contentData?.data?.intermediate_outputs && (
          <div className="mt-8 soft-card">
            <h2 className="text-xl font-bold text-gray-900 mb-4">
              Production Details
            </h2>
            
            <div className="space-y-4">
              {/* Script */}
              {contentData.data.intermediate_outputs.script && (
                <div className="border-l-4 border-indigo-500 pl-4">
                  <h3 className="font-medium text-gray-900">Video Script</h3>
                  <p className="text-sm text-gray-600 mt-1">
                    Contains narration, segments, and timing information
                  </p>
                  <a
                    href={`http://localhost:8000/${contentData.data.intermediate_outputs.script}`}
                    download
                    className="text-sm text-indigo-600 hover:text-indigo-700 mt-2 inline-flex items-center"
                  >
                    <Download className="w-4 h-4 mr-1" />
                    Download Script (JSON)
                  </a>
                </div>
              )}
              
              {/* Assets */}
              {contentData.data.intermediate_outputs.assets && (
                <div className="border-l-4 border-purple-500 pl-4">
                  <h3 className="font-medium text-gray-900">Visual Assets Plan</h3>
                  <p className="text-sm text-gray-600 mt-1">
                    Detailed specifications for all visual elements
                  </p>
                  <a
                    href={`http://localhost:8000/${contentData.data.intermediate_outputs.assets}`}
                    download
                    className="text-sm text-purple-600 hover:text-purple-700 mt-2 inline-flex items-center"
                  >
                    <Download className="w-4 h-4 mr-1" />
                    Download Assets (JSON)
                  </a>
                </div>
              )}
              
              {/* Metadata */}
              {contentData.data.intermediate_outputs.metadata && (
                <div className="border-l-4 border-pink-500 pl-4">
                  <h3 className="font-medium text-gray-900">Production Metadata</h3>
                  <p className="text-sm text-gray-600 mt-1">
                    Complete production information and timing
                  </p>
                  <a
                    href={`http://localhost:8000/${contentData.data.intermediate_outputs.metadata}`}
                    download
                    className="text-sm text-pink-600 hover:text-pink-700 mt-2 inline-flex items-center"
                  >
                    <Download className="w-4 h-4 mr-1" />
                    Download Metadata (JSON)
                  </a>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default VideoViewer;
