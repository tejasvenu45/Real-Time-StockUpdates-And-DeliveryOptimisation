"use client";

import { useState, useEffect } from "react";
import { RefreshCcw, Truck, Zap, ScrollText } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import Navbar from "@/components/ui/navbar";
export default function ProcessPage() {
  const [requests, setRequests] = useState([]);
  const [assignments, setAssignments] = useState(null);
  const [aiPrompt, setAiPrompt] = useState("");
  const [loading, setLoading] = useState(false);

  const fetchRestockRequests = async () => {
    const res = await fetch("http://localhost:8001/api/v1/restock-requests");
    const data = await res.json();
    const sorted = data.data.items.sort(
      (a, b) => new Date(b.created_at) - new Date(a.created_at)
    );
    setRequests(sorted);
  };

  const handleProcessFulfillment = async () => {
    setLoading(true);
    await fetch("http://localhost:8001/api/v1/kafka/process-fulfillment", {
      method: "POST",
    });
    setLoading(false);
  };

  const handleFetchAssignments = async () => {
    const res = await fetch("http://localhost:8001/api/v1/kafka/vehicle-assignments");
    const data = await res.json();
    setAssignments(data.data);
  };

  const handleFetchAiPrompt = async () => {
    const res = await fetch("http://localhost:8001/api/v1/ai/generate-prompt");
    const data = await res.text();
    setAiPrompt(data);
  };

  useEffect(() => {
    fetchRestockRequests();
    const interval = setInterval(fetchRestockRequests, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div>
        <Navbar/>   
    <div className="p-6 space-y-8">

     
      {/* Navbar */}
      <nav className="bg-gray-900 text-white p-4 rounded-lg shadow-md">
        <div className="text-2xl font-bold">📦 Fulfillment Control Center</div>
      </nav>

      {/* Restock Requests Section */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <RefreshCcw className="text-purple-600" size={20} />
            <h2 className="text-xl font-semibold text-gray-800">
              Real-Time Restock Requests
            </h2>
          </div>
          <div className="flex gap-3">
            <Button
              onClick={handleProcessFulfillment}
              disabled={loading}
              className="bg-green-600 hover:bg-green-700"
            >
              🚚 Process These Requests
            </Button>
            <Button
              onClick={handleFetchAssignments}
              className="bg-blue-600 hover:bg-blue-700"
            >
              🚛 View Greedy Vehicle Allotments
            </Button>
          </div>
        </div>

        {requests.length === 0 ? (
          <p className="text-center text-gray-500">No restock requests yet.</p>
        ) : (
          <div className="space-y-2 max-h-[400px] overflow-y-auto">
            {requests.map((req) => (
              <div
                key={req._id}
                className="p-4 border border-gray-200 rounded-md shadow-sm hover:shadow transition"
              >
                <div className="flex justify-between text-sm">
                  <span className="font-medium text-gray-700">
                    {req.store_id} → {req.product_id}
                  </span>
                  <span className="text-xs text-gray-400">
                    {new Date(req.created_at).toLocaleString()}
                  </span>
                </div>
                <p className="text-sm mt-1 text-gray-600">
                  <strong>Qty:</strong> {req.requested_quantity} | <strong>Priority:</strong> {req.priority} | <strong>Status:</strong> {req.status}
                </p>
                <p className="text-xs mt-1 text-gray-500 italic">{req.reason}</p>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Vehicle Assignments Section */}
      {assignments && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center gap-2 mb-4">
            <Truck className="text-blue-600" size={20} />
            <h2 className="text-xl font-semibold text-gray-800">
              Vehicle Assignment Results
            </h2>
          </div>
          {assignments.assignments.length === 0 ? (
            <p className="text-gray-500">No assignments yet.</p>
          ) : (
            <div className="space-y-4">
              {assignments.assignments.map((assign) => (
                <div
                  key={assign.request_id}
                  className="border border-gray-200 rounded-lg p-4 shadow-sm"
                >
                  <div className="text-sm text-gray-700">
                    📍 <strong>{assign.store_id}</strong> | Request: <strong>{assign.request_id}</strong>
                  </div>
                  <div className="text-xs text-gray-600 mt-1">
                    Volume Needed: <strong>{assign.total_volume_needed.toFixed(2)}</strong> | Volume Assigned: <strong>{assign.total_volume_assigned.toFixed(2)}</strong>
                  </div>
                  <div className="text-xs text-gray-600 mt-1">
                    Vehicles Used: {assign.vehicles_required}
                  </div>
                  <ul className="text-xs text-gray-500 mt-2 list-disc ml-4">
                    {assign.vehicles_assigned.map((v) => (
                      <li key={v.vehicle_id}>
                        🚚 {v.vehicle_id}: Assigned {v.assigned_volume.toFixed(2)}, Leftover: {v.leftover_volume.toFixed(2)}
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* AI Prompt Section */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <ScrollText className="text-gray-700" size={20} />
            <h2 className="text-xl font-semibold text-gray-800">AI Optimization Prompt</h2>
          </div>
          <Button onClick={handleFetchAiPrompt} className="bg-gray-700 hover:bg-gray-800 text-white">
            ✨ Regenerate Prompt
          </Button>
        </div>
        <pre className="whitespace-pre-wrap text-sm text-gray-700 bg-gray-50 p-4 rounded-md overflow-auto max-h-[400px]">
          {aiPrompt || "Click above to load AI prompt."}
        </pre>
      </div>
    </div>
    </div>
  );
}
