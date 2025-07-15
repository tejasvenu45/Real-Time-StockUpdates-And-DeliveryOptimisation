'use client';

import { useEffect, useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import Navbar from "@/components/ui/navbar";
export default function StoreSalesPage() {
  const [inventory, setInventory] = useState([]);
  const [products, setProducts] = useState([]);
  const [stores, setStores] = useState([]);
  const [selectedStore, setSelectedStore] = useState(null);
  const [visibleProducts, setVisibleProducts] = useState([]);
  const [showModal, setShowModal] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [cart, setCart] = useState([]);
  const [saleDetails, setSaleDetails] = useState({
    quantity: 1,
    discount: "0.00",
    tax: "0.00",
    payment_method: "credit_card",
    cashier_id: "CASHIER001",
    customer_id: "CUST001",
  });

  useEffect(() => {
    fetch("http://localhost:8001/api/v1/inventory")
      .then(res => res.json())
      .then(data => {
        setInventory(data.data.items);
        const uniqueStores = [...new Set(data.data.items.map(i => i.store_id))];
        setStores(uniqueStores);
      });

    fetch("http://localhost:8001/api/v1/products")
      .then(res => res.json())
      .then(data => setProducts(data.data.items));
  }, []);

  const handleStoreClick = (storeId) => {
    setSelectedStore(storeId);
    const productIds = inventory.filter(i => i.store_id === storeId).map(i => i.product_id);
    const storeProducts = products.filter(p => productIds.includes(p.product_id));
    setVisibleProducts(storeProducts);
  };

  const openProductModal = (product) => {
    setSelectedProduct(product);
    setShowModal(true);
  };

  const addToCart = () => {
    setCart([...cart, {
      store_id: selectedStore,
      product_id: selectedProduct.product_id,
      quantity: saleDetails.quantity,
      unit_price: selectedProduct.price,
      discount: saleDetails.discount,
      tax: saleDetails.tax,
      payment_method: saleDetails.payment_method,
      cashier_id: saleDetails.cashier_id,
      customer_id: saleDetails.customer_id,
    }]);
    setShowModal(false);
    setSaleDetails({ ...saleDetails, quantity: 1, discount: "0.00", tax: "0.00" });
  };

  const submitSales = async () => {
    for (const sale of cart) {
      await fetch("http://localhost:8001/api/v1/sales", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(sale)
      });
    }
    alert("Sales submitted successfully!");
    setCart([]);
  };

  return (
    <div><Navbar/>
    <div className="p-6 bg-gray-100 min-h-screen">
        
      <h1 className="text-2xl font-bold mb-4 text-gray-800">Store Sales</h1>

      {/* Store List */}
      <div className="flex flex-wrap gap-4 mb-6">
        {stores.map(store => (
          <Card
            key={store}
            onClick={() => handleStoreClick(store)}
            className={`cursor-pointer w-40 p-4 text-center shadow-md border ${selectedStore === store ? 'bg-blue-100' : 'bg-white'}`}
          >
            <CardContent>
              <p className="text-sm font-medium text-gray-700">{store}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Product List */}
      {selectedStore && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {visibleProducts.map(product => (
            <Card key={product.product_id} className="p-4 shadow hover:bg-gray-50 cursor-pointer" onClick={() => openProductModal(product)}>
              <CardContent>
                <p className="text-md font-semibold text-gray-800">{product.name}</p>
                <p className="text-sm text-gray-600">{product.category}</p>
                <p className="text-blue-700 font-bold">₹ {product.price}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Cart + Submit */}
      {cart.length > 0 && (
        <div className="mt-6 p-4 bg-white rounded shadow-md">
          <h3 className="text-lg font-bold mb-2">Cart</h3>
          <ul className="text-sm text-gray-800 list-disc list-inside">
            {cart.map((item, i) => (
              <li key={i}>{item.store_id} - {item.product_id} - Qty: {item.quantity}</li>
            ))}
          </ul>
          <Button className="mt-4" onClick={submitSales}>Submit Sales</Button>
        </div>
      )}

      {/* Product Modal */}
      {selectedProduct && (
        <Dialog open={showModal} onOpenChange={setShowModal}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>{selectedProduct.name}</DialogTitle>
            </DialogHeader>
            <div className="space-y-2 text-sm text-gray-700">
              <p><strong>Description:</strong> {selectedProduct.description}</p>
              <p><strong>Price:</strong> ₹{selectedProduct.price}</p>
              <p><strong>Category:</strong> {selectedProduct.category}</p>
              <p><strong>Weight:</strong> {selectedProduct.weight}kg</p>
              <p><strong>Storage:</strong> Temp - {selectedProduct.storage_requirements?.temperature}, Humidity - {selectedProduct.storage_requirements?.humidity}</p>
            </div>

            <div className="grid grid-cols-2 gap-4 mt-4">
              <Input type="number" placeholder="Quantity" value={saleDetails.quantity} onChange={(e) => setSaleDetails({ ...saleDetails, quantity: Number(e.target.value) })} />
              <Input placeholder="Discount" value={saleDetails.discount} onChange={(e) => setSaleDetails({ ...saleDetails, discount: e.target.value })} />
              <Input placeholder="Tax" value={saleDetails.tax} onChange={(e) => setSaleDetails({ ...saleDetails, tax: e.target.value })} />
            </div>

            <Button className="mt-4 w-full" onClick={addToCart}>Add to Cart</Button>
          </DialogContent>
        </Dialog>
      )}
    </div>
    </div>
  );
}
