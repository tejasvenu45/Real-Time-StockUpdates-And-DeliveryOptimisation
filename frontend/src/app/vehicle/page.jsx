'use client';
import { useEffect, useState } from "react";
import { Plus, Trash2, Pencil, Truck } from "lucide-react";
import Navbar from "@/components/ui/navbar";
export default function VehiclePage() {
  const [vehicles, setVehicles] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [editingVehicle, setEditingVehicle] = useState(null);
  const [formData, setFormData] = useState({
    vehicle_id: "",
    license_plate: "",
    vehicle_type: "",
    max_weight_capacity: 0,
    max_volume_capacity: 0,
    status: "available"
  });

  const fetchVehicles = async () => {
    const res = await fetch("http://localhost:8001/api/v1/vehicles");
    const data = await res.json();
    setVehicles(data.data.items);
  };

  useEffect(() => {
    fetchVehicles();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    const url = editingVehicle
      ? `http://localhost:8001/api/v1/vehicles/${editingVehicle.vehicle_id}`
      : "http://localhost:8001/api/v1/vehicles";
    const method = editingVehicle ? "PUT" : "POST";

    const res = await fetch(url, {
      method,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(formData)
    });

    if (res.ok) {
      setShowForm(false);
      setEditingVehicle(null);
      setFormData({
        vehicle_id: "",
        license_plate: "",
        vehicle_type: "",
        max_weight_capacity: 0,
        max_volume_capacity: 0,
        status: "available"
      });
      fetchVehicles();
    }
  };

  const handleDelete = async (id) => {
    await fetch(`http://localhost:8001/api/v1/vehicles/${id}`, {
      method: "DELETE"
    });
    fetchVehicles();
  };

  const handleEdit = (vehicle) => {
    setFormData(vehicle);
    setEditingVehicle(vehicle);
    setShowForm(true);
  };

  return (
    <div>
      
     <Navbar/>
    <div className="p-6">
    
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <Truck className="text-blue-600" />
          <h2 className="text-xl font-semibold text-gray-800">Vehicle Management</h2>
        </div>
        <button
          onClick={() => {
            setEditingVehicle(null);
            setFormData({
              vehicle_id: "",
              license_plate: "",
              vehicle_type: "",
              max_weight_capacity: 0,
              max_volume_capacity: 0,
              status: "available"
            });
            setShowForm(!showForm);
          }}
          className="bg-blue-600 text-white px-4 py-2 rounded"
        >
          {showForm ? "Close" : "Add Vehicle"}
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleSubmit} className="grid grid-cols-2 gap-4 mb-6">
          <input
            className="input"
            type="text"
            placeholder="Vehicle ID"
            value={formData.vehicle_id}
            onChange={(e) => setFormData({ ...formData, vehicle_id: e.target.value })}
            disabled={editingVehicle !== null}
          />
          <input
            className="input"
            type="text"
            placeholder="License Plate"
            value={formData.license_plate}
            onChange={(e) => setFormData({ ...formData, license_plate: e.target.value })}
          />
          <input
            className="input"
            type="text"
            placeholder="Vehicle Type"
            value={formData.vehicle_type}
            onChange={(e) => setFormData({ ...formData, vehicle_type: e.target.value })}
          />
          <input
            className="input"
            type="number"
            placeholder="Max Weight Capacity"
            value={formData.max_weight_capacity}
            onChange={(e) => setFormData({ ...formData, max_weight_capacity: Number(e.target.value) })}
          />
          <input
            className="input"
            type="number"
            placeholder="Max Volume Capacity"
            value={formData.max_volume_capacity}
            onChange={(e) => setFormData({ ...formData, max_volume_capacity: Number(e.target.value) })}
          />
          <select
            className="input"
            value={formData.status}
            onChange={(e) => setFormData({ ...formData, status: e.target.value })}
          >
            <option value="available">Available</option>
            <option value="in_use">In Use</option>
            <option value="maintenance">Maintenance</option>
          </select>
          <button
            type="submit"
            className="col-span-2 bg-green-600 text-white rounded px-4 py-2"
          >
            {editingVehicle ? "Update Vehicle" : "Add Vehicle"}
          </button>
        </form>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {vehicles.map((v) => (
          <div key={v.vehicle_id} className="border p-4 rounded shadow hover:shadow-md transition">
            <h3 className="font-bold text-gray-800">{v.vehicle_id}</h3>
            <p className="text-sm text-gray-600">Plate: {v.license_plate}</p>
            <p className="text-sm text-gray-600">Type: {v.vehicle_type}</p>
            <p className="text-sm text-gray-600">Weight: {v.max_weight_capacity} kg</p>
            <p className="text-sm text-gray-600">Volume: {v.max_volume_capacity} m³</p>
            <p className="text-sm text-gray-600">Status: {v.status}</p>
            <div className="flex gap-2 mt-2">
              <button
                onClick={() => handleEdit(v)}
                className="text-blue-500 hover:underline text-sm flex items-center gap-1"
              >
                <Pencil size={14} /> Edit
              </button>
              <button
                onClick={() => handleDelete(v.vehicle_id)}
                className="text-red-500 hover:underline text-sm flex items-center gap-1"
              >
                <Trash2 size={14} /> Delete
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
    </div>
  );
}
