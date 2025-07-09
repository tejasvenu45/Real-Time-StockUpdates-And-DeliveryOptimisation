"""
Pydantic models for the warehouse stock monitoring system
"""
from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from enum import Enum
from pydantic import BaseModel, Field, field_validator, model_validator
from decimal import Decimal

# Enums for status fields
class StoreStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"

class ProductCategory(str, Enum):
    ELECTRONICS = "electronics"
    CLOTHING = "clothing"
    FOOD = "food"
    BOOKS = "books"
    HOME = "home"
    SPORTS = "sports"
    BEAUTY = "beauty"
    AUTOMOTIVE = "automotive"

class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class RequestStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"

class VehicleStatus(str, Enum):
    AVAILABLE = "available"
    IN_TRANSIT = "in_transit"
    LOADING = "loading"
    UNLOADING = "unloading"
    MAINTENANCE = "maintenance"

class DeliveryStatus(str, Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    DELIVERED = "delivered"
    FAILED = "failed"
    CANCELLED = "cancelled"

# Base models
class BaseModel(BaseModel):
    """Base model with common fields"""
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    
    model_config = {
        "json_encoders": {
            datetime: lambda v: v.isoformat() if v else None,
            Decimal: lambda v: float(v) if v else None
        },
        "use_enum_values": True,
        "arbitrary_types_allowed": True
    }

class Coordinates(BaseModel):
    """GPS coordinates"""
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)

class Address(BaseModel):
    """Address information"""
    street: str
    city: str
    state: str
    postal_code: str
    country: str
    coordinates: Optional[Coordinates] = None

class Dimensions(BaseModel):
    """Physical dimensions"""
    length: float = Field(..., gt=0)
    width: float = Field(..., gt=0)
    height: float = Field(..., gt=0)
    
    @property
    def volume(self) -> float:
        return self.length * self.width * self.height

# Core business models
class Store(BaseModel):
    """Store model"""
    store_id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    address: Address
    status: StoreStatus = StoreStatus.ACTIVE
    manager_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    operating_hours: Dict[str, str] = Field(default_factory=dict)
    capacity: Dict[str, Union[int, float]] = Field(default_factory=dict)  # max_weight, max_volume
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None


class StoreCreateRequest(BaseModel):
    store_id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    address: Address
    manager_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    operating_hours: Dict[str, str] = Field(default_factory=dict)
    capacity: Dict[str, Union[int, float]] = Field(default_factory=dict)

class Product(BaseModel):
    """Product model"""
    product_id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    description: Optional[str] = None
    category: ProductCategory
    price: Decimal = Field(..., gt=0, decimal_places=2)
    weight: float = Field(..., gt=0)  # in kg
    dimensions: Dimensions
    barcode: Optional[str] = None
    supplier_id: Optional[str] = None
    shelf_life_days: Optional[int] = Field(None, gt=0)
    storage_requirements: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

class InventoryItemCreate(BaseModel):
    """Inventory item creation model (for API input)"""
    store_id: str
    product_id: str
    current_stock: int = Field(..., ge=0)
    reserved_stock: int = Field(default=0, ge=0)
    reorder_threshold: int = Field(..., gt=0)
    warning_threshold: int = Field(..., gt=0)
    critical_threshold: int = Field(..., gt=0)
    max_capacity: int = Field(..., gt=0)
    location: Optional[str] = None  # shelf/bin location
    
    @model_validator(mode='after')
    def validate_thresholds(self):
        """Validate that thresholds are in correct order"""
        if not (self.critical_threshold <= self.warning_threshold <= self.reorder_threshold):
            raise ValueError("Thresholds must satisfy: critical <= warning <= reorder")
        return self

class InventoryItem(BaseModel):
    """Inventory item model"""
    store_id: str
    product_id: str
    current_stock: int = Field(..., ge=0)
    reserved_stock: int = Field(default=0, ge=0)
    available_stock: Optional[int] = None  # Make it optional, will be calculated
    reorder_threshold: int = Field(..., gt=0)
    warning_threshold: int = Field(..., gt=0)
    critical_threshold: int = Field(..., gt=0)
    max_capacity: int = Field(..., gt=0)
    last_restock_date: Optional[datetime] = None
    last_sale_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    location: Optional[str] = None  # shelf/bin location
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    
    @model_validator(mode='after')
    def calculate_available_and_validate(self):
        """Calculate available stock and validate thresholds"""
        # Calculate available stock
        self.available_stock = max(0, self.current_stock - self.reserved_stock)
        
        # Validate thresholds
        if not (self.critical_threshold <= self.warning_threshold <= self.reorder_threshold):
            raise ValueError("Thresholds must satisfy: critical <= warning <= reorder")
        
        return self

class SaleTransaction(BaseModel):
    """Sales transaction model"""
    transaction_id: str = Field(..., min_length=1)
    store_id: str
    product_id: str
    quantity: int = Field(..., gt=0)
    unit_price: Decimal = Field(..., gt=0, decimal_places=2)
    total_amount: Decimal = Field(..., gt=0, decimal_places=2)
    discount: Decimal = Field(default=Decimal('0'), ge=0, decimal_places=2)
    tax: Decimal = Field(default=Decimal('0'), ge=0, decimal_places=2)
    payment_method: Optional[str] = None
    cashier_id: Optional[str] = None
    customer_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    @field_validator('total_amount')
    @classmethod
    def calculate_total(cls, v, info):
        """Calculate total amount based on quantity, unit_price, discount, and tax"""
        if info.data:
            quantity = info.data.get('quantity', 1)
            unit_price = info.data.get('unit_price', Decimal('0'))
            discount = info.data.get('discount', Decimal('0'))
            tax = info.data.get('tax', Decimal('0'))
            return (quantity * unit_price) - discount + tax
        return v

class RestockRequest(BaseModel):
    """Restock request model"""
    request_id: str = Field(..., min_length=1)
    store_id: str
    product_id: str
    requested_quantity: int = Field(..., gt=0)
    priority: Priority = Priority.MEDIUM
    reason: str = Field(..., min_length=1)
    status: RequestStatus = RequestStatus.PENDING
    requested_by: Optional[str] = None
    approved_by: Optional[str] = None
    approved_quantity: Optional[int] = Field(None, ge=0)
    estimated_delivery_date: Optional[datetime] = None
    actual_delivery_date: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

class Vehicle(BaseModel):
    """Vehicle model"""
    vehicle_id: str = Field(..., min_length=1)
    license_plate: str = Field(..., min_length=1)
    vehicle_type: str  # truck, van, etc.
    max_weight_capacity: float = Field(..., gt=0)  # in kg
    max_volume_capacity: float = Field(..., gt=0)  # in cubic meters
    current_weight: float = Field(default=0, ge=0)
    current_volume: float = Field(default=0, ge=0)
    status: VehicleStatus = VehicleStatus.AVAILABLE
    driver_id: Optional[str] = None
    current_location: Optional[Coordinates] = None
    fuel_level: Optional[float] = Field(None, ge=0, le=100)
    maintenance_due_date: Optional[datetime] = None
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    
    @property
    def available_weight_capacity(self) -> float:
        return max(0, self.max_weight_capacity - self.current_weight)
    
    @property
    def available_volume_capacity(self) -> float:
        return max(0, self.max_volume_capacity - self.current_volume)

class ManualStockRequest(BaseModel):
    """Manual stock request from stores"""
    request_id: str = Field(..., min_length=1)
    store_id: str
    product_id: str
    requested_quantity: int = Field(..., gt=0)
    priority: Priority = Priority.MEDIUM
    reason: str = Field(..., min_length=1)
    status: RequestStatus = RequestStatus.PENDING
    requested_by: str  # Store manager name/ID
    urgency_level: str = Field(default="normal")  # normal, urgent, critical
    preferred_delivery_window: Optional[str] = None  # morning, afternoon, evening
    notes: Optional[str] = None
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

class DeliveryPlan(BaseModel):
    """AI-generated delivery plan"""
    plan_id: str = Field(..., min_length=1)
    vehicle_id: str
    store_destinations: List[str] = Field(..., min_items=1)  # List of store IDs in delivery order
    product_items: List[Dict[str, Any]] = Field(..., min_items=1)  # Products to deliver
    estimated_total_weight: float = Field(..., gt=0)
    estimated_total_volume: float = Field(..., gt=0)
    estimated_distance_km: float = Field(..., gt=0)
    ai_reasoning: str = Field(..., min_length=1)  # AI's natural language explanation
    status: str = Field(default="pending")  # pending, approved, executing, completed
    created_by_ai: bool = Field(default=True)
    approved_by: Optional[str] = None  # Warehouse manager
    execution_notes: Optional[str] = None
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

class DeliveryItem(BaseModel):
    """Item in a delivery"""
    product_id: str
    quantity: int = Field(..., gt=0)
    weight: float = Field(..., gt=0)
    volume: float = Field(..., gt=0)

class Delivery(BaseModel):
    """Delivery model"""
    delivery_id: str = Field(..., min_length=1)
    vehicle_id: str
    driver_id: Optional[str] = None
    route_id: Optional[str] = None
    stores: List[str] = Field(..., min_items=1)  # List of store IDs in delivery order
    items: List[DeliveryItem] = Field(..., min_items=1)
    status: DeliveryStatus = DeliveryStatus.SCHEDULED
    scheduled_departure: datetime
    actual_departure: Optional[datetime] = None
    estimated_arrival: Optional[datetime] = None
    actual_arrival: Optional[datetime] = None
    total_weight: float = Field(..., gt=0)
    total_volume: float = Field(..., gt=0)
    total_distance: Optional[float] = Field(None, gt=0)
    fuel_consumed: Optional[float] = Field(None, ge=0)
    delivery_notes: Optional[str] = None
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

# Request/Response models for APIs
class StoreCreateRequest(BaseModel):
    """Request model for creating a store"""
    store_id: str
    name: str
    address: Address
    manager_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    operating_hours: Dict[str, str] = Field(default_factory=dict)
    capacity: Dict[str, Union[int, float]] = Field(default_factory=dict)

class ProductCreateRequest(BaseModel):
    """Request model for creating a product"""
    product_id: str
    name: str
    description: Optional[str] = None
    category: ProductCategory
    price: Decimal = Field(..., gt=0, decimal_places=2)
    weight: float = Field(..., gt=0)
    dimensions: Dimensions
    barcode: Optional[str] = None
    supplier_id: Optional[str] = None
    shelf_life_days: Optional[int] = Field(None, gt=0)
    storage_requirements: Dict[str, Any] = Field(default_factory=dict)

class InventoryUpdateRequest(BaseModel):
    """Request model for updating inventory"""
    store_id: str
    product_id: str
    quantity_change: int  # positive for addition, negative for reduction
    change_type: str  # 'sale', 'restock', 'adjustment', 'damage', 'expired'
    reference_id: Optional[str] = None  # transaction_id, delivery_id, etc.
    notes: Optional[str] = None

class SaleRequest(BaseModel):
    """Request model for recording a sale"""
    store_id: str
    product_id: str
    quantity: int = Field(..., gt=0)
    unit_price: Decimal = Field(..., gt=0, decimal_places=2)
    discount: Decimal = Field(default=Decimal('0'), ge=0, decimal_places=2)
    tax: Decimal = Field(default=Decimal('0'), ge=0, decimal_places=2)
    payment_method: Optional[str] = None
    cashier_id: Optional[str] = None
    customer_id: Optional[str] = None

# Response models
class APIResponse(BaseModel):
    """Standard API response"""
    success: bool
    message: str
    data: Optional[Any] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class PaginatedResponse(BaseModel):
    """Paginated response"""
    items: List[Any]
    total: int
    page: int
    size: int
    pages: int

# Health check model
class HealthCheck(BaseModel):
    """Health check response"""
    service: str
    status: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: Optional[str] = None
    dependencies: Dict[str, str] = Field(default_factory=dict)