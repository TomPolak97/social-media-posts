import axios from "axios";

export default function PostCard({ post, fetchPosts }) {
  const handleDelete = async () => {
    try {
      await axios.delete(`http://127.0.0.1:8000/posts/${post.id}`);
      fetchPosts();
    } catch (err) {
      console.error("Delete failed:", err);
    }
  };

  return (
    <div className="post-card">
      <div className="post-header">
        <div className="post-author">{post.author_first_name} {post.author_last_name}</div>
        <div>
          <button onClick={handleDelete} title="Delete">🗑️</button>
          <button title="Edit">✏️</button>
        </div>
      </div>
      <div className="post-text">{post.post_text}</div>
      {post.post_image_svg ? (
        <div dangerouslySetInnerHTML={{ __html: post.post_image_svg }} />
      ) : (
        <div style={{ height: "150px", background: "linear-gradient(45deg,#eee,#ddd)" }} />
      )}
      <div className="post-stats">
        <span>👍 {post.likes}</span>
        <span>💬 {post.comments}</span>
        <span>📊 {post.total_engagements}</span>
      </div>
      <div className="post-meta">{post.post_category} • {new Date(post.post_date).toLocaleDateString()}</div>
    </div>
  );
}
