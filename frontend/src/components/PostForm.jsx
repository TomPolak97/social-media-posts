import { useState, useEffect } from "react";
import axios from "axios";

export default function PostForm({ closeForm, fetchPosts, onSuccess, post = null, isEdit = false }) {
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [email, setEmail] = useState("");
  const [company, setCompany] = useState("");
  const [jobTitle, setJobTitle] = useState("");
  const [text, setText] = useState("");
  const [category, setCategory] = useState("Product");
  const [error, setError] = useState("");

  // Pre-fill form if editing
  useEffect(() => {
    if (isEdit && post) {
      setFirstName(post.author?.first_name || "");
      setLastName(post.author?.last_name || "");
      setEmail(post.author?.email || "");
      setCompany(post.author?.company || "");
      setJobTitle(post.author?.job_title || "");
      setText(post.text || "");
      setCategory(post.category || "Product");
    }
  }, [isEdit, post]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    if (isEdit) {
      // Edit mode - build update object with all fields (user can edit any field)
      // Basic validation for email if provided
      if (email.trim()) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(email.trim())) {
          setError("Please enter a valid email address");
          return;
        }
      }

      // Build update data - include fields that have values or are being cleared
      const updateData = {};
      
      if (firstName.trim() && firstName.trim() !== (post?.author?.first_name || "")) {
        updateData.first_name = firstName.trim();
      }
      if (lastName.trim() && lastName.trim() !== (post?.author?.last_name || "")) {
        updateData.last_name = lastName.trim();
      }
      if (email.trim() && email.trim() !== (post?.author?.email || "")) {
        updateData.email = email.trim();
      }
      // Check if company changed (handle null/undefined/empty properly)
      const currentCompany = post?.author?.company || "";
      const newCompany = company.trim();
      if (newCompany !== currentCompany) {
        updateData.company = newCompany || null;  // Empty string becomes null
      }
      
      // Check if job title changed
      const currentJobTitle = post?.author?.job_title || "";
      const newJobTitle = jobTitle.trim();
      if (newJobTitle !== currentJobTitle) {
        updateData.job_title = newJobTitle || null;  // Empty string becomes null
      }
      if (text.trim() && text.trim() !== (post?.text || "")) {
        updateData.text = text.trim();
      }
      if (category && category !== (post?.category || "")) {
        updateData.category = category || null;
      }

      // Check if there are any changes
      if (Object.keys(updateData).length === 0) {
        setError("No changes detected. Please modify at least one field.");
        return;
      }

      try {
        await axios.put(`http://127.0.0.1:8000/posts/${post.id}`, updateData);
        
        // Show success notification
        if (onSuccess) {
          onSuccess("Post updated successfully! ✓");
        }
        
        // Close form
        closeForm();
        
        // Refresh posts
        if (fetchPosts) {
          fetchPosts(false);
        }
      } catch (err) {
        console.error("Update post failed:", err);
        setError(err.response?.data?.detail || "Failed to update post. Please try again.");
      }
    } else {
      // Create mode - validate required fields
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
        
        // Show success notification
        if (onSuccess) {
          onSuccess("Post added successfully! ✓");
        }
        
        // Close form
        closeForm();
        
        // Refresh posts (pass true to reset to page 1 for new posts)
        if (fetchPosts) {
          fetchPosts(true);
        }
      } catch (err) {
        console.error("Add post failed:", err);
        setError(err.response?.data?.detail || "Failed to create post. Please try again.");
      }
    }
  };

  return (
    <div className="modal-overlay" onClick={closeForm}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <form onSubmit={handleSubmit}>
          <h2>{isEdit ? "Edit Post" : "Add New Post"}</h2>
          
          {error && (
            <div className="error-message">
              {error}
            </div>
          )}

          <div className="form-group">
            <label htmlFor="firstName">First Name {!isEdit && "*"}</label>
            <input
              type="text"
              id="firstName"
              value={firstName}
              onChange={(e) => setFirstName(e.target.value)}
              placeholder="Enter first name"
              required={!isEdit}
            />
          </div>

          <div className="form-group">
            <label htmlFor="lastName">Last Name {!isEdit && "*"}</label>
            <input
              type="text"
              id="lastName"
              value={lastName}
              onChange={(e) => setLastName(e.target.value)}
              placeholder="Enter last name"
              required={!isEdit}
            />
          </div>

          <div className="form-group">
            <label htmlFor="email">Email {!isEdit && "*"}</label>
            <input
              type="email"
              id="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Enter email address"
              required={!isEdit}
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
              <option value="Industry Insights">Industry Insights</option>
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="text">Post Text {!isEdit && "*"}</label>
            <textarea
              id="text"
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Enter post text..."
              required={!isEdit}
              rows={5}
            />
          </div>

          <div className="form-actions">
            <button type="button" onClick={closeForm}>Cancel</button>
            <button type="submit">{isEdit ? "Update Post" : "Add Post"}</button>
          </div>
        </form>
      </div>
    </div>
  );
}
