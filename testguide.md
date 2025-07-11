# Postman Testing Guide - Inventory Service

Base URL: `http://localhost:8001`

## 1. Health Check
**GET** `/health`
- Tests: Service connectivity, database, and Kafka health

## 2. Create Store
**POST** `/api/v1/stores`
```json
{
  "store_id": "STORE001",
  "name": "Downtown Electronics Store",
  "address": {
    "street": "123 Main Street",
    "city": "New York",
    "state": "NY",
    "postal_code": "10001",
    "country": "USA",
    "coordinates": {
      "latitude": 40.7128,
      "longitude": -74.0060
    }
  },
  "manager_name": "John Smith",
  "phone": "555-0123",
  "email": "manager@store001.com",
  "operating_hours": {
    "monday": "9:00-21:00",
    "tuesday": "9:00-21:00",
    "wednesday": "9:00-21:00",
    "thursday": "9:00-21:00",
    "friday": "9:00-22:00",
    "saturday": "9:00-22:00",
    "sunday": "10:00-20:00"
  },
  "capacity": {
    "max_weight": 10000,
    "max_volume": 500
  }
}
```

## 3. Create Product
**POST** `/api/v1/products`
```json
{
  "product_id": "PROD001",
  "name": "iPhone 15 Pro",
  "description": "Latest iPhone with advanced features",
  "category": "electronics",
  "price": "999.99",
  "weight": 0.187,
  "dimensions": {
    "length": 14.67,
    "width": 7.09,
    "height": 0.83
  },
  "barcode": "123456789012",
  "supplier_id": "APPLE001",
  "shelf_life_days": 1095,
  "storage_requirements": {
    "temperature": "room",
    "humidity": "low"
  }
}
```

## 4. Create Inventory Item
**POST** `/api/v1/inventory`
```json
{
  "store_id": "STORE001",
  "product_id": "PROD001",
  "current_stock": 50,
  "reserved_stock": 0,
  "available_stock": 50,
  "reorder_threshold": 10,
  "warning_threshold": 15,
  "critical_threshold": 5,
  "max_capacity": 100,
  "location": "A1-B2"
}
```

## 5. Record Sale
**POST** `/api/v1/sales`
```json
{
  "store_id": "STORE001",
  "product_id": "PROD001",
  "quantity": 2,
  "unit_price": "999.99",
  "discount": "50.00",
  "tax": "80.00",
  "payment_method": "credit_card",
  "cashier_id": "CASHIER001",
  "customer_id": "CUST001"
}
```

## 6. Create Manual Restock Request
**POST** `/api/v1/restock-requests?store_id=STORE001&product_id=PROD001&quantity=20&priority=medium&reason=Manual restocking`

## 7. Get Inventory
**GET** `/api/v1/inventory?store_id=STORE001`

## 8. Get Low Stock Alerts
**GET** `/api/v1/analytics/low-stock-alerts?store_id=STORE001`

## 9. Get Inventory Summary
**GET** `/api/v1/analytics/inventory-summary?store_id=STORE001`

## 10. Update Inventory (Manual Adjustment)
**PUT** `/api/v1/inventory/STORE001/PROD001`
```json
{
  "store_id": "STORE001",
  "product_id": "PROD001",
  "quantity_change": 10,
  "change_type": "adjustment",
  "notes": "Manual inventory adjustment"
}
```

## 11. Vehicle CRUD
**POST** `/api/v1/vehicles`
```json
{
  "vehicle_id": "VEH_001",
  "type": "van",
  "available_weight_capacity": 1000,
  "available_volume_capacity": 8,
  "status": "available"
}
```
**GET** `/api/v1/vehicles` - List all

## 12. Process Fulfillment Request
**POST** `/api/v1/fulfillment/process-request`
```json
{
  "request_id": "FUL_XXXXXXX"
}
```

## 13. Fulfillment Messages (via Kafka UI or logs)
- Topic: `fulfillment-events`
- Contains vehicle assignments and errors

## 14. Generate AI SCM Strategy
**GET** `/api/v1/ai/generate-prompt`
- Returns SCM prompt + Gemini suggestion based on live inventory, vehicles, and restock data

## Testing Sequence:
1. Health check
2. Create store
3. Create product
4. Create inventory item
5. Record sales (multiple times to trigger low stock)
6. Check inventory status
7. View low stock alerts
8. Create restock requests
9. Process fulfillment
10. Generate AI optimization prompt

## Expected Kafka Events:
- Check Kafka UI at http://localhost:8080
- Topics:
  - `sales-events`
  - `inventory-updates`
  - `restock-requests`
  - `fulfillment-events`

## Error Testing:
- Create duplicate entries
- Oversell stock
- Use invalid IDs
- Send malformed requests
