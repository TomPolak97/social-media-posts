import { useState } from "react";
import axios from "axios";

export default function PostForm({ closeForm, fetchPosts, onSuccess }) {
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [email, setEmail] = useState("");
  const [company, setCompany] = useState("");
  const [jobTitle, setJobTitle] = useState("");
  const [text, setText] = useState("");
  const [category, setCategory] = useState("Product");
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    // Validation
    if (!firstName.trim() || !lastName.trim() || !email.trim() || !text.trim()) {
      setError("First name, last name, email, and post text are required");
      return;
    }

    // Basic email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email.trim())) {
      setError("Please enter a valid email address");
      return;
    }

    try {
      const postData = {
        first_name: firstName.trim(),
        last_name: lastName.trim(),
        email: email.trim(),
        company: company.trim() || null,
        job_title: jobTitle.trim() || null,
        text: text.trim(),
        category: category || null
      };

      await axios.post("http://127.0.0.1:8000/posts", postData);
      fetchPosts();
      closeForm();
      
      // Show success notification
      if (onSuccess) {
        onSuccess("Post added successfully! ✓");
      }
    } catch (err) {
      console.error("Add post failed:", err);
      setError(err.response?.data?.detail || "Failed to create post. Please try again.");
    }
  };

  return (
    <div className="modal-overlay" onClick={closeForm}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <form onSubmit={handleSubmit}>
          <h2>Add New Post</h2>
          
          {error && (
            <div className="error-message">
              {error}
            </div>
          )}

          <div className="form-group">
            <label htmlFor="firstName">First Name *</label>
            <input
              type="text"
              id="firstName"
              value={firstName}
              onChange={(e) => setFirstName(e.target.value)}
              placeholder="Enter first name"
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="lastName">Last Name *</label>
            <input
              type="text"
              id="lastName"
              value={lastName}
              onChange={(e) => setLastName(e.target.value)}
              placeholder="Enter last name"
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="email">Email *</label>
            <input
              type="email"
              id="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Enter email address"
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="company">Company</label>
            <input
              type="text"
              id="company"
              value={company}
              onChange={(e) => setCompany(e.target.value)}
              placeholder="Enter company name (optional)"
            />
          </div>

          <div className="form-group">
            <label htmlFor="jobTitle">Job Title</label>
            <input
              type="text"
              id="jobTitle"
              value={jobTitle}
              onChange={(e) => setJobTitle(e.target.value)}
              placeholder="Enter job title (optional)"
            />
          </div>

          <div className="form-group">
            <label htmlFor="category">Category</label>
            <select 
              id="category"
              value={category} 
              onChange={(e) => setCategory(e.target.value)}
            >
              <option value="Product">Product</option>
              <option value="Marketing">Marketing</option>
              <option value="Business">Business</option>
              <option value="Technology">Technology</option>
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="text">Post Text *</label>
            <textarea
              id="text"
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Enter post text..."
              required
              rows={5}
            />
          </div>

          <div className="form-actions">
            <button type="button" onClick={closeForm}>Cancel</button>
            <button type="submit">Add Post</button>
          </div>
        </form>
      </div>
    </div>
  );
}
