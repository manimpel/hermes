"use client";
import { useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/store";
import api from "@/lib/api";
import { motion } from "framer-motion";
import { Upload, Plus, X } from "lucide-react";

const INTEREST_TAGS = [
  "UI/UX Design", "Frontend Development", "Backend Development", "Full-Stack",
  "Mobile Development", "Data Science", "Machine Learning", "DevOps",
  "Copywriting", "Content Writing", "Graphic Design", "Video Editing",
  "SEO", "Digital Marketing", "Photography", "3D Design", "Illustration",
  "WordPress", "Shopify", "Product Management",
];

export default function FreelancerOnboarding() {
  const [step, setStep] = useState(1);
  const [linkedinFile, setLinkedinFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [headline, setHeadline] = useState("");
  const [summary, setSummary] = useState("");
  const [location, setLocation] = useState("");
  const [portfolioLinks, setPortfolioLinks] = useState<string[]>([""]);
  const [selectedAreas, setSelectedAreas] = useState<string[]>([]);
  const [customArea, setCustomArea] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);
  const router = useRouter();
  const { user } = useAuth();

  const handleLinkedinUpload = async () => {
    if (!linkedinFile) return;
    setUploading(true);
    const formData = new FormData();
    formData.append("file", linkedinFile);
    try {
      await api.post("/freelancer/linkedin-upload", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
    } catch {}
    setUploading(false);
    setStep(2);
  };

  const handleFinish = async () => {
    try {
      await api.post("/freelancer/profile", {
        headline, summary, location, availability: true,
      });
      if (portfolioLinks.filter(Boolean).length > 0) {
        await api.post("/freelancer/portfolio-links", portfolioLinks.filter(Boolean));
      }
      if (selectedAreas.length > 0) {
        await api.put("/freelancer/interest-areas", selectedAreas);
      }
      router.push("/dashboard/freelancer");
    } catch {}
  };

  const toggleArea = (area: string) => {
    setSelectedAreas((prev) =>
      prev.includes(area) ? prev.filter((a) => a !== area) : [...prev, area]
    );
  };

  const addCustomArea = () => {
    if (customArea.trim() && !selectedAreas.includes(customArea.trim())) {
      setSelectedAreas([...selectedAreas, customArea.trim()]);
      setCustomArea("");
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen px-6 py-12">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-lg"
      >
        {/* Step indicator */}
        <div className="flex gap-2 mb-8">
          {[1, 2, 3].map((s) => (
            <div
              key={s}
              className={`h-1 flex-1 rounded-full transition ${
                s <= step ? "bg-amber-500" : "bg-gray-800"
              }`}
            />
          ))}
        </div>

        {step === 1 && (
          <div className="space-y-6">
            <div>
              <h1 className="text-2xl font-bold mb-2">Upload LinkedIn Profile</h1>
              <p className="text-gray-400 text-sm">
                Save your LinkedIn page as HTML and upload it. Hermes AI will extract your info.
              </p>
            </div>
            <div
              onClick={() => fileRef.current?.click()}
              className="border-2 border-dashed border-gray-700 hover:border-amber-500 rounded-xl p-8 text-center cursor-pointer transition"
            >
              <Upload className="w-10 h-10 text-gray-500 mx-auto mb-3" />
              <p className="text-gray-400">
                {linkedinFile ? linkedinFile.name : "Click to upload HTML file"}
              </p>
              <input
                ref={fileRef}
                type="file"
                accept=".html,.htm"
                className="hidden"
                onChange={(e) => setLinkedinFile(e.target.files?.[0] || null)}
              />
            </div>
            <div className="flex gap-3">
              <button
                onClick={handleLinkedinUpload}
                disabled={!linkedinFile || uploading}
                className="flex-1 bg-gradient-to-r from-amber-500 to-orange-600 text-white font-semibold py-3 rounded-xl disabled:opacity-50"
              >
                {uploading ? "Uploading..." : "Upload & Parse"}
              </button>
              <button
                onClick={() => setStep(2)}
                className="px-6 py-3 border border-gray-700 rounded-xl text-gray-400 hover:text-white transition"
              >
                Skip
              </button>
            </div>
          </div>
        )}

        {step === 2 && (
          <div className="space-y-6">
            <h1 className="text-2xl font-bold">Your Profile</h1>
            <div className="space-y-4">
              <div>
                <label className="text-sm text-gray-400 mb-1 block">Headline</label>
                <input
                  value={headline}
                  onChange={(e) => setHeadline(e.target.value)}
                  placeholder="e.g. Senior UI/UX Designer"
                  className="w-full bg-gray-900 border border-gray-700 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-amber-500 transition"
                />
              </div>
              <div>
                <label className="text-sm text-gray-400 mb-1 block">Summary</label>
                <textarea
                  value={summary}
                  onChange={(e) => setSummary(e.target.value)}
                  placeholder="Brief intro about your expertise..."
                  rows={3}
                  className="w-full bg-gray-900 border border-gray-700 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-amber-500 transition resize-none"
                />
              </div>
              <div>
                <label className="text-sm text-gray-400 mb-1 block">Location</label>
                <input
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                  placeholder="e.g. Mumbai, India"
                  className="w-full bg-gray-900 border border-gray-700 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-amber-500 transition"
                />
              </div>
              <div>
                <label className="text-sm text-gray-400 mb-1 block">Portfolio Links (max 3)</label>
                {portfolioLinks.map((link, i) => (
                  <div key={i} className="flex gap-2 mb-2">
                    <input
                      value={link}
                      onChange={(e) => {
                        const updated = [...portfolioLinks];
                        updated[i] = e.target.value;
                        setPortfolioLinks(updated);
                      }}
                      placeholder="https://..."
                      className="flex-1 bg-gray-900 border border-gray-700 rounded-xl px-4 py-2 text-white text-sm focus:outline-none focus:border-amber-500 transition"
                    />
                    {portfolioLinks.length > 1 && (
                      <button
                        onClick={() => setPortfolioLinks(portfolioLinks.filter((_, j) => j !== i))}
                        className="text-gray-500 hover:text-red-400"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                ))}
                {portfolioLinks.length < 3 && (
                  <button
                    onClick={() => setPortfolioLinks([...portfolioLinks, ""])}
                    className="text-amber-400 text-sm flex items-center gap-1 mt-1"
                  >
                    <Plus className="w-3 h-3" /> Add link
                  </button>
                )}
              </div>
            </div>
            <button
              onClick={() => setStep(3)}
              className="w-full bg-gradient-to-r from-amber-500 to-orange-600 text-white font-semibold py-3 rounded-xl"
            >
              Continue
            </button>
          </div>
        )}

        {step === 3 && (
          <div className="space-y-6">
            <div>
              <h1 className="text-2xl font-bold mb-2">Interest Areas</h1>
              <p className="text-gray-400 text-sm">Select what you want to work on</p>
            </div>
            <div className="flex flex-wrap gap-2">
              {INTEREST_TAGS.map((tag) => (
                <button
                  key={tag}
                  onClick={() => toggleArea(tag)}
                  className={`px-3 py-1.5 rounded-full text-sm border transition ${
                    selectedAreas.includes(tag)
                      ? "bg-amber-500/20 border-amber-500 text-amber-400"
                      : "border-gray-700 text-gray-400 hover:border-gray-500"
                  }`}
                >
                  {tag}
                </button>
              ))}
            </div>
            <div className="flex gap-2">
              <input
                value={customArea}
                onChange={(e) => setCustomArea(e.target.value)}
                placeholder="Add custom..."
                className="flex-1 bg-gray-900 border border-gray-700 rounded-xl px-4 py-2 text-white text-sm focus:outline-none focus:border-amber-500 transition"
                onKeyDown={(e) => e.key === "Enter" && addCustomArea()}
              />
              <button onClick={addCustomArea} className="text-amber-400 px-3">
                <Plus className="w-5 h-5" />
              </button>
            </div>
            <button
              onClick={handleFinish}
              className="w-full bg-gradient-to-r from-amber-500 to-orange-600 text-white font-semibold py-3 rounded-xl"
            >
              Finish Setup
            </button>
          </div>
        )}
      </motion.div>
    </div>
  );
}
