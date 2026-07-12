"use client";
import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import api from "@/lib/api";
import { useAuth } from "@/lib/store";
import { motion } from "framer-motion";
import { Clock, CheckCircle, AlertTriangle } from "lucide-react";

const STATUS_LABELS: Record<string, string> = {
  DRAFT: "Draft",
  MATCHING: "Finding freelancers...",
  ADVANCE_PENDING: "Awaiting your payment",
  IN_PROGRESS: "Work in progress",
  NEAR_COMPLETION_REQUESTED: "Freelancer says it's nearly done — review",
  NEAR_COMPLETION_APPROVED: "Nearly done — waiting for final delivery",
  COMPLETED_REQUESTED: "Freelancer has submitted — approve or request changes",
  REVISION_1: "Revision 1/3 requested",
  REVISION_2: "Revision 2/3 requested",
  REVISION_3: "Revision 3/3 requested",
  COMPLETED: "Processing final payment",
  CLOSED: "Done",
};

export default function ProjectDetail() {
  const { id } = useParams();
  const { user } = useAuth();
  const [project, setProject] = useState<any>(null);
  const [revisionNote, setRevisionNote] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadProject();
  }, [id]);

  const loadProject = async () => {
    try {
      const res = await api.get(`/projects/${id}`);
      setProject(res.data);
    } catch {}
    setLoading(false);
  };

  const action = async (endpoint: string, body?: any) => {
    try {
      await api.post(`/projects/${id}/${endpoint}`, body);
      loadProject();
    } catch (e: any) {
      alert(e.response?.data?.detail || "Error");
    }
  };

  if (loading || !project) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-2 border-amber-500 border-t-transparent" />
      </div>
    );
  }

  const isClient = user?.id === project.client_id;
  const isFreelancer = user?.id === project.assigned_freelancer_id;

  return (
    <div className="max-w-lg mx-auto px-6 py-10">
      <h1 className="text-2xl font-bold mb-1">{project.title}</h1>
      <p className="text-amber-400 text-sm mb-6">{STATUS_LABELS[project.status] || project.status}</p>

      <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 space-y-4 mb-6">
        {project.description && (
          <div>
            <label className="text-xs text-gray-500">Description</label>
            <p className="text-gray-300 text-sm">{project.description}</p>
          </div>
        )}
        {project.category && (
          <div>
            <label className="text-xs text-gray-500">Category</label>
            <p className="text-gray-300 text-sm">{project.category}</p>
          </div>
        )}
        <div className="flex gap-6">
          {project.budget && (
            <div>
              <label className="text-xs text-gray-500">Budget</label>
              <p className="text-gray-300 text-sm">₹{project.budget.toLocaleString()}</p>
            </div>
          )}
          {project.timeline_value && (
            <div>
              <label className="text-xs text-gray-500">Timeline</label>
              <p className="text-gray-300 text-sm">{project.timeline_value} {project.timeline_unit}</p>
            </div>
          )}
          {project.deadline && (
            <div>
              <label className="text-xs text-gray-500">Deadline</label>
              <p className="text-gray-300 text-sm flex items-center gap-1">
                <Clock className="w-3 h-3" /> {project.deadline}
              </p>
            </div>
          )}
        </div>
        {project.revision_count > 0 && (
          <div className="flex items-center gap-2 text-yellow-400 text-sm">
            <AlertTriangle className="w-4 h-4" />
            Revisions used: {project.revision_count}/3
          </div>
        )}
      </div>

      {/* Client actions */}
      {isClient && (
        <div className="space-y-3">
          {project.status === "NEAR_COMPLETION_REQUESTED" && (
            <div className="flex gap-3">
              <motion.button
                whileTap={{ scale: 0.95 }}
                onClick={() => action("approve-near-complete")}
                className="flex-1 bg-green-500/20 text-green-400 border border-green-500/30 py-3 rounded-xl font-medium"
              >
                Approve Near Complete
              </motion.button>
              <motion.button
                whileTap={{ scale: 0.95 }}
                onClick={() => action("reject-near-complete?reason=Not+ready+yet")}
                className="flex-1 bg-red-500/20 text-red-400 border border-red-500/30 py-3 rounded-xl font-medium"
              >
                Reject
              </motion.button>
            </div>
          )}

          {project.status === "COMPLETED_REQUESTED" && (
            <div className="space-y-3">
              <motion.button
                whileTap={{ scale: 0.95 }}
                onClick={() => action("approve-complete")}
                className="w-full bg-green-500/20 text-green-400 border border-green-500/30 py-3 rounded-xl font-medium"
              >
                <CheckCircle className="w-4 h-4 inline mr-2" />
                Approve & Pay Final 50%
              </motion.button>

              {project.revision_count < 3 && (
                <div>
                  <textarea
                    value={revisionNote}
                    onChange={(e) => setRevisionNote(e.target.value)}
                    placeholder="What needs to change?"
                    rows={2}
                    className="w-full bg-gray-900 border border-gray-700 rounded-xl px-4 py-3 text-white text-sm focus:outline-none focus:border-amber-500 transition resize-none mb-2"
                  />
                  <motion.button
                    whileTap={{ scale: 0.95 }}
                    onClick={() => action("request-revision", { note: revisionNote })}
                    disabled={!revisionNote.trim()}
                    className="w-full bg-yellow-500/20 text-yellow-400 border border-yellow-500/30 py-3 rounded-xl font-medium disabled:opacity-50"
                  >
                    Request Revision ({3 - project.revision_count} remaining)
                  </motion.button>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Freelancer actions */}
      {isFreelancer && (
        <div className="space-y-3">
          {project.status === "IN_PROGRESS" && (
            <motion.button
              whileTap={{ scale: 0.95 }}
              onClick={() => action("mark-near-complete")}
              className="w-full bg-amber-500/20 text-amber-400 border border-amber-500/30 py-3 rounded-xl font-medium"
            >
              Mark Near Complete
            </motion.button>
          )}
          {project.status === "NEAR_COMPLETION_APPROVED" && (
            <motion.button
              whileTap={{ scale: 0.95 }}
              onClick={() => action("mark-complete")}
              className="w-full bg-green-500/20 text-green-400 border border-green-500/30 py-3 rounded-xl font-medium"
            >
              Submit Final Delivery
            </motion.button>
          )}
        </div>
      )}
    </div>
  );
}
