"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import api from "@/lib/api";
import { motion } from "framer-motion";

const CATEGORIES = [
  "UI/UX Design", "Frontend Development", "Backend Development", "Full-Stack",
  "Mobile Development", "Data Science", "Copywriting", "Content Writing",
  "Graphic Design", "Video Editing", "SEO", "Digital Marketing",
  "WordPress", "Shopify", "Product Management", "3D Design", "Illustration",
];

export default function NewProjectPage() {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [category, setCategory] = useState("");
  const [budget, setBudget] = useState("");
  const [timelineValue, setTimelineValue] = useState("");
  const [timelineUnit, setTimelineUnit] = useState("weeks");
  const [brief, setBrief] = useState("");
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleCreate = async () => {
    setLoading(true);
    try {
      const res = await api.post("/projects/", {
        title,
        description,
        category,
        budget: budget ? parseFloat(budget) : null,
        timeline_value: timelineValue ? parseInt(timelineValue) : null,
        timeline_unit: timelineUnit || null,
        written_brief: brief || null,
      });
      const projectId = res.data.id;

      // Auto-publish
      await api.post(`/projects/${projectId}/publish`);
      router.push(`/swipe/${projectId}`);
    } catch (e: any) {
      alert(e.response?.data?.detail || "Error creating project");
    }
    setLoading(false);
  };

  return (
    <div className="max-w-lg mx-auto px-6 py-10">
      <h1 className="text-2xl font-bold mb-2">Create Project</h1>
      <p className="text-gray-400 text-sm mb-8">Describe what you need — Hermes will find the best matches</p>

      <div className="space-y-5">
        <div>
          <label className="text-sm text-gray-400 mb-1 block">Project Title</label>
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="e.g. Redesign our landing page"
            className="w-full bg-gray-900 border border-gray-700 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-amber-500 transition"
          />
        </div>

        <div>
          <label className="text-sm text-gray-400 mb-1 block">Category</label>
          <select
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            className="w-full bg-gray-900 border border-gray-700 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-amber-500 transition"
          >
            <option value="">Select category...</option>
            {CATEGORIES.map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="text-sm text-gray-400 mb-1 block">Description</label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="What do you need done?"
            rows={3}
            className="w-full bg-gray-900 border border-gray-700 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-amber-500 transition resize-none"
          />
        </div>

        <div>
          <label className="text-sm text-gray-400 mb-1 block">Detailed Brief</label>
          <textarea
            value={brief}
            onChange={(e) => setBrief(e.target.value)}
            placeholder="Detailed requirements, references, expectations..."
            rows={4}
            className="w-full bg-gray-900 border border-gray-700 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-amber-500 transition resize-none"
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="text-sm text-gray-400 mb-1 block">Budget (₹)</label>
            <input
              type="number"
              value={budget}
              onChange={(e) => setBudget(e.target.value)}
              placeholder="50000"
              className="w-full bg-gray-900 border border-gray-700 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-amber-500 transition"
            />
          </div>
          <div>
            <label className="text-sm text-gray-400 mb-1 block">Timeline</label>
            <div className="flex gap-2">
              <input
                type="number"
                value={timelineValue}
                onChange={(e) => setTimelineValue(e.target.value)}
                placeholder="2"
                className="w-20 bg-gray-900 border border-gray-700 rounded-xl px-3 py-3 text-white focus:outline-none focus:border-amber-500 transition"
              />
              <select
                value={timelineUnit}
                onChange={(e) => setTimelineUnit(e.target.value)}
                className="flex-1 bg-gray-900 border border-gray-700 rounded-xl px-3 py-3 text-white focus:outline-none focus:border-amber-500 transition"
              >
                <option value="days">Days</option>
                <option value="weeks">Weeks</option>
                <option value="months">Months</option>
              </select>
            </div>
          </div>
        </div>

        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={handleCreate}
          disabled={loading || !title.trim()}
          className="w-full bg-gradient-to-r from-amber-500 to-orange-600 text-white font-semibold py-3 rounded-xl disabled:opacity-50 mt-4"
        >
          {loading ? "Creating & Finding Matches..." : "Create & Find Matches"}
        </motion.button>
      </div>
    </div>
  );
}
