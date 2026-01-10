import { useState } from "react";
import axios from "axios";

export default function PostForm({ closeForm, fetchPosts, onSuccess }) {
  const [text, setText] = useState("");
  const [category, setCategory] = useState("Product");

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post("http://127.0.0.1:8000/posts", { post_text: text, post_category: category });
      fetchPosts();
      closeForm();
      
      // Show success notification
      if (onSuccess) {
        onSuccess("Post added successfully! ✓");
      }
    } catch (err) {
      console.error("Add post failed:", err);
    }
  };

  return (
    <div style={{ position: "fixed", top: 0, left: 0, width: "100%", height: "100%",
                  background: "rgba(0,0,0,0.3)", display: "flex", justifyContent: "center", alignItems: "center" }}>
      <form onSubmit={handleSubmit} style={{ background: "#fff", padding: "24px", borderRadius: "8px", width: "400px" }}>
        <h2>Add New Post</h2>
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Post text"
          required
          style={{ width: "100%", minHeight: "100px", marginBottom: "12px" }}
        />
        <select value={category} onChange={(e) => setCategory(e.target.value)} style={{ width: "100%", marginBottom: "12px" }}>
          <option>Product</option>
          <option>Marketing</option>
          <option>Business</option>
          <option>Technology</option>
        </select>
        <div style={{ display: "flex", justifyContent: "flex-end", gap: "8px" }}>
          <button type="button" onClick={closeForm}>Cancel</button>
          <button type="submit" style={{ backgroundColor: "#48bb78", color: "#fff" }}>Add</button>
        </div>
      </form>
    </div>
  );
}
