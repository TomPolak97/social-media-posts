import axios from "axios";

export default function PostCard({ post, fetchPosts, onSuccess, onError }) {
  const handleDelete = async () => {
    // Confirm deletion
    const confirmed = window.confirm(
      `Are you sure you want to delete this post?\n\n"${(post.text || "").substring(0, 50)}${(post.text || "").length > 50 ? "..." : ""}"`
    );
    
    if (!confirmed) {
      return;
    }

    try {
      await axios.delete(`http://127.0.0.1:8000/posts/${post.id}`);
      
      // Show success notification first
      if (onSuccess) {
        onSuccess("Post deleted successfully! ✓");
      }
      
      // Refresh posts (pass false to stay on current page)
      if (fetchPosts) {
        fetchPosts(false);
      }
    } catch (err) {
      console.error("Delete failed:", err);
      const errorMsg = err.response?.data?.detail || "Failed to delete post. Please try again.";
      
      // Show error notification
      if (onError) {
        onError(errorMsg);
      }
    }
  };

  // Get author information from nested object or flat structure (for backwards compatibility)
  const authorFirstName = post.author?.first_name || post.author_first_name || "";
  const authorLastName = post.author?.last_name || post.author_last_name || "";
  const jobTitle = post.author?.job_title || post.job_title || "";
  const company = post.author?.company || post.company || "";
  const postText = post.text || post.post_text || "";
  const postImage = post.svg_image || post.post_image_svg || null;
  const postCategory = post.category || post.post_category || "";

  // Format job title and company
  const jobInfo = jobTitle && company 
    ? `${jobTitle} at ${company}`
    : jobTitle || company || "";

  // Format date for display
  const formatDate = (postDate) => {
    if (!postDate) return "Unknown";
    
    try {
      const postDateObj = new Date(postDate);
      if (isNaN(postDateObj.getTime())) {
        return "Invalid date";
      }
      return postDateObj.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      });
    } catch (error) {
      return "Unknown";
    }
  };

  // Calculate relative time (days ago)
  const getRelativeTime = (postDate) => {
    if (!postDate) return "Unknown";
    
    try {
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      
      const postDateObj = new Date(postDate);
      if (isNaN(postDateObj.getTime())) {
        return "Unknown";
      }
      
      postDateObj.setHours(0, 0, 0, 0);
      
      const diffTime = today - postDateObj;
      const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
      
      if (diffDays < 0) {
        return "Future";
      } else if (diffDays === 0) {
        return "Today";
      } else if (diffDays === 1) {
        return "1 day ago";
      } else if (diffDays < 7) {
        return `${diffDays} days ago`;
      } else if (diffDays < 30) {
        const weeks = Math.floor(diffDays / 7);
        return weeks === 1 ? "1 week ago" : `${weeks} weeks ago`;
      } else if (diffDays < 365) {
        const months = Math.floor(diffDays / 30);
        return months === 1 ? "1 month ago" : `${months} months ago`;
      } else {
        const years = Math.floor(diffDays / 365);
        return years === 1 ? "1 year ago" : `${years} years ago`;
      }
    } catch (error) {
      return "Unknown";
    }
  };

  // Process SVG to ensure proper display within container
  const processSVG = (svgString) => {
    if (!svgString) return svgString;
    
    let processed = svgString;
    
    // Extract width and height if they exist (before removing them)
    const widthMatch = processed.match(/width="([^"]*)"/i);
    const heightMatch = processed.match(/height="([^"]*)"/i);
    const viewBoxMatch = processed.match(/viewBox="([^"]*)"/i);
    
    // Remove fixed width/height attributes that might cause cropping
    processed = processed.replace(/\s+width="[^"]*"/gi, '');
    processed = processed.replace(/\s+height="[^"]*"/gi, '');
    
    // Ensure viewBox exists - if not, try to create one from width/height
    if (!viewBoxMatch && widthMatch && heightMatch) {
      const width = widthMatch[1];
      const height = heightMatch[1];
      const widthNum = parseFloat(width);
      const heightNum = parseFloat(height);
      if (!isNaN(widthNum) && !isNaN(heightNum)) {
        processed = processed.replace(/<svg/i, `<svg viewBox="0 0 ${widthNum} ${heightNum}"`);
      }
    }
    
    // If still no viewBox, add a default one
    if (!processed.includes('viewBox=') && !viewBoxMatch) {
      processed = processed.replace(/<svg/i, '<svg viewBox="0 0 800 600"');
    }
    
    // Ensure preserveAspectRatio is set to maintain aspect ratio
    if (!processed.includes('preserveAspectRatio')) {
      processed = processed.replace(/<svg/i, '<svg preserveAspectRatio="xMidYMid meet"');
    } else {
      processed = processed.replace(/preserveAspectRatio="[^"]*"/i, 'preserveAspectRatio="xMidYMid meet"');
    }
    
    // Add style to ensure proper scaling within container
    if (!processed.includes('style=')) {
      processed = processed.replace(/<svg/i, '<svg style="width: 100%; height: auto; max-width: 100%; max-height: 100%; display: block; box-sizing: border-box;"');
    } else {
      processed = processed.replace(/style="([^"]*)"/i, (match, style) => {
        let cleanStyle = style.replace(/width\s*:[^;]*;?/gi, '');
        cleanStyle = cleanStyle.replace(/height\s*:[^;]*;?/gi, '');
        cleanStyle = cleanStyle.replace(/max-width\s*:[^;]*;?/gi, '');
        cleanStyle = cleanStyle.replace(/max-height\s*:[^;]*;?/gi, '');
        cleanStyle = cleanStyle.replace(/display\s*:[^;]*;?/gi, '');
        cleanStyle = cleanStyle.replace(/box-sizing\s*:[^;]*;?/gi, '');
        const newStyle = cleanStyle + '; width: 100%; height: auto; max-width: 100%; max-height: 100%; display: block; box-sizing: border-box;';
        return `style="${newStyle}"`;
      });
    }
    
    return processed;
  };

  return (
    <div className="post-card">
      {/* Image - displayed first */}
      {postImage ? (
        <div className="post-image-wrapper">
          <div className="post-image" dangerouslySetInnerHTML={{ __html: processSVG(postImage) }} />
        </div>
      ) : (
        <div className="post-image-placeholder" />
      )}
      
      {/* Author name */}
      <div className="post-author">
        {authorFirstName} {authorLastName}
      </div>
      
      {/* Job title and company */}
      {jobInfo && (
        <div className="post-job-info">{jobInfo}</div>
      )}
      
      {/* Category */}
      {postCategory && (
        <div className="post-category">{postCategory}</div>
      )}
      
      {/* Post date and relative time */}
      {post.post_date && (
        <div className="post-time">
          {getRelativeTime(post.post_date)} • {formatDate(post.post_date)}
        </div>
      )}
      
      {/* Post text */}
      <div className="post-text">{postText}</div>
      
      {/* Post stats - likes, comments, engagements */}
      <div className="post-stats">
        <span>👍 {post.likes || 0}</span>
        <span>💬 {post.comments || 0}</span>
        <span>📊 {post.total_engagements || 0}</span>
      </div>
      
      {/* Action buttons */}
      <div className="post-actions">
        <button onClick={handleDelete} title="Delete">🗑️</button>
        <button title="Edit">✏️</button>
      </div>
    </div>
  );
}
