"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/store";
import { motion } from "framer-motion";

export default function LoginPage() {
  const [phone, setPhone] = useState("+91");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const router = useRouter();

  const handleLogin = async () => {
    setError("");
    setLoading(true);
    try {
      const isNew = await login(phone);
      router.push(isNew ? "/onboarding" : "/");
    } catch {
      setError("Login failed. Check your number and try again.");
    }
    setLoading(false);
  };

  return (
    <div className="flex items-center justify-center min-h-screen px-6">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-sm"
      >
        <h1 className="text-3xl font-bold mb-2">Welcome to Hermes</h1>
        <p className="text-gray-400 mb-8">Enter your phone number to continue</p>

        <div className="space-y-4">
          <input
            type="tel"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            placeholder="+919876543210"
            className="w-full bg-gray-900 border border-gray-700 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-amber-500 transition"
            onKeyDown={(e) => e.key === "Enter" && handleLogin()}
          />
          <button
            onClick={handleLogin}
            disabled={loading || phone.length < 10}
            className="w-full bg-gradient-to-r from-amber-500 to-orange-600 text-white font-semibold py-3 rounded-xl disabled:opacity-50 transition"
          >
            {loading ? "Signing in..." : "Continue"}
          </button>
        </div>

        {error && <p className="text-red-400 text-sm mt-4">{error}</p>}
      </motion.div>
    </div>
  );
}
