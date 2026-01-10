export default function Filters({ search, setSearch, category, setCategory, sortBy, setSortBy }) {
  const categories = ["All Categories", "Product", "Marketing", "Business", "Technology"];
  const sortOptions = ["Most Recent", "Highest Engagement", "Most Liked", "Most Commented"];

  return (
    <div className="filters">
      <input
        type="text"
        placeholder="Search posts..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
      />
      <select value={category} onChange={(e) => setCategory(e.target.value)}>
        {categories.map((c) => (
          <option key={c} value={c}>{c}</option>
        ))}
      </select>
      <select value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
        {sortOptions.map((s) => (
          <option key={s} value={s}>{s}</option>
        ))}
      </select>
      <button onClick={() => { setSearch(""); setCategory("All Categories"); setSortBy("Most Recent"); }}>
        Clear All
      </button>
    </div>
  );
}
