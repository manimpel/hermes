"use client";
import { useSearchParams } from "next/navigation";
import { Suspense } from "react";
import { motion } from "framer-motion";
import { Copy, Check } from "lucide-react";
import { useState } from "react";

const UPI_ID = "8655229505@upi";

function PaymentContent() {
  const params = useSearchParams();
  const amount = params.get("amount") || "0";
  const projectId = params.get("project_id") || "";
  const type = params.get("type") || "ADVANCE";
  const [copied, setCopied] = useState(false);

  const upiLink = `upi://pay?pa=${UPI_ID}&pn=Hermes&am=${amount}&cu=INR&tn=hermes_${projectId}_${type}`;

  const copyUpi = () => {
    navigator.clipboard.writeText(UPI_ID);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="flex items-center justify-center min-h-screen px-6">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-sm text-center"
      >
        <h1 className="text-2xl font-bold mb-2">Pay via UPI</h1>
        <p className="text-gray-400 text-sm mb-6">
          {type === "ADVANCE" ? "50% Advance" : "Final 50%"} Payment
        </p>

        <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6 mb-6">
          <div className="text-4xl font-bold text-amber-400 mb-4">
            ₹{parseFloat(amount).toLocaleString()}
          </div>

          {/* QR placeholder — generated via UPI deep link */}
          <div className="bg-white rounded-xl p-4 mb-4 inline-block">
            <img
              src={`https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=${encodeURIComponent(upiLink)}`}
              alt="UPI QR Code"
              width={200}
              height={200}
            />
          </div>

          <p className="text-gray-400 text-sm mb-3">Scan QR or pay to:</p>

          <div className="flex items-center justify-center gap-2 bg-gray-800 rounded-xl px-4 py-3">
            <span className="font-mono text-lg text-white">{UPI_ID}</span>
            <button onClick={copyUpi} className="text-amber-400 hover:text-amber-300">
              {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
            </button>
          </div>
        </div>

        <a
          href={upiLink}
          className="block w-full bg-gradient-to-r from-amber-500 to-orange-600 text-white font-semibold py-3 rounded-xl mb-3"
        >
          Open UPI App
        </a>

        <p className="text-gray-500 text-xs">
          After payment, the admin will verify and confirm your payment.
          You&apos;ll be notified once confirmed.
        </p>
      </motion.div>
    </div>
  );
}

export default function PaymentPage() {
  return (
    <Suspense fallback={<div className="flex items-center justify-center min-h-screen">Loading...</div>}>
      <PaymentContent />
    </Suspense>
  );
}
