import { useState, useEffect } from "react";
import axios from "axios";
import PostForm from "./PostForm";

export default function Header({ fetchPosts, onSuccess }) {
  const [showForm, setShowForm] = useState(false);
  const [stats, setStats] = useState({
    total_posts: 0,
    total_likes: 0,
    total_comments: 0,
    avg_engagement_rate: 0
  });

  const fetchStats = async () => {
    try {
      const res = await axios.get("http://127.0.0.1:8000/posts/stats");
      setStats(res.data);
    } catch (err) {
      console.error("Error fetching stats:", err);
    }
  };

  useEffect(() => {
    fetchStats();
    
    // Listen for stats refresh events (triggered after add/delete operations)
    const handleStatsRefresh = () => {
      fetchStats();
    };
    
    window.addEventListener('refreshStats', handleStatsRefresh);
    
    return () => {
      window.removeEventListener('refreshStats', handleStatsRefresh);
    };
  }, []);

  // Refresh posts when fetchPosts is called (after add/delete operations)
  const handleRefresh = async (resetPage = false) => {
    if (fetchPosts) {
      await fetchPosts(resetPage);
    }
  };

  const totalPosts = stats.total_posts || 0;
  const totalLikes = stats.total_likes || 0;
  const totalComments = stats.total_comments || 0;
  const avgEngagement = stats.avg_engagement_rate || 0;

  // Format large numbers
  const formatNumber = (num) => {
    if (num >= 1000000) {
      return (num / 1000000).toFixed(1) + "M";
    } else if (num >= 1000) {
      return (num / 1000).toFixed(1) + "K";
    }
    return num.toLocaleString();
  };

  return (
    <>
      {/* Dashboard Title */}
      <div className="dashboard-title">
        <h1>Social Media Posts</h1>
        <p>Browse and manage all social media posts with advanced filtering</p>
      </div>

      {/* Header with Stats and Add Button */}
      <div className="header">
        <div className="stats-grid">
          <div className="stat-box">
            <div className="stat-label">Total Posts</div>
            <div className="stat-value">{totalPosts.toLocaleString()}</div>
          </div>
          <div className="stat-box">
            <div className="stat-label">Total Likes</div>
            <div className="stat-value">{formatNumber(totalLikes)}</div>
          </div>
          <div className="stat-box">
            <div className="stat-label">Total Comments</div>
            <div className="stat-value">{formatNumber(totalComments)}</div>
          </div>
          <div className="stat-box">
            <div className="stat-label">Avg Engagement</div>
            <div className="stat-value">{avgEngagement}%</div>
          </div>
        </div>
        <button
          className="add-post-button"
          onClick={() => setShowForm(true)}
        >
          ➕ Add New Post
        </button>
      </div>
      {showForm && (
        <PostForm 
          closeForm={() => setShowForm(false)} 
          fetchPosts={handleRefresh}
          onSuccess={onSuccess}
        />
      )}
    </>
  );
}
