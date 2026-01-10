import { useState } from "react";
import PostForm from "./PostForm";

export default function Header({ posts, fetchPosts, onSuccess }) {
  const [showForm, setShowForm] = useState(false);

  const totalPosts = posts.length;
  const totalLikes = posts.reduce((sum, p) => sum + (p.likes || 0), 0);
  const totalComments = posts.reduce((sum, p) => sum + (p.comments || 0), 0);
  // Average engagement rate - engagement_rate is already a percentage
  const avgEngagement = totalPosts
    ? (posts.reduce((sum, p) => sum + (p.engagement_rate || 0), 0) / totalPosts).toFixed(1)
    : 0;

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
          fetchPosts={fetchPosts}
          onSuccess={onSuccess}
        />
      )}
    </>
  );
}
