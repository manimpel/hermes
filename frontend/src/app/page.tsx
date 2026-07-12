"use client";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { useAuth } from "@/lib/store";
import { motion } from "framer-motion";

export default function Home() {
  const { user, token, fetchMe } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (token) {
      fetchMe().then(() => {});
    }
  }, [token, fetchMe]);

  useEffect(() => {
    if (user) {
      if (!user.role) {
        router.push("/onboarding");
      } else if (user.role === "client" || user.role === "both") {
        router.push("/dashboard/client");
      } else {
        router.push("/dashboard/freelancer");
      }
    }
  }, [user, router]);

  return (
    <div className="flex flex-col items-center justify-center min-h-screen px-6">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="text-center max-w-lg"
      >
        <h1 className="text-6xl font-bold mb-4 bg-gradient-to-r from-amber-400 to-orange-500 bg-clip-text text-transparent">
          Hermes
        </h1>
        <p className="text-gray-400 text-lg mb-10">
          AI-powered freelance matchmaking. Swipe to find the perfect talent.
        </p>
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={() => router.push("/login")}
          className="bg-gradient-to-r from-amber-500 to-orange-600 text-white font-semibold px-8 py-4 rounded-2xl text-lg shadow-lg shadow-orange-500/20 hover:shadow-orange-500/40 transition-shadow"
        >
          Get Started
        </motion.button>
      </motion.div>
    </div>
  );
}
