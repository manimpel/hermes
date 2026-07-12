"use client";
import { useState, useEffect } from "react";
import { useAuth } from "@/lib/store";
import api from "@/lib/api";
import { motion } from "framer-motion";
import { Briefcase, IndianRupee, Star, ToggleLeft, ToggleRight } from "lucide-react";

export default function FreelancerDashboard() {
  const { user, fetchMe } = useAuth();
  const [dashboard, setDashboard] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchMe();
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    try {
      const res = await api.get("/dashboard/freelancer");
      setDashboard(res.data);
    } catch {}
    setLoading(false);
  };

  const toggleAvailability = async () => {
    const current = dashboard?.availability;
    await api.put(`/freelancer/availability?available=${!current}`);
    setDashboard({ ...dashboard, availability: !current });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-2 border-amber-500 border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto px-6 py-10">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold">Hi, {user?.name || "Freelancer"}</h1>
          <p className="text-gray-400 text-sm">Your freelancer dashboard</p>
        </div>
        <button
          onClick={toggleAvailability}
          className="flex items-center gap-2 text-sm"
        >
          {dashboard?.availability ? (
            <ToggleRight className="w-8 h-8 text-green-400" />
          ) : (
            <ToggleLeft className="w-8 h-8 text-gray-500" />
          )}
          <span className={dashboard?.availability ? "text-green-400" : "text-gray-500"}>
            {dashboard?.availability ? "Available" : "Unavailable"}
          </span>
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4 mb-8">
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 text-center">
          <Briefcase className="w-5 h-5 text-amber-400 mx-auto mb-2" />
          <div className="text-2xl font-bold">{dashboard?.completed_count || 0}</div>
          <div className="text-xs text-gray-500">Projects</div>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 text-center">
          <Star className="w-5 h-5 text-amber-400 mx-auto mb-2" />
          <div className="text-2xl font-bold">
            {dashboard?.avg_rating ? dashboard.avg_rating.toFixed(1) : "—"}
          </div>
          <div className="text-xs text-gray-500">Rating</div>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 text-center">
          <IndianRupee className="w-5 h-5 text-amber-400 mx-auto mb-2" />
          <div className="text-2xl font-bold">
            {dashboard?.total_earnings ? `₹${dashboard.total_earnings.toLocaleString()}` : "₹0"}
          </div>
          <div className="text-xs text-gray-500">Earned</div>
        </div>
      </div>

      {/* Current project */}
      {dashboard?.current_project ? (
        <div className="mb-8">
          <h2 className="text-lg font-semibold mb-3">Current Project</h2>
          <div className="bg-gray-900 border border-amber-500/30 rounded-xl p-5">
            <h3 className="font-bold text-lg">{dashboard.current_project.title}</h3>
            <div className="flex items-center gap-4 mt-2 text-sm text-gray-400">
              <span className="text-amber-400">{dashboard.current_project.status}</span>
              {dashboard.current_project.deadline && (
                <span>Deadline: {dashboard.current_project.deadline}</span>
              )}
              <span>Revisions: {dashboard.current_project.revision_count}/3</span>
            </div>
            <div className="flex gap-3 mt-4">
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={async () => {
                  try {
                    await api.post(`/projects/${dashboard.current_project.id}/mark-near-complete`);
                    loadDashboard();
                  } catch (e: any) {
                    alert(e.response?.data?.detail || "Error");
                  }
                }}
                className="bg-amber-500/20 text-amber-400 border border-amber-500/30 px-4 py-2 rounded-lg text-sm font-medium"
              >
                Mark Near Complete
              </motion.button>
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={async () => {
                  try {
                    await api.post(`/projects/${dashboard.current_project.id}/mark-complete`);
                    loadDashboard();
                  } catch (e: any) {
                    alert(e.response?.data?.detail || "Error");
                  }
                }}
                className="bg-green-500/20 text-green-400 border border-green-500/30 px-4 py-2 rounded-lg text-sm font-medium"
              >
                Mark Complete
              </motion.button>
            </div>
          </div>
        </div>
      ) : (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 text-center text-gray-500 mb-8">
          No active project. Keep your availability on to receive matches.
        </div>
      )}

      {/* Past projects */}
      {dashboard?.past_projects?.length > 0 && (
        <div>
          <h2 className="text-lg font-semibold mb-3">Past Projects</h2>
          <div className="space-y-3">
            {dashboard.past_projects.map((p: any) => (
              <div
                key={p.id}
                className="bg-gray-900 border border-gray-800 rounded-xl p-4 flex justify-between items-center"
              >
                <div>
                  <h3 className="font-medium">{p.title}</h3>
                  <p className="text-xs text-gray-500">{p.completed_at}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
