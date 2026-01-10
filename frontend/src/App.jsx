import { useState, useEffect } from "react";
import axios from "axios";
import Header from "./components/header";
import Filters from "./components/Filters";
import PostGrid from "./components/PostGrid";
import Pagination from "./components/Pagination";
import Toast from "./components/Toast";

function App() {
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("All Categories");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [sortBy, setSortBy] = useState("Most Recent");
  const [page, setPage] = useState(1);
  const [toast, setToast] = useState({ show: false, message: "", type: "success" });
  const POSTS_PER_PAGE = 3;

  const showToast = (message, type = "success") => {
    setToast({ show: true, message, type });
  };

  const hideToast = () => {
    setToast({ show: false, message: "", type: "success" });
  };

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

  // Reset to page 1 when filters change
  useEffect(() => {
    setPage(1);
  }, [search, category, dateFrom, dateTo, firstName, lastName]);

  // Filtering and searching
  const filtered = posts.filter(post => {
    // Post text search
    const matchesSearch = !search || (post.text || "").toLowerCase().includes(search.toLowerCase());
    
    // Category filter
    const matchesCategory = category === "All Categories" || (post.category || "") === category;
    
    // First name filter
    const authorFirstName = post.author?.first_name || "";
    const matchesFirstName = !firstName || authorFirstName.toLowerCase().includes(firstName.toLowerCase());
    
    // Last name filter
    const authorLastName = post.author?.last_name || "";
    const matchesLastName = !lastName || authorLastName.toLowerCase().includes(lastName.toLowerCase());
    
    // Date range filter
    let matchesDateFrom = true;
    let matchesDateTo = true;
    
    if (dateFrom || dateTo) {
      const postDate = new Date(post.post_date);
      if (!isNaN(postDate.getTime())) {
        postDate.setHours(0, 0, 0, 0);
        
        if (dateFrom) {
          const fromDate = new Date(dateFrom);
          fromDate.setHours(0, 0, 0, 0);
          matchesDateFrom = postDate >= fromDate;
        }
        
        if (dateTo) {
          const toDate = new Date(dateTo);
          toDate.setHours(23, 59, 59, 999);
          matchesDateTo = postDate <= toDate;
        }
      } else {
        // If date is invalid, exclude from results if date filters are set
        matchesDateFrom = false;
        matchesDateTo = false;
      }
    }
    
    return matchesSearch && matchesCategory && matchesFirstName && matchesLastName && matchesDateFrom && matchesDateTo;
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
      {toast.show && (
        <Toast 
          message={toast.message} 
          type={toast.type} 
          onClose={hideToast}
        />
      )}
      <Header posts={posts} fetchPosts={fetchPosts} onSuccess={showToast} />
      <Filters
        search={search} setSearch={setSearch}
        category={category} setCategory={setCategory}
        dateFrom={dateFrom} setDateFrom={setDateFrom}
        dateTo={dateTo} setDateTo={setDateTo}
        firstName={firstName} setFirstName={setFirstName}
        lastName={lastName} setLastName={setLastName}
        sortBy={sortBy} setSortBy={setSortBy}
        onClearAll={() => {
          setSearch("");
          setCategory("All Categories");
          setDateFrom("");
          setDateTo("");
          setFirstName("");
          setLastName("");
          setSortBy("Most Recent");
          setPage(1);
        }}
      />
      <PostGrid 
        posts={paginated} 
        loading={loading} 
        fetchPosts={fetchPosts}
        onSuccess={showToast}
        onError={(msg) => showToast(msg, "error")}
      />
      <Pagination page={page} setPage={setPage} totalPages={totalPages} />
    </div>
  );
}

export default App;
