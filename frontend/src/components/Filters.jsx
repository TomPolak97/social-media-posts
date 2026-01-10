export default function Filters({ 
  search, setSearch,
  category, setCategory,
  dateFrom, setDateFrom,
  dateTo, setDateTo,
  firstName, setFirstName,
  lastName, setLastName,
  sortBy, setSortBy,
  onClearAll
}) {
  const categories = ["All Categories", "Product", "Marketing", "Business", "Technology"];
  const sortOptions = ["Most Recent", "Highest Engagement", "Most Liked", "Most Commented"];

  return (
    <div className="filters">
      <input
        type="text"
        placeholder="Search post text..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
      />
      <select value={category} onChange={(e) => setCategory(e.target.value)}>
        {categories.map((c) => (
          <option key={c} value={c}>{c}</option>
        ))}
      </select>
      <input
        type="date"
        placeholder="Date From"
        value={dateFrom}
        onChange={(e) => setDateFrom(e.target.value)}
        title="Date From"
      />
      <input
        type="date"
        placeholder="Date To"
        value={dateTo}
        onChange={(e) => setDateTo(e.target.value)}
        title="Date To"
      />
      <input
        type="text"
        placeholder="First Name"
        value={firstName}
        onChange={(e) => setFirstName(e.target.value)}
      />
      <input
        type="text"
        placeholder="Last Name"
        value={lastName}
        onChange={(e) => setLastName(e.target.value)}
      />
      <select value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
        {sortOptions.map((s) => (
          <option key={s} value={s}>{s}</option>
        ))}
      </select>
      <button onClick={onClearAll}>
        Clear All
      </button>
    </div>
  );
}
