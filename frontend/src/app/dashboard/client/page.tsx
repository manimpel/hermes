"use client";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/store";
import api from "@/lib/api";
import { motion } from "framer-motion";
import { Plus, ArrowRight, Clock, CheckCircle, AlertCircle } from "lucide-react";

const STATUS_COLORS: Record<string, string> = {
  DRAFT: "text-gray-400",
  MATCHING: "text-blue-400",
  ADVANCE_PENDING: "text-yellow-400",
  IN_PROGRESS: "text-amber-400",
  NEAR_COMPLETION_REQUESTED: "text-orange-400",
  NEAR_COMPLETION_APPROVED: "text-green-400",
  COMPLETED_REQUESTED: "text-green-400",
  COMPLETED: "text-green-500",
  CLOSED: "text-gray-500",
};

const STATUS_LABELS: Record<string, string> = {
  DRAFT: "Draft",
  MATCHING: "Finding freelancers...",
  ADVANCE_PENDING: "Awaiting payment",
  IN_PROGRESS: "In progress",
  NEAR_COMPLETION_REQUESTED: "Nearly done — review",
  NEAR_COMPLETION_APPROVED: "Nearly done — awaiting final",
  COMPLETED_REQUESTED: "Submitted — approve or revise",
  REVISION_1: "Revision 1/3",
  REVISION_2: "Revision 2/3",
  REVISION_3: "Revision 3/3",
  COMPLETED: "Final payment pending",
  CLOSED: "Done",
};

interface Project {
  id: string;
  title: string;
  status: string;
  assigned_freelancer_id: string | null;
  deadline: string | null;
  completed_at: string | null;
}

interface SwipeBatch {
  project_id: string;
  remaining: number;
}

export default function ClientDashboard() {
  const { user, fetchMe } = useAuth();
  const [activeProjects, setActiveProjects] = useState<Project[]>([]);
  const [pastProjects, setPastProjects] = useState<Project[]>([]);
  const [batches, setBatches] = useState<SwipeBatch[]>([]);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    fetchMe();
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    try {
      const res = await api.get("/dashboard/client");
      setActiveProjects(res.data.active_projects);
      setPastProjects(res.data.past_projects);
      setBatches(res.data.swipe_batches);
    } catch {}
    setLoading(false);
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
          <h1 className="text-2xl font-bold">Welcome, {user?.name || "Client"}</h1>
          <p className="text-gray-400 text-sm">Your project dashboard</p>
        </div>
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={() => router.push("/projects/new")}
          className="bg-gradient-to-r from-amber-500 to-orange-600 text-white font-semibold px-5 py-2.5 rounded-xl flex items-center gap-2 text-sm"
        >
          <Plus className="w-4 h-4" /> New Project
        </motion.button>
      </div>

      {/* Swipe batches */}
      {batches.filter((b) => b.remaining > 0).map((batch) => (
        <motion.div
          key={batch.project_id}
          whileHover={{ scale: 1.01 }}
          onClick={() => router.push(`/swipe/${batch.project_id}`)}
          className="bg-amber-500/10 border border-amber-500/30 rounded-xl p-4 mb-4 cursor-pointer"
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-amber-400">
              <AlertCircle className="w-4 h-4" />
              <span className="font-medium">{batch.remaining} matches ready to swipe</span>
            </div>
            <ArrowRight className="w-4 h-4 text-amber-400" />
          </div>
        </motion.div>
      ))}

      {/* Active projects */}
      <h2 className="text-lg font-semibold mb-3 mt-6">Active Projects</h2>
      {activeProjects.length === 0 ? (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 text-center text-gray-500">
          No active projects. Create one to get started.
        </div>
      ) : (
        <div className="space-y-3">
          {activeProjects.map((project) => (
            <motion.div
              key={project.id}
              whileHover={{ scale: 1.01 }}
              onClick={() => router.push(`/projects/${project.id}`)}
              className="bg-gray-900 border border-gray-800 rounded-xl p-4 cursor-pointer hover:border-gray-700 transition"
            >
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-semibold">{project.title}</h3>
                  <p className={`text-sm mt-1 ${STATUS_COLORS[project.status] || "text-gray-400"}`}>
                    {STATUS_LABELS[project.status] || project.status}
                  </p>
                </div>
                {project.deadline && (
                  <div className="flex items-center gap-1 text-gray-500 text-sm">
                    <Clock className="w-3 h-3" /> {project.deadline}
                  </div>
                )}
              </div>
            </motion.div>
          ))}
        </div>
      )}

      {/* Past projects */}
      {pastProjects.length > 0 && (
        <>
          <h2 className="text-lg font-semibold mb-3 mt-8">Completed</h2>
          <div className="space-y-3">
            {pastProjects.map((project) => (
              <div
                key={project.id}
                className="bg-gray-900 border border-gray-800 rounded-xl p-4 flex items-center justify-between"
              >
                <div>
                  <h3 className="font-semibold">{project.title}</h3>
                  <p className="text-sm text-gray-500">{project.completed_at}</p>
                </div>
                <CheckCircle className="w-5 h-5 text-green-500" />
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
