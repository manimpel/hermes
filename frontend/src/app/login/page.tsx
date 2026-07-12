"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/store";
import { motion } from "framer-motion";

export default function LoginPage() {
  const [phone, setPhone] = useState("+91");
  const [otp, setOtp] = useState("");
  const [step, setStep] = useState<"phone" | "otp">("phone");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { sendOtp, verifyOtp } = useAuth();
  const router = useRouter();

  const handleSendOtp = async () => {
    setError("");
    setLoading(true);
    try {
      await sendOtp(phone);
      setStep("otp");
    } catch {
      setError("Failed to send OTP. Check your number.");
    }
    setLoading(false);
  };

  const handleVerify = async () => {
    setError("");
    setLoading(true);
    try {
      const isNew = await verifyOtp(phone, otp);
      router.push(isNew ? "/onboarding" : "/");
    } catch {
      setError("Invalid OTP. Try again.");
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
        <p className="text-gray-400 mb-8">Sign in with your phone number</p>

        {step === "phone" ? (
          <div className="space-y-4">
            <input
              type="tel"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              placeholder="+919876543210"
              className="w-full bg-gray-900 border border-gray-700 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-amber-500 transition"
            />
            <button
              onClick={handleSendOtp}
              disabled={loading || phone.length < 10}
              className="w-full bg-gradient-to-r from-amber-500 to-orange-600 text-white font-semibold py-3 rounded-xl disabled:opacity-50 transition"
            >
              {loading ? "Sending..." : "Send OTP"}
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            <p className="text-sm text-gray-400">
              OTP has been generated. Contact the Hermes admin to get your code.
            </p>
            <input
              type="text"
              value={otp}
              onChange={(e) => setOtp(e.target.value)}
              placeholder="Enter 6-digit OTP"
              maxLength={6}
              className="w-full bg-gray-900 border border-gray-700 rounded-xl px-4 py-3 text-white tracking-widest text-center text-xl focus:outline-none focus:border-amber-500 transition"
            />
            <button
              onClick={handleVerify}
              disabled={loading || otp.length !== 6}
              className="w-full bg-gradient-to-r from-amber-500 to-orange-600 text-white font-semibold py-3 rounded-xl disabled:opacity-50 transition"
            >
              {loading ? "Verifying..." : "Verify OTP"}
            </button>
            <button
              onClick={() => { setStep("phone"); setOtp(""); }}
              className="w-full text-gray-400 text-sm hover:text-white transition"
            >
              ← Change number
            </button>
          </div>
        )}

        {error && <p className="text-red-400 text-sm mt-4">{error}</p>}
      </motion.div>
    </div>
  );
}
