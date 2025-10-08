import { Link } from "react-router-dom";

export default function AdminPage() {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-900 text-white">
      <h1 className="text-4xl font-bold mb-4">Admin Dashboard</h1>
      <p className="mb-6">Manage attendance records, user data, and more.</p>
      <Link
        to="/"
        className="bg-green-600 hover:bg-green-700 px-5 py-2 rounded-lg font-semibold"
      >
        Back to Home
      </Link>
    </div>
  );
}
