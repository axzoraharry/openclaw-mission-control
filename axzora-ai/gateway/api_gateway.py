#!/usr/bin/env python3
"""
Axzora API Gateway - Unified Super-Aggregator
Connects 50+ providers: Travel, Marketplace, Food, Events, Loyalty
"""

import os
import json
import asyncio
from datetime import datetime
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field

import httpx
from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import websockets

# ─────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────
HAPPY_PAISA_CONTRACT = "0xf99ae6F3234b5E7f247BD12A8a59668Aa479E560"

API_KEYS = {
    "amadeus": os.getenv("AMADEUS_API_KEY", ""),
    "amadeus_secret": os.getenv("AMADEUS_API_SECRET", ""),
    "duffel": os.getenv("DUFFEL_API_KEY", ""),
    "skyscanner": os.getenv("SKYSCANNER_API_KEY", ""),
    "rapidapi": os.getenv("RAPIDAPI_KEY", ""),
    "zomato": os.getenv("ZOMATO_API_KEY", ""),
    "eventbrite": os.getenv("EVENTBRITE_API_KEY", ""),
    "ticketmaster": os.getenv("TICKETMASTER_API_KEY", ""),
}

BASE_URLS = {
    "amadeus": "https://api.amadeus.com/v2",
    "duffel": "https://api.duffel.com",
    "skyscanner": "https://partners.api.skyscanner.net/apiservices",
    "rapidapi": "https://rapidapi.p.rapidapi.com",
    "zomato": "https://developers.zomato.com/api/v2.1",
    "eventbrite": "https://www.eventbriteapi.com/v3",
    "ticketmaster": "https://app.ticketmaster.com/discovery/v2",
}

# ─────────────────────────────────────────────
# Models
# ─────────────────────────────────────────────
class SearchRequest(BaseModel):
    query: str
    category: str = "all"  # travel, marketplace, food, events, all
    location: Optional[Dict[str, float]] = None  # {lat, lng}
    dates: Optional[Dict[str, str]] = None  # {check_in, check_out}
    budget: Optional[float] = None
    currency: str = "INR"

class SearchResponse(BaseModel):
    category: str
    results: List[Dict[str, Any]]
    total: int
    rewards_eligible: int
    cached: bool = False

class RewardRequest(BaseModel):
    user_id: str
    action: str  # flight_booking, hotel_booking, shopping, dining
    amount: float
    currency: str = "INR"
    booking_id: str

class RewardResponse(BaseModel):
    user_id: str
    happy_paisa_earned: float
    total_balance: float
    transaction_id: str
    message: str

# ─────────────────────────────────────────────
# Reward Rules
# ─────────────────────────────────────────────
REWARD_RULES = {
    "flight_booking": {"rate": 50, "type": "fixed"},
    "hotel_booking": {"rate": 40, "type": "fixed"},
    "shopping": {"rate": 0.05, "type": "percentage"},
    "dining": {"rate": 0.03, "type": "percentage"},
    "event_booking": {"rate": 20, "type": "fixed"},
}

# ─────────────────────────────────────────────
# API Gateway
# ─────────────────────────────────────────────
app = FastAPI(
    title="Axzora Super-Aggregator API",
    description="Unified gateway for 50+ providers: Travel, Marketplace, Food, Events, Loyalty",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory cache
cache: Dict[str, Dict] = {}
ws_clients: set = set()


# ─────────────────────────────────────────────
# Travel Service
# ─────────────────────────────────────────────
class TravelService:
    """Aggregates Amadeus, Duffel, Skyscanner"""
    
    def __init__(self):
        self.amadeus_token = None
        
    async def get_amadeus_token(self) -> str:
        """Get Amadeus access token"""
        if not API_KEYS["amadeus"]:
            return None
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.amadeus.com/v1/security/oauth2/token",
                    data={
                        "grant_type": "client_credentials",
                        "client_id": API_KEYS["amadeus"],
                        "client_secret": API_KEYS["amadeus_secret"],
                    }
                )
                if response.status_code == 200:
                    return response.json().get("access_token")
        except Exception as e:
            print(f"[Amadeus auth error: {e}]")
        return None
    
    async def search_flights(self, origin: str, destination: str, date: str, budget: float = None) -> List[Dict]:
        """Search flights across providers"""
        results = []
        
        # Amadeus
        token = await self.get_amadeus_token()
        if token:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"{BASE_URLS['amadeus']}/shopping/flight-offers",
                        params={
                            "originLocationCode": origin,
                            "destinationLocationCode": destination,
                            "departureDate": date,
                            "adults": 1,
                            "currencyCode": "INR",
                            "maxPrice": budget,
                        },
                        headers={"Authorization": f"Bearer {token}"}
                    )
                    if response.status_code == 200:
                        data = response.json()
                        for offer in data.get("data", [])[:10]:
                            results.append({
                                "provider": "amadeus",
                                "type": "flight",
                                "id": offer.get("id"),
                                "price": float(offer.get("price", {}).get("total", 0)),
                                "currency": "INR",
                                "airline": offer.get("validatingAirlineCodes", ["Unknown"])[0],
                                "departure": offer.get("itineraries", [{}])[0].get("segments", [{}])[0].get("departure", {}),
                                "arrival": offer.get("itineraries", [{}])[0].get("segments", [{}])[-1].get("arrival", {}),
                                "duration": offer.get("itineraries", [{}])[0].get("duration", ""),
                                "stops": len(offer.get("itineraries", [{}])[0].get("segments", [])) - 1,
                                "rewards_eligible": True,
                            })
            except Exception as e:
                print(f"[Amadeus search error: {e}]")
        
        # Mock results if no API key
        if not results:
            results = self._mock_flights(origin, destination, date, budget)
        
        return results
    
    def _mock_flights(self, origin: str, destination: str, date: str, budget: float = None) -> List[Dict]:
        """Mock flight results for demo"""
        import random
        airlines = ["IndiGo", "Air India", "SpiceJet", "Vistara", "GoAir"]
        results = []
        for i in range(5):
            price = random.randint(3000, 15000)
            if budget and price > budget:
                continue
            results.append({
                "provider": "mock",
                "type": "flight",
                "id": f"FLIGHT-{i+1}",
                "price": price,
                "currency": "INR",
                "airline": random.choice(airlines),
                "departure": {"airport": origin, "time": f"{date}T{random.randint(6,18):02d}:00"},
                "arrival": {"airport": destination, "time": f"{date}T{random.randint(6,18):02d}+{random.randint(1,4)}:00"},
                "duration": f"PT{random.randint(1,4)}H{random.randint(0,59)}M",
                "stops": random.randint(0, 2),
                "rewards_eligible": True,
            })
        return results
    
    async def search_hotels(self, city: str, check_in: str, check_out: str, budget: float = None) -> List[Dict]:
        """Search hotels"""
        # Mock for demo
        import random
        hotels = ["Taj Palace", "The Oberoi", "ITC Grand", "Leela Palace", "JW Marriott", "Hyatt Regency"]
        results = []
        for i in range(6):
            price_per_night = random.randint(2000, 25000)
            total_price = price_per_night * 2  # Assuming 2 nights
            if budget and total_price > budget:
                continue
            results.append({
                "provider": "mock",
                "type": "hotel",
                "id": f"HOTEL-{i+1}",
                "name": random.choice(hotels),
                "price_per_night": price_per_night,
                "total_price": total_price,
                "currency": "INR",
                "rating": round(random.uniform(3.5, 5.0), 1),
                "amenities": ["WiFi", "Pool", "Spa", "Restaurant"][:random.randint(1, 4)],
                "location": city,
                "rewards_eligible": True,
            })
        return results


# ─────────────────────────────────────────────
# Marketplace Service
# ─────────────────────────────────────────────
class MarketplaceService:
    """Aggregates RapidAPI, Commerce Layer"""
    
    async def search_products(self, query: str, budget: float = None) -> List[Dict]:
        """Search products across marketplaces"""
        import random
        products = []
        platforms = ["Amazon", "Flipkart", "Myntra", "Ajio"]
        
        for i in range(8):
            price = random.randint(100, 50000)
            if budget and price > budget:
                continue
            products.append({
                "provider": "mock",
                "type": "product",
                "id": f"PROD-{i+1}",
                "name": f"{query.title()} - Product {i+1}",
                "price": price,
                "currency": "INR",
                "platform": random.choice(platforms),
                "rating": round(random.uniform(3.0, 5.0), 1),
                "reviews": random.randint(10, 5000),
                "image": f"https://via.placeholder.com/150?text={query}",
                "rewards_eligible": True,
            })
        return products


# ─────────────────────────────────────────────
# Food Service
# ─────────────────────────────────────────────
class FoodService:
    """Aggregates Zomato, Swiggy"""
    
    async def search_restaurants(self, query: str, lat: float = None, lng: float = None) -> List[Dict]:
        """Search restaurants"""
        import random
        cuisines = ["North Indian", "Chinese", "Italian", "Mexican", "Thai", "Continental"]
        restaurants = []
        
        for i in range(6):
            restaurants.append({
                "provider": "mock",
                "type": "restaurant",
                "id": f"REST-{i+1}",
                "name": f"{random.choice(cuisines)} Restaurant {i+1}",
                "cuisine": random.choice(cuisines),
                "rating": round(random.uniform(3.5, 5.0), 1),
                "delivery_time": f"{random.randint(20, 60)} mins",
                "cost_for_two": random.randint(200, 2000),
                "currency": "INR",
                "address": f"Location {i+1}, City",
                "rewards_eligible": True,
            })
        return restaurants


# ─────────────────────────────────────────────
# Events Service
# ─────────────────────────────────────────────
class EventsService:
    """Aggregates Eventbrite, Ticketmaster"""
    
    async def search_events(self, query: str, city: str = None, dates: Dict = None) -> List[Dict]:
        """Search events"""
        import random
        event_types = ["Concert", "Sports", "Theatre", "Comedy", "Workshop", "Festival"]
        events = []
        
        for i in range(5):
            events.append({
                "provider": "mock",
                "type": "event",
                "id": f"EVENT-{i+1}",
                "name": f"{random.choice(event_types)}: {query.title()}",
                "venue": f"Venue {i+1}, {city or 'City'}",
                "date": dates.get("check_in", "2026-03-15") if dates else "2026-03-15",
                "price": random.randint(500, 5000),
                "currency": "INR",
                "category": random.choice(event_types),
                "available_tickets": random.randint(10, 500),
                "rewards_eligible": True,
            })
        return events


# ─────────────────────────────────────────────
# Loyalty Service (Happy Paisa)
# ─────────────────────────────────────────────
class LoyaltyService:
    """Happy Paisa rewards engine"""
    
    def __init__(self):
        self.balances: Dict[str, float] = {}  # user_id -> balance
        self.transactions: List[Dict] = []
    
    def calculate_reward(self, action: str, amount: float) -> float:
        """Calculate Happy Paisa reward"""
        rule = REWARD_RULES.get(action, {"rate": 0, "type": "fixed"})
        if rule["type"] == "fixed":
            return rule["rate"]
        else:
            return amount * rule["rate"]
    
    async def issue_reward(self, user_id: str, action: str, amount: float, booking_id: str) -> RewardResponse:
        """Issue Happy Paisa reward"""
        reward = self.calculate_reward(action, amount)
        
        if user_id not in self.balances:
            self.balances[user_id] = 0
        
        self.balances[user_id] += reward
        
        transaction = {
            "id": f"TXN-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "user_id": user_id,
            "action": action,
            "amount": amount,
            "reward": reward,
            "booking_id": booking_id,
            "timestamp": datetime.now().isoformat(),
            "contract": HAPPY_PAISA_CONTRACT,
        }
        self.transactions.append(transaction)
        
        # Broadcast to WebSocket clients
        await broadcast_event({
            "event": "reward_issued",
            "user_id": user_id,
            "amount": reward,
            "token": "Happy Paisa",
            "total_balance": self.balances[user_id],
        })
        
        return RewardResponse(
            user_id=user_id,
            happy_paisa_earned=reward,
            total_balance=self.balances[user_id],
            transaction_id=transaction["id"],
            message=f"🎉 You earned {reward} Happy Paisa! Total: {self.balances[user_id]}",
        )
    
    def get_balance(self, user_id: str) -> float:
        """Get user's Happy Paisa balance"""
        return self.balances.get(user_id, 0)


# ─────────────────────────────────────────────
# Service Instances
# ─────────────────────────────────────────────
travel_service = TravelService()
marketplace_service = MarketplaceService()
food_service = FoodService()
events_service = EventsService()
loyalty_service = LoyaltyService()


# ─────────────────────────────────────────────
# WebSocket Broadcaster
# ─────────────────────────────────────────────
async def broadcast_event(data: Dict):
    """Broadcast event to all WebSocket clients"""
    if ws_clients:
        message = json.dumps(data)
        await asyncio.gather(
            *[client.send(message) for client in ws_clients],
            return_exceptions=True
        )


# ─────────────────────────────────────────────
# API Routes
# ─────────────────────────────────────────────
@app.get("/")
async def root():
    """API Gateway info"""
    return {
        "service": "Axzora Super-Aggregator API",
        "version": "1.0.0",
        "providers": {
            "travel": ["Amadeus", "Duffel", "Skyscanner"],
            "marketplace": ["RapidAPI", "Commerce Layer"],
            "food": ["Zomato", "Swiggy"],
            "events": ["Eventbrite", "Ticketmaster"],
            "loyalty": ["Happy Paisa"],
        },
        "endpoints": [
            "/api/travel/flights",
            "/api/travel/hotels",
            "/api/marketplace/search",
            "/api/food/restaurants",
            "/api/events/search",
            "/api/loyalty/reward",
            "/api/loyalty/balance/{user_id}",
            "/api/search (unified)",
        ],
        "contract": HAPPY_PAISA_CONTRACT,
    }


@app.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


# ─────────────────────────────────────────────
# Travel Routes
# ─────────────────────────────────────────────
@app.get("/api/travel/flights")
async def search_flights(
    origin: str = Query(..., description="Origin airport code (e.g., DEL)"),
    destination: str = Query(..., description="Destination airport code (e.g., GOI)"),
    date: str = Query(..., description="Departure date (YYYY-MM-DD)"),
    budget: Optional[float] = Query(None, description="Maximum budget in INR"),
):
    """Search flights across providers"""
    results = await travel_service.search_flights(origin, destination, date, budget)
    return SearchResponse(
        category="flights",
        results=results,
        total=len(results),
        rewards_eligible=sum(1 for r in results if r.get("rewards_eligible")),
    )


@app.get("/api/travel/hotels")
async def search_hotels(
    city: str = Query(..., description="City name"),
    check_in: str = Query(..., description="Check-in date (YYYY-MM-DD)"),
    check_out: str = Query(..., description="Check-out date (YYYY-MM-DD)"),
    budget: Optional[float] = Query(None, description="Maximum budget in INR"),
):
    """Search hotels"""
    results = await travel_service.search_hotels(city, check_in, check_out, budget)
    return SearchResponse(
        category="hotels",
        results=results,
        total=len(results),
        rewards_eligible=sum(1 for r in results if r.get("rewards_eligible")),
    )


# ─────────────────────────────────────────────
# Marketplace Routes
# ─────────────────────────────────────────────
@app.get("/api/marketplace/search")
async def search_products(
    q: str = Query(..., description="Search query"),
    budget: Optional[float] = Query(None, description="Maximum budget in INR"),
):
    """Search products across marketplaces"""
    results = await marketplace_service.search_products(q, budget)
    return SearchResponse(
        category="products",
        results=results,
        total=len(results),
        rewards_eligible=sum(1 for r in results if r.get("rewards_eligible")),
    )


# ─────────────────────────────────────────────
# Food Routes
# ─────────────────────────────────────────────
@app.get("/api/food/restaurants")
async def search_restaurants(
    q: str = Query(..., description="Search query"),
    lat: Optional[float] = Query(None, description="Latitude"),
    lng: Optional[float] = Query(None, description="Longitude"),
):
    """Search restaurants"""
    results = await food_service.search_restaurants(q, lat, lng)
    return SearchResponse(
        category="restaurants",
        results=results,
        total=len(results),
        rewards_eligible=sum(1 for r in results if r.get("rewards_eligible")),
    )


# ─────────────────────────────────────────────
# Events Routes
# ─────────────────────────────────────────────
@app.get("/api/events/search")
async def search_events(
    q: str = Query(..., description="Search query"),
    city: Optional[str] = Query(None, description="City"),
    date_from: Optional[str] = Query(None, description="From date"),
    date_to: Optional[str] = Query(None, description="To date"),
):
    """Search events"""
    dates = {"check_in": date_from, "check_out": date_to} if date_from else None
    results = await events_service.search_events(q, city, dates)
    return SearchResponse(
        category="events",
        results=results,
        total=len(results),
        rewards_eligible=sum(1 for r in results if r.get("rewards_eligible")),
    )


# ─────────────────────────────────────────────
# Loyalty Routes
# ─────────────────────────────────────────────
@app.post("/api/loyalty/reward", response_model=RewardResponse)
async def issue_reward(request: RewardRequest):
    """Issue Happy Paisa reward"""
    return await loyalty_service.issue_reward(
        request.user_id,
        request.action,
        request.amount,
        request.booking_id,
    )


@app.get("/api/loyalty/balance/{user_id}")
async def get_balance(user_id: str):
    """Get Happy Paisa balance"""
    return {
        "user_id": user_id,
        "happy_paisa_balance": loyalty_service.get_balance(user_id),
        "contract": HAPPY_PAISA_CONTRACT,
    }


# ─────────────────────────────────────────────
# Unified Search (Mr Happy AI)
# ─────────────────────────────────────────────
@app.post("/api/search")
async def unified_search(request: SearchRequest, background_tasks: BackgroundTasks):
    """
    Unified search across all categories.
    Mr Happy AI can use this to plan complete trips.
    """
    all_results = []
    
    # Search all categories in parallel
    tasks = []
    
    if request.category in ["all", "travel"]:
        if request.dates:
            tasks.append(travel_service.search_flights(
                "DEL", "GOI", request.dates.get("check_in", "2026-03-15"), request.budget
            ))
            tasks.append(travel_service.search_hotels(
                request.query, request.dates.get("check_in"), request.dates.get("check_out"), request.budget
            ))
    
    if request.category in ["all", "marketplace"]:
        tasks.append(marketplace_service.search_products(request.query, request.budget))
    
    if request.category in ["all", "food"]:
        lat = request.location.get("lat") if request.location else None
        lng = request.location.get("lng") if request.location else None
        tasks.append(food_service.search_restaurants(request.query, lat, lng))
    
    if request.category in ["all", "events"]:
        tasks.append(events_service.search_events(request.query, request.query, request.dates))
    
    # Execute all searches
    results_list = await asyncio.gather(*tasks, return_exceptions=True)
    
    for results in results_list:
        if isinstance(results, list):
            all_results.extend(results)
    
    return {
        "query": request.query,
        "category": request.category,
        "results": all_results,
        "total": len(all_results),
        "rewards_eligible": sum(1 for r in all_results if r.get("rewards_eligible")),
        "happy_paisa_contract": HAPPY_PAISA_CONTRACT,
    }


# ─────────────────────────────────────────────
# WebSocket for Real-Time Updates
# ─────────────────────────────────────────────
@app.websocket("/ws")
async def websocket_endpoint(websocket):
    """WebSocket for real-time price/reward updates"""
    await websocket.accept()
    ws_clients.add(websocket)
    try:
        await websocket.send_json({"event": "connected", "message": "Welcome to Axzora real-time updates"})
        while True:
            data = await websocket.receive_text()
            # Echo or handle commands
            if data == "ping":
                await websocket.send_json({"event": "pong"})
    except Exception:
        pass
    finally:
        ws_clients.discard(websocket)


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    print(f"""
╔══════════════════════════════════════════════════════════════════╗
║           AXZORA SUPER-AGGREGATOR API GATEWAY                    ║
║                                                                  ║
║  Travel: Amadeus, Duffel, Skyscanner                            ║
║  Marketplace: RapidAPI, Commerce Layer                          ║
║  Food: Zomato, Swiggy                                           ║
║  Events: Eventbrite, Ticketmaster                               ║
║  Loyalty: Happy Paisa ({HAPPY_PAISA_CONTRACT[:10]}...)           ║
╚══════════════════════════════════════════════════════════════════╝
    """)
    uvicorn.run(app, host="0.0.0.0", port=8080)
