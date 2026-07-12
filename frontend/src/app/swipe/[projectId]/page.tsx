"use client";
import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import api from "@/lib/api";
import { motion, AnimatePresence } from "framer-motion";
import { MapPin, Star, ExternalLink, X, Heart } from "lucide-react";

interface Profile {
  id: string;
  user_id: string;
  headline: string | null;
  summary: string | null;
  location: string | null;
  skills: string[];
  interest_areas: string[];
  portfolio_links: string[];
  profile_photo_url: string | null;
  avg_rating: number | null;
  completed_count: number | null;
}

export default function SwipePage() {
  const { projectId } = useParams();
  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [current, setCurrent] = useState(0);
  const [loading, setLoading] = useState(true);
  const [swiping, setSwiping] = useState(false);
  const [direction, setDirection] = useState<"left" | "right" | null>(null);

  useEffect(() => {
    loadBatch();
  }, [projectId]);

  const loadBatch = async () => {
    try {
      const res = await api.get(`/swipe/batch/${projectId}`);
      setProfiles(res.data.profiles);
    } catch {}
    setLoading(false);
  };

  const handleSwipe = async (dir: "left" | "right") => {
    if (swiping || current >= profiles.length) return;
    setSwiping(true);
    setDirection(dir);

    const profile = profiles[current];
    await api.post("/swipe", {
      project_id: projectId,
      freelancer_id: profile.user_id,
      direction: dir,
    });

    setTimeout(() => {
      setCurrent((c) => c + 1);
      setDirection(null);
      setSwiping(false);
    }, 300);
  };

  const handleSelect = async () => {
    const profile = profiles[current - 1]; // last right-swiped
    try {
      const res = await api.post(`/swipe/select/${profile.user_id}?project_id=${projectId}`);
      const order = res.data.order;
      window.location.href = `/payment?amount=${order.amount}&project_id=${projectId}&type=ADVANCE`;
    } catch (e: any) {
      alert(e.response?.data?.detail || "Error selecting freelancer");
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-2 border-amber-500 border-t-transparent" />
      </div>
    );
  }

  if (profiles.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen px-6 text-center">
        <h2 className="text-2xl font-bold mb-2">No matches today</h2>
        <p className="text-gray-400">Check back tomorrow for fresh matches</p>
      </div>
    );
  }

  const profile = profiles[current];

  if (current >= profiles.length) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen px-6 text-center">
        <h2 className="text-2xl font-bold mb-2">All caught up!</h2>
        <p className="text-gray-400 mb-6">You&apos;ve swiped through today&apos;s batch</p>
        <button
          onClick={handleSelect}
          className="bg-gradient-to-r from-amber-500 to-orange-600 text-white font-semibold px-8 py-3 rounded-xl"
        >
          Select a Freelancer
        </button>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-screen px-6 py-8">
      <div className="text-sm text-gray-500 mb-4">
        {current + 1} / {profiles.length}
      </div>

      <div className="relative w-[340px] h-[520px]">
        <AnimatePresence mode="wait">
          <motion.div
            key={profile.user_id}
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{
              opacity: 1,
              scale: 1,
              x: direction === "left" ? -300 : direction === "right" ? 300 : 0,
              rotate: direction === "left" ? -15 : direction === "right" ? 15 : 0,
            }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="absolute inset-0 bg-gray-900 border border-gray-800 rounded-2xl p-6 flex flex-col shadow-2xl"
          >
            {/* Avatar */}
            <div className="w-20 h-20 rounded-full bg-gradient-to-br from-amber-400 to-orange-500 flex items-center justify-center text-2xl font-bold mx-auto mb-4">
              {(profile.headline || "?")[0].toUpperCase()}
            </div>

            {/* Info */}
            <h2 className="text-xl font-bold text-center">{profile.headline || "Freelancer"}</h2>
            {profile.location && (
              <div className="flex items-center justify-center gap-1 text-gray-400 text-sm mt-1">
                <MapPin className="w-3 h-3" /> {profile.location}
              </div>
            )}

            {profile.avg_rating && (
              <div className="flex items-center justify-center gap-1 text-amber-400 text-sm mt-1">
                <Star className="w-3 h-3 fill-current" /> {profile.avg_rating.toFixed(1)}
                <span className="text-gray-500">({profile.completed_count} projects)</span>
              </div>
            )}

            {/* Skills */}
            <div className="flex flex-wrap gap-1.5 mt-4 justify-center">
              {(profile.skills || []).slice(0, 6).map((skill) => (
                <span key={skill} className="px-2 py-0.5 bg-gray-800 rounded-full text-xs text-gray-300">
                  {skill}
                </span>
              ))}
            </div>

            {/* Summary */}
            {profile.summary && (
              <p className="text-gray-400 text-sm mt-4 flex-1 overflow-hidden line-clamp-4">
                {profile.summary}
              </p>
            )}

            {/* Portfolio links */}
            {profile.portfolio_links && profile.portfolio_links.length > 0 && (
              <div className="flex gap-2 mt-4 justify-center">
                {profile.portfolio_links.map((link, i) => (
                  <a
                    key={i}
                    href={link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-amber-400 hover:text-amber-300 text-sm flex items-center gap-1"
                  >
                    <ExternalLink className="w-3 h-3" /> Portfolio {i + 1}
                  </a>
                ))}
              </div>
            )}
          </motion.div>
        </AnimatePresence>
      </div>

      {/* Swipe buttons */}
      <div className="flex gap-6 mt-8">
        <motion.button
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.9 }}
          onClick={() => handleSwipe("left")}
          disabled={swiping}
          className="w-16 h-16 rounded-full border-2 border-red-500/50 flex items-center justify-center hover:bg-red-500/10 transition"
        >
          <X className="w-7 h-7 text-red-400" />
        </motion.button>
        <motion.button
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.9 }}
          onClick={() => handleSwipe("right")}
          disabled={swiping}
          className="w-16 h-16 rounded-full border-2 border-green-500/50 flex items-center justify-center hover:bg-green-500/10 transition"
        >
          <Heart className="w-7 h-7 text-green-400" />
        </motion.button>
      </div>
    </div>
  );
}
