export default function Pagination({ page, setPage, totalPages }) {
  return (
    <div style={{ marginTop: "20px", display: "flex", justifyContent: "center", gap: "8px" }}>
      <button disabled={page === 1} onClick={() => setPage(page - 1)}>← Previous</button>
      <span>{page} / {totalPages}</span>
      <button disabled={page === totalPages} onClick={() => setPage(page + 1)}>Next →</button>
    </div>
  );
}
