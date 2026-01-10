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
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
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
      
      // Build query parameters
      const params = new URLSearchParams({
        page: page.toString(),
        per_page: POSTS_PER_PAGE.toString(),
        sort_by: sortBy,
      });
      
      if (search) params.append("search", search);
      if (category && category !== "All Categories") params.append("category", category);
      if (dateFrom) params.append("date_from", dateFrom);
      if (dateTo) params.append("date_to", dateTo);
      if (firstName) params.append("first_name", firstName);
      if (lastName) params.append("last_name", lastName);
      
      const res = await axios.get(`http://127.0.0.1:8000/posts?${params.toString()}`);
      
      setPosts(res.data.posts || []);
      setTotalPages(res.data.total_pages || 1);
      setTotal(res.data.total || 0);
    } catch (err) {
      console.error("Error fetching posts:", err);
      setPosts([]);
      setTotalPages(1);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  };
  
  // Refresh function for add/delete operations - refreshes both posts and triggers stats refresh
  const refreshAll = async (resetPage = false) => {
    // Reset to page 1 if requested (for new posts)
    if (resetPage) {
      setPage(1);
    }
    
    // Always fetch posts (useEffect will handle it if page changed)
    await fetchPosts();
    
    // Trigger stats refresh event for Header
    window.dispatchEvent(new CustomEvent('refreshStats'));
  };

  // Fetch posts whenever filters, sort, or page changes
  useEffect(() => {
    fetchPosts();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, search, category, dateFrom, dateTo, firstName, lastName, sortBy]);

  // Reset to page 1 when filters change (but not on initial load)
  useEffect(() => {
    if (page !== 1) {
      setPage(1);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [search, category, dateFrom, dateTo, firstName, lastName, sortBy]);

  return (
    <div className="App">
      {toast.show && (
        <Toast 
          message={toast.message} 
          type={toast.type} 
          onClose={hideToast}
        />
      )}
      <Header fetchPosts={refreshAll} onSuccess={showToast} />
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
        posts={posts} 
        loading={loading} 
        fetchPosts={refreshAll}
        onSuccess={showToast}
        onError={(msg) => showToast(msg, "error")}
      />
      <Pagination page={page} setPage={setPage} totalPages={totalPages} />
    </div>
  );
}

export default App;
