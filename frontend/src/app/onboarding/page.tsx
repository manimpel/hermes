"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/store";
import { motion } from "framer-motion";
import { User, Briefcase, Users } from "lucide-react";

const roles = [
  { id: "freelancer", label: "I want to work", desc: "Find projects that match your skills", icon: User },
  { id: "client", label: "I want to hire", desc: "Find perfect freelancers for your projects", icon: Briefcase },
  { id: "both", label: "Both", desc: "Hire and work on projects", icon: Users },
];

export default function OnboardingPage() {
  const [name, setName] = useState("");
  const [selectedRole, setSelectedRole] = useState("");
  const [step, setStep] = useState<"name" | "role">("name");
  const [loading, setLoading] = useState(false);
  const { updateUser } = useAuth();
  const router = useRouter();

  const handleNameSubmit = () => {
    if (name.trim()) setStep("role");
  };

  const handleRoleSelect = async (role: string) => {
    setSelectedRole(role);
    setLoading(true);
    await updateUser({ name: name.trim(), role });
    setLoading(false);
    if (role === "freelancer") {
      router.push("/onboarding/freelancer");
    } else if (role === "client") {
      router.push("/dashboard/client");
    } else {
      router.push("/onboarding/freelancer");
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen px-6">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-md"
      >
        {step === "name" ? (
          <div className="space-y-6">
            <div>
              <h1 className="text-3xl font-bold mb-2">What&apos;s your name?</h1>
              <p className="text-gray-400">Let&apos;s set up your Hermes profile</p>
            </div>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Your full name"
              className="w-full bg-gray-900 border border-gray-700 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-amber-500 transition"
              onKeyDown={(e) => e.key === "Enter" && handleNameSubmit()}
            />
            <button
              onClick={handleNameSubmit}
              disabled={!name.trim()}
              className="w-full bg-gradient-to-r from-amber-500 to-orange-600 text-white font-semibold py-3 rounded-xl disabled:opacity-50 transition"
            >
              Continue
            </button>
          </div>
        ) : (
          <div className="space-y-6">
            <div>
              <h1 className="text-3xl font-bold mb-2">Hi, {name}!</h1>
              <p className="text-gray-400">How do you want to use Hermes?</p>
            </div>
            <div className="space-y-3">
              {roles.map((role) => (
                <motion.button
                  key={role.id}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => handleRoleSelect(role.id)}
                  disabled={loading}
                  className="w-full bg-gray-900 border border-gray-700 hover:border-amber-500 rounded-xl p-4 text-left flex items-center gap-4 transition disabled:opacity-50"
                >
                  <div className="bg-gray-800 rounded-lg p-3">
                    <role.icon className="w-6 h-6 text-amber-400" />
                  </div>
                  <div>
                    <div className="font-semibold">{role.label}</div>
                    <div className="text-sm text-gray-400">{role.desc}</div>
                  </div>
                </motion.button>
              ))}
            </div>
          </div>
        )}
      </motion.div>
    </div>
  );
}
