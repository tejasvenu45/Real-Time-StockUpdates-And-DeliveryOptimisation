# 📦 Real-Time Stock Updates & Delivery Optimization

This project is a complete real-time retail logistics management system built using FastAPI, Kafka, MongoDB, and Gemini AI. It allows retail stores to maintain inventory, monitor low stock, process sales, and auto-optimize restock deliveries using vehicle capacity constraints and AI-generated SCM strategies.

Youtube link explaining the project: https://www.youtube.com/watch?v=mMhBD4ASmDo
---

## 🚀 Tech Stack

- **Backend**: FastAPI
- **Database**: MongoDB
- **Messaging Queue**: Apache Kafka
- **AI Integration**: Gemini API (RAG for SCM strategy)
- **Testing**: Postman, Kafka UI
- **Containerization**: Docker (optional)
- **Monitoring**: Health check endpoints

---

## 🧠 Features

- Store, Product & Inventory Management
- Real-time Sale & Stock Updates
- Auto-generated Restock Requests (threshold-based)
- Low-stock analytics alerts
- Vehicle-based delivery fulfillment optimization
- AI-prompt generation for SCM strategies (via Gemini)
- Kafka event streaming across the system

---

## 📬 API Endpoints (Inventory Service)

Base URL: `http://localhost:8001`

### 1. Health Check
```http
GET /health
```
Tests service, database, and Kafka connectivity.

### 2. Store Management
```http
POST /api/v1/stores
```
Creates a new store with location, manager, capacity.

### 3. Product Creation
```http
POST /api/v1/products
```
Adds new product metadata to the catalog.

### 4. Inventory Item Creation
```http
POST /api/v1/inventory
```
Links a product to a store’s inventory.

### 5. Sales Recording
```http
POST /api/v1/sales
```
Logs customer purchases, deducts stock.

### 6. Manual Restock Request
```http
POST /api/v1/restock-requests
```
Triggers a manual restock for a store-product.

### 7. Inventory Fetch
```http
GET /api/v1/inventory?store_id=STORE001
```

### 8. Analytics - Low Stock
```http
GET /api/v1/analytics/low-stock-alerts
```

### 9. Inventory Summary
```http
GET /api/v1/analytics/inventory-summary
```

### 10. Inventory Adjustment
```http
PUT /api/v1/inventory/{store_id}/{product_id}
```

---

## 🚚 Fulfillment Service

### 11. Vehicle Management
```http
POST /api/v1/vehicles
GET /api/v1/vehicles
```
CRUD operations for delivery vehicles.

### 12. Fulfillment Processing
```http
POST /api/v1/fulfillment/process-request
```
Assigns vehicles based on store demands and delivery constraints.

---

## 🧠 AI Strategy Engine

### 13. SCM Prompt Generator
```http
GET /api/v1/ai/generate-prompt
```
Returns structured SCM prompt and Gemini suggestion.

---

## 🧪 Sample Testing Sequence (Postman)

1. Health check
2. Create store
3. Add product
4. Add inventory item
5. Record sale (repeat to trigger low stock)
6. Fetch low stock alerts
7. Create restock request
8. Process fulfillment
9. Generate AI strategy

---

## 📡 Kafka Topics

Check Kafka UI (`http://localhost:8080`) for event logs:

- `sales-events`
- `inventory-updates`
- `restock-requests`
- `fulfillment-events`

---

## ❌ Error Testing

- Duplicate store/product
- Oversell inventory
- Malformed/invalid requests

---

## 📁 Folder Structure

```
/inventory_service/
/fulfillment_service/
/models/
/kafka_client/
/utils/
/tests/
/docs/
main.py
```

---

## 🤖 Example AI Prompt Output

```json
{
  "scm_prompt": "How can we optimize van delivery for STORE001 needing 20 units of PROD001?",
  "gemini_response": "Suggest sending 2 vans of type A and B with combined capacity of 1000kg."
}
```

---

## 👨‍💻 Author

**Tejas Venugopalan** – [GitHub](https://github.com/tejasvenu45)  
📩 tenacioustejas@gmail.com

---

## 🌟 Star this repo if you like the project!
