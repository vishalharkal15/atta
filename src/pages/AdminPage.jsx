import { useState } from "react";
import { useNavigate } from "react-router-dom";

export default function AdminPage() {
  const [password, setPassword] = useState("");
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const navigate = useNavigate();

  async function handleSubmit(e) {
    e.preventDefault();

    const response = await fetch("http://localhost:5000/api/verify", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ password }),
    });

    const data = await response.json();
    if (data.success) {
      setIsAuthenticated(true);
    } else {
      alert("Invalid password!");
    }
  }

  if (!isAuthenticated) {
    return (
      <div style={styles.fullPage}>
        <div style={styles.loginBox}>
          <h2 style={styles.title}>Admin Login</h2>
          <form onSubmit={handleSubmit} style={styles.form}>
            <input
              type="password"
              placeholder="Enter Admin Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              style={styles.input}
              required
            />
            <button type="submit" style={styles.button}>
              Login
            </button>
          </form>
        </div>
      </div>
    );
  }

  // After login
  return (
    <div style={styles.fullPage}>
      <div style={styles.dashboardBox}>
        <h1 style={styles.heading}>Admin Dashboard</h1>
        <p style={styles.description}>
          Manage attendance records, user data, and more.
        </p>
        <button onClick={() => navigate("/")} style={styles.backButton}>
          Back to Home
        </button>
      </div>
    </div>
  );
}

// ✅ Fixed Fullscreen Styles
const styles = {
  fullPage: {
    width: "100vw",
    height: "100vh",
    margin: 0,
    padding: 0,
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    background: "linear-gradient(135deg, #0f172a, #1e293b, #111827)",
    boxSizing: "border-box",
    overflow: "hidden",
  },
  loginBox: {
    width: "90%",
    maxWidth: "400px",
    background: "rgba(255, 255, 255, 0.05)",
    padding: "40px 30px",
    borderRadius: "12px",
    textAlign: "center",
    boxShadow: "0 0 25px rgba(0, 0, 0, 0.5)",
  },
  title: {
    fontSize: "2rem",
    color: "#38bdf8",
    fontWeight: "bold",
    marginBottom: "1rem",
  },
  form: {
    display: "flex",
    flexDirection: "column",
    gap: "15px",
  },
  input: {
    width: "90%",
    padding: "12px 15px",
    borderRadius: "8px",
    border: "1px solid #334155",
    backgroundColor: "#1e293b",
    color: "white",
    fontSize: "1rem",
    outline: "none",
  },
  button: {
    backgroundColor: "#38bdf8",
    border: "none",
    borderRadius: "8px",
    padding: "12px 15px",
    fontSize: "1rem",
    fontWeight: "600",
    cursor: "pointer",
    color: "white",
    transition: "all 0.3s ease",
  },
  dashboardBox: {
    width: "90%",
    maxWidth: "600px",
    background: "rgba(255, 255, 255, 0.08)",
    padding: "50px",
    borderRadius: "16px",
    textAlign: "center",
    boxShadow: "0 0 30px rgba(0, 0, 0, 0.4)",
  },
  heading: {
    fontSize: "2.5rem",
    fontWeight: "bold",
    marginBottom: "1rem",
    color: "#22c55e",
  },
  description: {
    fontSize: "1.1rem",
    color: "#d1d5db",
    marginBottom: "2rem",
  },
  backButton: {
    backgroundColor: "#22c55e",
    border: "none",
    borderRadius: "8px",
    padding: "12px 20px",
    fontSize: "1rem",
    fontWeight: "600",
    cursor: "pointer",
    color: "white",
    transition: "all 0.3s ease",
  },
};
