import { useState } from "react";
import PostForm from "./PostForm";

export default function Header({ posts, fetchPosts }) {
  const [showForm, setShowForm] = useState(false);

  const totalPosts = posts.length;
  const totalLikes = posts.reduce((sum, p) => sum + p.likes, 0);
  const totalComments = posts.reduce((sum, p) => sum + p.comments, 0);
  const avgEngagement = totalPosts
    ? ((posts.reduce((sum, p) => sum + p.total_engagements, 0) / totalPosts) * 100).toFixed(1)
    : 0;

  return (
    <div className="header">
      <div className="stats">
        <div>Total Posts: {totalPosts}</div>
        <div>Total Likes: {totalLikes}</div>
        <div>Total Comments: {totalComments}</div>
        <div>Avg Engagement: {avgEngagement}%</div>
      </div>
      <button
        style={{ backgroundColor: "#48bb78", color: "white", padding: "10px", borderRadius: "4px" }}
        onClick={() => setShowForm(true)}
      >
        ➕ Add New Post
      </button>
      {showForm && <PostForm closeForm={() => setShowForm(false)} fetchPosts={fetchPosts} />}
    </div>
  );
}
