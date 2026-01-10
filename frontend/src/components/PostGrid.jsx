import PostCard from "./PostCard";
import SkeletonCard from "./SkeletonCard";

export default function PostGrid({ posts, loading, fetchPosts }) {
  if (loading) {
    return (
      <div className="post-grid">
        {Array(5).fill(0).map((_, i) => <SkeletonCard key={i} />)}
      </div>
    );
  }

  if (!posts.length) return <p>No posts found.</p>;

  return (
    <div className="post-grid">
      {posts.map((post) => (
        <PostCard key={post.id} post={post} fetchPosts={fetchPosts} />
      ))}
    </div>
  );
}
