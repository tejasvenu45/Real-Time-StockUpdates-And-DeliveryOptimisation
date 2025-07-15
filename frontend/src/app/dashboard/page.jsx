'use client';

import { useState, useEffect } from 'react';
import { Plus, Edit, Trash2, Package, ShoppingCart, Warehouse } from 'lucide-react';
import { RefreshCcw } from "lucide-react";
import Navbar from '@/components/ui/navbar';
const Dashboard = () => {
  const [requests, setRequests] = useState([]);
  const [products, setProducts] = useState([]);
  const [stores, setStores] = useState([]);
  const [loading, setLoading] = useState(true);
  const [storesLoading, setStoresLoading] = useState(true);
  const [showAddProduct, setShowAddProduct] = useState(false);
  const [showAddStore, setShowAddStore] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [selectedStore, setSelectedStore] = useState(null);
  const [showProductDetails, setShowProductDetails] = useState(false);
  const [showStoreDetails, setShowStoreDetails] = useState(false);
  const [inventory, setInventory] = useState([]);
  const [selectedInventory, setSelectedInventory] = useState(null);
  const [showFormInventory, setFormInventory] = useState(false);
  const [formInventory, setformInventory] = useState({
    store_id: "",
    product_id: "",
    current_stock: 0,
    reserved_stock: 0,
    available_stock: 0,
    reorder_threshold: 10,
    warning_threshold: 15,
    critical_threshold: 5,
    max_capacity: 100,
    location: ""
  });
    useEffect(() => {
    fetch("http://localhost:8001/api/v1/inventory")
      .then((res) => res.json())
      .then((data) => setInventory(data.data.items))
      .catch((err) => console.error("Error fetching inventory:", err));
  }, []);


    useEffect(() => {
    const fetchRequests = () => {
      fetch("http://localhost:8001/api/v1/restock-requests")
        .then((res) => res.json())
        .then((data) => {
          const sorted = data.data.items.sort(
            (a, b) => new Date(b.created_at) - new Date(a.created_at)
          );
          setRequests(sorted);
        })
        .catch((err) => console.error("Error fetching restock requests:", err));
    };

    fetchRequests(); // Initial fetch
    const interval = setInterval(fetchRequests, 5000); // Poll every 5 seconds

    return () => clearInterval(interval); // Cleanup
  }, []);


  const handleSubmitInventory = async (e) => {
    e.preventDefault();
    try {
      const res = await fetch("http://localhost:8001/api/v1/inventory", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formInventory),
      });
      if (!res.ok) throw new Error("Failed to add inventory");
      const data = await res.json();
      setInventory((prev) => [...prev, { ...formInventory, _id: data.data._id }]);
      setFormInventory(false);
      setFormInventoryState({
        store_id: "",
        product_id: "",
        current_stock: 0,
        reserved_stock: 0,
        available_stock: 0,
        reorder_threshold: 10,
        warning_threshold: 15,
        critical_threshold: 5,
        max_capacity: 100,
        location: ""
      });
    } catch (err) {
      console.error("Error submitting inventory:", err);
    }
  };


  const [formData, setFormData] = useState({
    product_id: '',
    name: '',
    description: '',
    category: '',
    price: '',
    weight: '',
    dimensions: {
      length: '',
      width: '',
      height: ''
    },
    barcode: '',
    supplier_id: '',
    shelf_life_days: '',
    storage_requirements: {
      temperature: '',
      humidity: ''
    }
  });
  const [storeFormData, setStoreFormData] = useState({
    store_id: '',
    name: '',
    address: {
      street: '',
      city: '',
      state: '',
      postal_code: '',
      country: '',
      coordinates: {
        latitude: '',
        longitude: ''
      }
    },
    manager_name: '',
    phone: '',
    email: '',
    operating_hours: {
      monday: '',
      tuesday: '',
      wednesday: '',
      thursday: '',
      friday: '',
      saturday: '',
      sunday: ''
    },
    capacity: {
      max_weight: '',
      max_volume: ''
    }
  });

  const categories = [
    'electronics',
    'grocery',
    'clothing',
    'home-garden',
    'health-beauty',
    'sports-outdoors',
    'books-media'
  ];

  const temperatureOptions = ['room', 'cold', 'frozen', 'cool', 'warm'];
  const humidityOptions = ['low', 'medium', 'high', 'controlled'];

  // Fetch products
  const fetchProducts = async () => {
    try {
      const response = await fetch('http://localhost:8001/api/v1/products');
      const data = await response.json();
      if (data.success) {
        setProducts(data.data.items);
      }
    } catch (error) {
      console.error('Error fetching products:', error);
    } finally {
      setLoading(false);
    }
  };

  // Fetch stores
  const fetchStores = async () => {
    try {
      const response = await fetch('http://localhost:8001/api/v1/stores');
      const data = await response.json();
      if (data.success) {
        setStores(data.data.items);
      }
    } catch (error) {
      console.error('Error fetching stores:', error);
    } finally {
      setStoresLoading(false);
    }
  };

  // Add new product
  const addProduct = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch('http://localhost:8001/api/v1/products', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ...formData,
          price: parseFloat(formData.price),
          weight: parseFloat(formData.weight),
          shelf_life_days: parseInt(formData.shelf_life_days),
          dimensions: {
            length: parseFloat(formData.dimensions.length),
            width: parseFloat(formData.dimensions.width),
            height: parseFloat(formData.dimensions.height)
          }
        }),
      });
      
      if (response.ok) {
        setShowAddProduct(false);
        resetForm();
        fetchProducts();
      }
    } catch (error) {
      console.error('Error adding product:', error);
    }
  };

  // Add new store
  const addStore = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch('http://localhost:8001/api/v1/stores', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ...storeFormData,
          address: {
            ...storeFormData.address,
            coordinates: {
              latitude: parseFloat(storeFormData.address.coordinates.latitude),
              longitude: parseFloat(storeFormData.address.coordinates.longitude)
            }
          },
          capacity: {
            max_weight: parseFloat(storeFormData.capacity.max_weight),
            max_volume: parseFloat(storeFormData.capacity.max_volume)
          }
        }),
      });
      
      if (response.ok) {
        setShowAddStore(false);
        resetStoreForm();
        fetchStores();
      }
    } catch (error) {
      console.error('Error adding store:', error);
    }
  };

  const resetForm = () => {
    setFormData({
      product_id: '',
      name: '',
      description: '',
      category: '',
      price: '',
      weight: '',
      dimensions: {
        length: '',
        width: '',
        height: ''
      },
      barcode: '',
      supplier_id: '',
      shelf_life_days: '',
      storage_requirements: {
        temperature: '',
        humidity: ''
      }
    });
  };

  const resetStoreForm = () => {
    setStoreFormData({
      store_id: '',
      name: '',
      address: {
        street: '',
        city: '',
        state: '',
        postal_code: '',
        country: '',
        coordinates: {
          latitude: '',
          longitude: ''
        }
      },
      manager_name: '',
      phone: '',
      email: '',
      operating_hours: {
        monday: '',
        tuesday: '',
        wednesday: '',
        thursday: '',
        friday: '',
        saturday: '',
        sunday: ''
      },
      capacity: {
        max_weight: '',
        max_volume: ''
      }
    });
  };

  useEffect(() => {
    fetchProducts();
    fetchStores();
  }, []);

  return (
    <div>  
         <Navbar/>

     <div className="min-h-screen bg-gray-50">
    
      {/* Navbar */}
      <nav className="bg-blue-600 text-white p-4 shadow-lg">
        <h1 className="text-2xl font-bold">Walmart Dashboard</h1>
      </nav>

      {/* Main Content */}
      <div className="p-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Products Section */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex justify-between items-center mb-4">
              <div className="flex items-center gap-2">
                <Package className="text-blue-600" size={24} />
                <h2 className="text-xl font-semibold text-gray-800">Products</h2>
              </div>
              <button
                onClick={() => setShowAddProduct(true)}
                className="bg-blue-600 hover:bg-blue-700 text-white p-2 rounded-lg transition-colors"
              >
                <Plus size={20} />
              </button>
            </div>

            {/* Products List */}
            <div className="space-y-3">
              {loading ? (
                <div className="text-center py-8">Loading products...</div>
              ) : products.length === 0 ? (
                <div className="text-center py-8 text-gray-500">No products found</div>
              ) : (
                products.map((product) => (
                  <div
                    key={product._id}
                    className="border rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
                    onClick={() => {
                      setSelectedProduct(product);
                      setShowProductDetails(true);
                    }}
                  >
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <h3 className="font-medium text-gray-800">{product.name}</h3>
                        <p className="text-sm text-gray-600 capitalize">{product.category}</p>
                        <p className="text-lg font-semibold text-green-600">${product.price}</p>
                      </div>
                      <div className="flex gap-2">
                        <button className="text-blue-600 hover:text-blue-800 p-1">
                          <Edit size={16} />
                        </button>
                        <button className="text-red-600 hover:text-red-800 p-1">
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Stores Section */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex justify-between items-center mb-4">
              <div className="flex items-center gap-2">
                <ShoppingCart className="text-green-600" size={24} />
                <h2 className="text-xl font-semibold text-gray-800">Stores</h2>
              </div>
              <button
                onClick={() => setShowAddStore(true)}
                className="bg-green-600 hover:bg-green-700 text-white p-2 rounded-lg transition-colors"
              >
                <Plus size={20} />
              </button>
            </div>

            {/* Stores List */}
            <div className="space-y-3">
              {storesLoading ? (
                <div className="text-center py-8">Loading stores...</div>
              ) : stores.length === 0 ? (
                <div className="text-center py-8 text-gray-500">No stores found</div>
              ) : (
                stores.map((store) => (
                  <div
                    key={store._id}
                    className="border rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
                    onClick={() => {
                      setSelectedStore(store);
                      setShowStoreDetails(true);
                    }}
                  >
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <h3 className="font-medium text-gray-800">{store.name}</h3>
                        <p className="text-sm text-gray-600">{store.address.city}, {store.address.state}</p>
                        <p className="text-sm text-gray-500">Manager: {store.manager_name}</p>
                      </div>
                      <div className="flex gap-2">
                        <button className="text-green-600 hover:text-green-800 p-1">
                          <Edit size={16} />
                        </button>
                        <button className="text-red-600 hover:text-red-800 p-1">
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Inventory Section (Placeholder) */}
          {/* <div className="bg-white rounded-lg shadow-md p-6">
                <div className="flex items-center gap-2 mb-4">
                <Warehouse className="text-orange-600" size={24} />
                <h2 className="text-xl font-semibold text-gray-800">Inventory</h2>
                </div>
                <div className="text-center py-8 text-gray-500">
                Inventory section coming soon...
                </div>
          </div> */}
              <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Warehouse className="text-orange-600" size={24} />
          <h2 className="text-xl font-semibold text-gray-800">Inventory</h2>
        </div>
        <button onClick={() => setFormInventory(!showFormInventory)}>
          {showFormInventory ? <X className="text-red-600" /> : <Plus className="text-green-600" />}
        </button>
      </div>

      {showFormInventory && (
        <form onSubmit={handleSubmitInventory} className="grid grid-cols-2 gap-4 mb-6">
          <input type="text" placeholder="Store ID" className="input" value={formInventory.store_id} onChange={(e) => setFormInventoryState({ ...formInventory, store_id: e.target.value })} />
          <input type="text" placeholder="Product ID" className="input" value={formInventory.product_id} onChange={(e) => setFormInventoryState({ ...formInventory, product_id: e.target.value })} />
          <input type="number" placeholder="Current Stock" className="input" value={formInventory.current_stock} onChange={(e) => setFormInventoryState({ ...formInventory, current_stock: Number(e.target.value) })} />
          <input type="number" placeholder="Reserved Stock" className="input" value={formInventory.reserved_stock} onChange={(e) => setFormInventoryState({ ...formInventory, reserved_stock: Number(e.target.value) })} />
          <input type="number" placeholder="Available Stock" className="input" value={formInventory.available_stock} onChange={(e) => setFormInventoryState({ ...formInventory, available_stock: Number(e.target.value) })} />
          <input type="number" placeholder="Reorder Threshold" className="input" value={formInventory.reorder_threshold} onChange={(e) => setFormInventoryState({ ...formInventory, reorder_threshold: Number(e.target.value) })} />
          <input type="number" placeholder="Warning Threshold" className="input" value={formInventory.warning_threshold} onChange={(e) => setFormInventoryState({ ...formInventory, warning_threshold: Number(e.target.value) })} />
          <input type="number" placeholder="Critical Threshold" className="input" value={formInventory.critical_threshold} onChange={(e) => setFormInventoryState({ ...formInventory, critical_threshold: Number(e.target.value) })} />
          <input type="number" placeholder="Max Capacity" className="input" value={formInventory.max_capacity} onChange={(e) => setFormInventoryState({ ...formInventory, max_capacity: Number(e.target.value) })} />
          <input type="text" placeholder="Location" className="input" value={formInventory.location} onChange={(e) => setFormInventoryState({ ...formInventory, location: e.target.value })} />
          <button type="submit" className="col-span-2 bg-blue-600 text-white rounded px-4 py-2">Add Inventory</button>
        </form>
      )}

      <div className="space-y-2">
        {inventory.length === 0 ? (
          <p className="text-center py-8 text-gray-500">No inventory available.</p>
        ) : (
          inventory.map((inv) => (
            <div key={inv._id} className="border p-4 rounded hover:bg-gray-50 cursor-pointer" onClick={() => setSelectedInventory(inv)}>
              <p className="font-semibold">{inv.store_id} - {inv.product_id}</p>
              <p>Stock: {inv.current_stock}</p>
            </div>
          ))
        )}
      </div>

      {selectedInventory && (
        <div className="mt-6 border-t pt-4">
          <h3 className="text-lg font-semibold mb-2">Inventory Details</h3>
          <pre className="text-sm text-gray-700 bg-gray-100 p-3 rounded overflow-x-auto">
            {JSON.stringify(selectedInventory, null, 2)}
          </pre>
        </div>
      )}
    </div>
        </div>
      </div>

      {/* Add Store Modal */}
      {showAddStore && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-4xl max-h-[90vh] overflow-y-auto">
            <h3 className="text-xl font-semibold mb-4">Add New Store</h3>
            <form onSubmit={addStore} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Store ID</label>
                  <input
                    type="text"
                    required
                    value={storeFormData.store_id}
                    onChange={(e) => setStoreFormData({...storeFormData, store_id: e.target.value})}
                    className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-green-500 focus:border-green-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Store Name</label>
                  <input
                    type="text"
                    required
                    value={storeFormData.name}
                    onChange={(e) => setStoreFormData({...storeFormData, name: e.target.value})}
                    className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-green-500 focus:border-green-500"
                  />
                </div>
              </div>

              <div>
                <h4 className="text-lg font-medium mb-2">Address Information</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-1">Street</label>
                    <input
                      type="text"
                      required
                      value={storeFormData.address.street}
                      onChange={(e) => setStoreFormData({...storeFormData, address: {...storeFormData.address, street: e.target.value}})}
                      className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-green-500 focus:border-green-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">City</label>
                    <input
                      type="text"
                      required
                      value={storeFormData.address.city}
                      onChange={(e) => setStoreFormData({...storeFormData, address: {...storeFormData.address, city: e.target.value}})}
                      className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-green-500 focus:border-green-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">State</label>
                    <input
                      type="text"
                      required
                      value={storeFormData.address.state}
                      onChange={(e) => setStoreFormData({...storeFormData, address: {...storeFormData.address, state: e.target.value}})}
                      className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-green-500 focus:border-green-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Postal Code</label>
                    <input
                      type="text"
                      required
                      value={storeFormData.address.postal_code}
                      onChange={(e) => setStoreFormData({...storeFormData, address: {...storeFormData.address, postal_code: e.target.value}})}
                      className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-green-500 focus:border-green-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Country</label>
                    <input
                      type="text"
                      required
                      value={storeFormData.address.country}
                      onChange={(e) => setStoreFormData({...storeFormData, address: {...storeFormData.address, country: e.target.value}})}
                      className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-green-500 focus:border-green-500"
                    />
                  </div>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                  <div>
                    <label className="block text-sm font-medium mb-1">Latitude</label>
                    <input
                      type="number"
                      step="0.000001"
                      required
                      value={storeFormData.address.coordinates.latitude}
                      onChange={(e) => setStoreFormData({...storeFormData, address: {...storeFormData.address, coordinates: {...storeFormData.address.coordinates, latitude: e.target.value}}})}
                      className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-green-500 focus:border-green-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Longitude</label>
                    <input
                      type="number"
                      step="0.000001"
                      required
                      value={storeFormData.address.coordinates.longitude}
                      onChange={(e) => setStoreFormData({...storeFormData, address: {...storeFormData.address, coordinates: {...storeFormData.address.coordinates, longitude: e.target.value}}})}
                      className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-green-500 focus:border-green-500"
                    />
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Manager Name</label>
                  <input
                    type="text"
                    required
                    value={storeFormData.manager_name}
                    onChange={(e) => setStoreFormData({...storeFormData, manager_name: e.target.value})}
                    className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-green-500 focus:border-green-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Phone</label>
                  <input
                    type="tel"
                    required
                    value={storeFormData.phone}
                    onChange={(e) => setStoreFormData({...storeFormData, phone: e.target.value})}
                    className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-green-500 focus:border-green-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Email</label>
                  <input
                    type="email"
                    required
                    value={storeFormData.email}
                    onChange={(e) => setStoreFormData({...storeFormData, email: e.target.value})}
                    className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-green-500 focus:border-green-500"
                  />
                </div>
              </div>

              <div>
                <h4 className="text-lg font-medium mb-2">Operating Hours</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {Object.keys(storeFormData.operating_hours).map((day) => (
                    <div key={day}>
                      <label className="block text-sm font-medium mb-1 capitalize">{day}</label>
                      <input
                        type="text"
                        required
                        placeholder="9:00-21:00"
                        value={storeFormData.operating_hours[day]}
                        onChange={(e) => setStoreFormData({...storeFormData, operating_hours: {...storeFormData.operating_hours, [day]: e.target.value}})}
                        className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-green-500 focus:border-green-500"
                      />
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <h4 className="text-lg font-medium mb-2">Capacity</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-1">Max Weight (kg)</label>
                    <input
                      type="number"
                      required
                      value={storeFormData.capacity.max_weight}
                      onChange={(e) => setStoreFormData({...storeFormData, capacity: {...storeFormData.capacity, max_weight: e.target.value}})}
                      className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-green-500 focus:border-green-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Max Volume (m³)</label>
                    <input
                      type="number"
                      required
                      value={storeFormData.capacity.max_volume}
                      onChange={(e) => setStoreFormData({...storeFormData, capacity: {...storeFormData.capacity, max_volume: e.target.value}})}
                      className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-green-500 focus:border-green-500"
                    />
                  </div>
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-4">
                <button
                  type="button"
                  onClick={() => {
                    setShowAddStore(false);
                    resetStoreForm();
                  }}
                  className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors"
                >
                  Add Store
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Add Product Modal */}
      {showAddProduct && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <h3 className="text-xl font-semibold mb-4">Add New Product</h3>
            <form onSubmit={addProduct} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Product ID</label>
                  <input
                    type="text"
                    required
                    value={formData.product_id}
                    onChange={(e) => setFormData({...formData, product_id: e.target.value})}
                    className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Name</label>
                  <input
                    type="text"
                    required
                    value={formData.name}
                    onChange={(e) => setFormData({...formData, name: e.target.value})}
                    className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Description</label>
                <textarea
                  required
                  value={formData.description}
                  onChange={(e) => setFormData({...formData, description: e.target.value})}
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  rows="3"
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Category</label>
                  <select
                    required
                    value={formData.category}
                    onChange={(e) => setFormData({...formData, category: e.target.value})}
                    className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="">Select category</option>
                    {categories.map(cat => (
                      <option key={cat} value={cat}>{cat}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Price</label>
                  <input
                    type="number"
                    step="0.01"
                    required
                    value={formData.price}
                    onChange={(e) => setFormData({...formData, price: e.target.value})}
                    className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Weight (kg)</label>
                  <input
                    type="number"
                    step="0.001"
                    required
                    value={formData.weight}
                    onChange={(e) => setFormData({...formData, weight: e.target.value})}
                    className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Barcode</label>
                  <input
                    type="text"
                    required
                    value={formData.barcode}
                    onChange={(e) => setFormData({...formData, barcode: e.target.value})}
                    className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Dimensions (cm)</label>
                <div className="grid grid-cols-3 gap-2">
                  <input
                    type="number"
                    step="0.01"
                    required
                    placeholder="Length"
                    value={formData.dimensions.length}
                    onChange={(e) => setFormData({...formData, dimensions: {...formData.dimensions, length: e.target.value}})}
                    className="p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                  <input
                    type="number"
                    step="0.01"
                    required
                    placeholder="Width"
                    value={formData.dimensions.width}
                    onChange={(e) => setFormData({...formData, dimensions: {...formData.dimensions, width: e.target.value}})}
                    className="p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                  <input
                    type="number"
                    step="0.01"
                    required
                    placeholder="Height"
                    value={formData.dimensions.height}
                    onChange={(e) => setFormData({...formData, dimensions: {...formData.dimensions, height: e.target.value}})}
                    className="p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Supplier ID</label>
                  <input
                    type="text"
                    required
                    value={formData.supplier_id}
                    onChange={(e) => setFormData({...formData, supplier_id: e.target.value})}
                    className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Shelf Life (days)</label>
                  <input
                    type="number"
                    required
                    value={formData.shelf_life_days}
                    onChange={(e) => setFormData({...formData, shelf_life_days: e.target.value})}
                    className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Storage Requirements</label>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                  <select
                    required
                    value={formData.storage_requirements.temperature}
                    onChange={(e) => setFormData({...formData, storage_requirements: {...formData.storage_requirements, temperature: e.target.value}})}
                    className="p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="">Temperature</option>
                    {temperatureOptions.map(temp => (
                      <option key={temp} value={temp}>{temp}</option>
                    ))}
                  </select>
                  <select
                    required
                    value={formData.storage_requirements.humidity}
                    onChange={(e) => setFormData({...formData, storage_requirements: {...formData.storage_requirements, humidity: e.target.value}})}
                    className="p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="">Humidity</option>
                    {humidityOptions.map(humidity => (
                      <option key={humidity} value={humidity}>{humidity}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-4">
                <button
                  type="button"
                  onClick={() => {
                    setShowAddProduct(false);
                    resetForm();
                  }}
                  className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                >
                  Add Product
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Store Details Modal */}
      {showStoreDetails && selectedStore && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-3xl max-h-[90vh] overflow-y-auto">
            <h3 className="text-xl font-semibold mb-4">Store Details</h3>
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div><strong>Store ID:</strong> {selectedStore.store_id}</div>
                <div><strong>Name:</strong> {selectedStore.name}</div>
                <div><strong>Manager:</strong> {selectedStore.manager_name}</div>
                <div><strong>Phone:</strong> {selectedStore.phone}</div>
                <div><strong>Email:</strong> {selectedStore.email}</div>
                <div><strong>Status:</strong> <span className="capitalize">{selectedStore.status}</span></div>
              </div>
              
              <div>
                <h4 className="font-semibold mb-2">Address</h4>
                <div className="bg-gray-50 p-3 rounded-md">
                  <p>{selectedStore.address.street}</p>
                  <p>{selectedStore.address.city}, {selectedStore.address.state} {selectedStore.address.postal_code}</p>
                  <p>{selectedStore.address.country}</p>
                  <p className="text-sm text-gray-600 mt-1">
                    Coordinates: {selectedStore.address.coordinates.latitude}, {selectedStore.address.coordinates.longitude}
                  </p>
                </div>
              </div>

              <div>
                <h4 className="font-semibold mb-2">Operating Hours</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                  {Object.entries(selectedStore.operating_hours).map(([day, hours]) => (
                    <div key={day} className="flex justify-between bg-gray-50 p-2 rounded">
                      <span className="capitalize font-medium">{day}:</span>
                      <span>{hours}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <h4 className="font-semibold mb-2">Capacity</h4>
                <div className="bg-gray-50 p-3 rounded-md">
                  <p><strong>Max Weight:</strong> {selectedStore.capacity.max_weight} kg</p>
                  <p><strong>Max Volume:</strong> {selectedStore.capacity.max_volume} m³</p>
                </div>
              </div>
            </div>
            <div className="flex justify-end mt-6">
              <button
                onClick={() => setShowStoreDetails(false)}
                className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Product Details Modal */}
      {showProductDetails && selectedProduct && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <h3 className="text-xl font-semibold mb-4">Product Details</h3>
            <div className="space-y-3">
              <div><strong>Product ID:</strong> {selectedProduct.product_id}</div>
              <div><strong>Name:</strong> {selectedProduct.name}</div>
              <div><strong>Description:</strong> {selectedProduct.description}</div>
              <div><strong>Category:</strong> {selectedProduct.category}</div>
              <div><strong>Price:</strong> ${selectedProduct.price}</div>
              <div><strong>Weight:</strong> {selectedProduct.weight} kg</div>
              <div><strong>Dimensions:</strong> {selectedProduct.dimensions.length} × {selectedProduct.dimensions.width} × {selectedProduct.dimensions.height} cm</div>
              <div><strong>Barcode:</strong> {selectedProduct.barcode}</div>
              <div><strong>Supplier ID:</strong> {selectedProduct.supplier_id}</div>
              <div><strong>Shelf Life:</strong> {selectedProduct.shelf_life_days} days</div>
              <div><strong>Storage:</strong> {selectedProduct.storage_requirements.temperature} temperature, {selectedProduct.storage_requirements.humidity} humidity</div>
            </div>
            <div className="flex justify-end mt-6">
              <button
                onClick={() => setShowProductDetails(false)}
                className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

        <div className="bg-white rounded-lg shadow-md p-6 mt-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <RefreshCcw className="text-purple-600" size={20} />
          <h2 className="text-xl font-semibold text-gray-800">Real-Time Restock Requests</h2>
        </div>
        <span className="text-xs text-gray-400">Auto-refreshes every 5s</span>
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
    </div>
    </div>

  );
};

export default Dashboard;