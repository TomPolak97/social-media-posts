import { useState, useEffect } from "react";
import axios from "axios";
import Header from "./components/Header";
import Filters from "./components/Filters";
import PostGrid from "./components/PostGrid";
import Pagination from "./components/Pagination";

function App() {
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("All Categories");
  const [sortBy, setSortBy] = useState("Most Recent");
  const [page, setPage] = useState(1);
  const POSTS_PER_PAGE = 5;

  const fetchPosts = async () => {
    try {
      setLoading(true);
      const res = await axios.get("http://127.0.0.1:8000/posts");
      setPosts(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPosts();
  }, []);

  // Filtering and searching
  const filtered = posts.filter(post => {
    const matchesSearch = post.text.toLowerCase().includes(search.toLowerCase());
    const matchesCategory = category === "All Categories" || post.category === category;
    return matchesSearch && matchesCategory;
  });

  // Sorting
  const sorted = filtered.sort((a, b) => {
    switch (sortBy) {
      case "Highest Engagement":
        return b.total_engagements - a.total_engagements;
      case "Most Liked":
        return b.likes - a.likes;
      case "Most Commented":
        return b.comments - a.comments;
      case "Most Recent":
      default:
        return new Date(b.post_date) - new Date(a.post_date);
    }
  });

  // Pagination
  const totalPages = Math.ceil(sorted.length / POSTS_PER_PAGE);
  const paginated = sorted.slice((page - 1) * POSTS_PER_PAGE, page * POSTS_PER_PAGE);

  return (
    <div className="App">
      <Header posts={posts} fetchPosts={fetchPosts} />
      <Filters
        search={search} setSearch={setSearch}
        category={category} setCategory={setCategory}
        sortBy={sortBy} setSortBy={setSortBy}
      />
      <PostGrid posts={paginated} loading={loading} fetchPosts={fetchPosts} />
      <Pagination page={page} setPage={setPage} totalPages={totalPages} />
    </div>
  );
}

export default App;
