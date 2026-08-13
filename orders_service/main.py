from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy import create_engine, Column, Integer, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy.sql import func
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
import os
import httpx
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL not set")

# URLs des autres services (à configurer selon votre environnement)
USERS_SERVICE_URL = os.getenv("USERS_SERVICE_URL", "http://users-service:8001")
PRODUCTS_SERVICE_URL = os.getenv("PRODUCTS_SERVICE_URL", "http://products-service:8002")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    product_id = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Orders Service")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class OrderCreate(BaseModel):
    user_id: int
    product_id: int

class OrderResponse(BaseModel):
    id: int
    user_id: int
    product_id: int
    user_name: Optional[str] = None
    product_name: Optional[str] = None
    created_at: datetime

    class Config:
        orm_mode = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

async def get_user_name(user_id: int):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{USERS_SERVICE_URL}/users/{user_id}")
            if response.status_code == 200:
                user_data = response.json()
                return user_data.get('name', f'Utilisateur #{user_id}')
    except Exception:
        pass
    return f'Utilisateur #{user_id}'

async def get_product_name(product_id: int):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{PRODUCTS_SERVICE_URL}/products/{product_id}")
            if response.status_code == 200:
                product_data = response.json()
                return product_data.get('name', f'Produit #{product_id}')
    except Exception:
        pass
    return f'Produit #{product_id}'

@app.get("/")
async def root():
    return {"message": "Orders Service"}

@app.get("/orders", response_model=list[OrderResponse])
async def list_orders(db: Session = Depends(get_db)):
    orders = db.query(Order).all()
    
    # Récupérer les noms des utilisateurs et produits
    orders_with_names = []
    for order in orders:
        order_response = OrderResponse.from_orm(order)
        order_response.user_name = await get_user_name(order.user_id)
        order_response.product_name = await get_product_name(order.product_id)
        orders_with_names.append(order_response)
    
    return orders_with_names

@app.post("/orders", response_model=OrderResponse)
async def create_order(order: OrderCreate, db: Session = Depends(get_db)):
    db_order = Order(user_id=order.user_id, product_id=order.product_id)
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    
    # Récupérer les noms pour la réponse
    order_response = OrderResponse.from_orm(db_order)
    order_response.user_name = await get_user_name(db_order.user_id)
    order_response.product_name = await get_product_name(db_order.product_id)
    
    return order_response

@app.get("/orders/{order_id}", response_model=OrderResponse)
async def get_order(order_id: int, db: Session = Depends(get_db)):
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    order_response = OrderResponse.from_orm(order)
    order_response.user_name = await get_user_name(order.user_id)
    order_response.product_name = await get_product_name(order.product_id)
    
    return order_response

@app.put("/orders/{order_id}", response_model=OrderResponse)
async def update_order(order_id: int, order: OrderCreate, db: Session = Depends(get_db)):
    db_order = db.get(Order, order_id)
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    db_order.user_id = order.user_id
    db_order.product_id = order.product_id
    
    db.commit()
    db.refresh(db_order)
    
    # Récupérer les noms pour la réponse
    order_response = OrderResponse.from_orm(db_order)
    order_response.user_name = await get_user_name(db_order.user_id)
    order_response.product_name = await get_product_name(db_order.product_id)
    
    return order_response

@app.delete("/orders/{order_id}")
async def delete_order(order_id: int, db: Session = Depends(get_db)):
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    db.delete(order)
    db.commit()
    return {"message": "Order deleted successfully"}
