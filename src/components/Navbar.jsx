import { useState } from "react";
import { Link } from "react-router-dom";
import "./Navbar.css";

export default function Navbar() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <nav className="navbar">
      <div className="navbar-container">
        {/* Brand Name */}
        <Link to="/" className="navbar-brand">
          Versatile Attendance System
        </Link>

        {/* Desktop Links */}
        <div className={`nav-links ${isOpen ? "active" : ""}`}>
          <Link to="/admin" onClick={() => setIsOpen(false)}>
            Admin Panel
          </Link>
        </div>

        {/* Hamburger Menu */}
        <div
          className={`hamburger ${isOpen ? "open" : ""}`}
          onClick={() => setIsOpen(!isOpen)}
        >
          <span></span>
          <span></span>
          <span></span>
        </div>
      </div>
    </nav>
  );
}
