"""
AXZORA Super App - FastAPI Backend
===================================

Main API backend for the AXZORA Super App.
Provides endpoints for flights, hotels, cricket, wallet, and AI.

Author: Mr. Happy AI (Digital CEO of Axzora)
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import json
import requests

# ============================================================================
# APP SETUP
# ============================================================================

app = FastAPI(
    title="AXZORA Super App API",
    description="Backend API for AXZORA Super App - One App, Infinite Power",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# MODELS
# ============================================================================

class User(BaseModel):
    id: str
    name: str
    email: EmailStr
    phone: str
    wallet_balance: float = 0.0
    hp_balance: float = 0.0
    created_at: datetime = datetime.utcnow()

class FlightSearch(BaseModel):
    from_city: str
    to_city: str
    departure_date: str
    passengers: int = 1
    travel_class: str = "Economy"

class Flight(BaseModel):
    id: str
    airline: str
    flight_number: str
    origin: str
    destination: str
    departure_time: str
    arrival_time: str
    price: float
    seats_available: int

class HotelSearch(BaseModel):
    destination: str
    check_in: str
    check_out: str
    guests: int = 2
    rooms: int = 1

class Hotel(BaseModel):
    id: str
    name: str
    location: str
    rating: float
    price_per_night: float
    amenities: List[str]
    image_url: str

class CricketMatch(BaseModel):
    id: str
    team1: str
    team2: str
    score1: str
    score2: str
    status: str
    venue: str
    start_time: str
    ai_prediction: Optional[Dict[str, Any]] = None

class ChatMessage(BaseModel):
    message: str
    context: Optional[Dict[str, Any]] = None

class WalletTransaction(BaseModel):
    amount: float
    transaction_type: str  # "credit", "debit", "hp_convert"
    description: str

class HPConvert(BaseModel):
    amount: float
    from_currency: str  # "HP" or "INR"
    to_currency: str    # "HP" or "INR"

# ============================================================================
# SAMPLE DATA
# ============================================================================

SAMPLE_FLIGHTS = [
    Flight(
        id="FL001",
        airline="Air India",
        flight_number="AI-302",
        origin="Mumbai",
        destination="Delhi",
        departure_time="2026-03-07 06:00",
        arrival_time="2026-03-07 08:00",
        price=4500.0,
        seats_available=45
    ),
    Flight(
        id="FL002",
        airline="IndiGo",
        flight_number="6E-2341",
        origin="Mumbai",
        destination="Delhi",
        departure_time="2026-03-07 09:30",
        arrival_time="2026-03-07 11:30",
        price=3200.0,
        seats_available=120
    ),
    Flight(
        id="FL003",
        airline="Vistara",
        flight_number="UK-944",
        origin="Mumbai",
        destination="Delhi",
        departure_time="2026-03-07 14:00",
        arrival_time="2026-03-07 16:00",
        price=5800.0,
        seats_available=32
    )
]

SAMPLE_HOTELS = [
    Hotel(
        id="HT001",
        name="Taj Palace",
        location="New Delhi",
        rating=4.8,
        price_per_night=15000.0,
        amenities=["WiFi", "Pool", "Spa", "Restaurant", "Gym"],
        image_url="https://example.com/taj.jpg"
    ),
    Hotel(
        id="HT002",
        name="The Oberoi",
        location="New Delhi",
        rating=4.9,
        price_per_night=22000.0,
        amenities=["WiFi", "Pool", "Spa", "Restaurant", "Gym", "Butler"],
        image_url="https://example.com/oberoi.jpg"
    ),
    Hotel(
        id="HT003",
        name="ITC Maurya",
        location="New Delhi",
        rating=4.7,
        price_per_night=12000.0,
        amenities=["WiFi", "Pool", "Restaurant", "Gym"],
        image_url="https://example.com/itc.jpg"
    )
]

SAMPLE_MATCHES = [
    CricketMatch(
        id="CM001",
        team1="India",
        team2="Australia",
        score1="285/6",
        score2="312/10",
        status="LIVE - India batting",
        venue="Melbourne Cricket Ground",
        start_time="2026-03-07 09:00",
        ai_prediction={"winner": "India", "confidence": 0.72, "key_factors": ["Home advantage", "Strong batting lineup"]}
    ),
    CricketMatch(
        id="CM002",
        team1="England",
        team2="South Africa",
        score1="245/10",
        score2="198/4",
        status="LIVE - SA batting",
        venue="Lord's",
        start_time="2026-03-07 11:00",
        ai_prediction={"winner": "England", "confidence": 0.65, "key_factors": ["Swing conditions", "Strong bowling"]}
    )
]

# In-memory user storage (replace with database in production)
USERS_DB: Dict[str, User] = {
    "user_001": User(
        id="user_001",
        name="Harish Padiyar",
        email="harish@axzora.com",
        phone="+91 9876543210",
        wallet_balance=5000.0,
        hp_balance=5.0
    )
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_ollama_response(message: str, system_prompt: str = None) -> str:
    """Get response from Ollama AI"""
    if system_prompt is None:
        system_prompt = "You are Mr. Happy, the Digital CEO of AXZORA. Be helpful and concise."
    
    try:
        response = requests.post(
            "http://localhost:11434/api/chat",
            json={
                "model": "llama3.2:3b",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                "stream": False
            },
            timeout=60
        )
        
        if response.status_code == 200:
            return response.json().get("message", {}).get("content", "")
        return "I'm having trouble connecting to my AI backend. Please try again."
    except Exception as e:
        return f"Error: {str(e)}"

# ============================================================================
# HEALTH & STATUS
# ============================================================================

@app.get("/healthz")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}

@app.get("/api/status")
async def system_status():
    """System status"""
    return {
        "status": "operational",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "api": "ok",
            "ollama": "checking"
        }
    }

# ============================================================================
# AUTH ENDPOINTS
# ============================================================================

@app.post("/api/auth/login")
async def login(email: str, password: str):
    """User login"""
    # In production, verify password
    for user in USERS_DB.values():
        if user.email == email:
            return {
                "status": "success",
                "user": user.model_dump(),
                "token": f"jwt_token_{user.id}"
            }
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.get("/api/auth/me")
async def get_current_user(user_id: str = "user_001"):
    """Get current user"""
    if user_id in USERS_DB:
        return USERS_DB[user_id]
    raise HTTPException(status_code=404, detail="User not found")

# ============================================================================
# FLIGHT ENDPOINTS
# ============================================================================

@app.post("/api/flights/search")
async def search_flights(search: FlightSearch):
    """Search for flights"""
    # In production, call Amadeus API or similar
    return {
        "search_params": search.model_dump(),
        "flights": [f.model_dump() for f in SAMPLE_FLIGHTS],
        "total_results": len(SAMPLE_FLIGHTS)
    }

@app.get("/api/flights/{flight_id}")
async def get_flight(flight_id: str):
    """Get flight details"""
    for flight in SAMPLE_FLIGHTS:
        if flight.id == flight_id:
            return flight
    raise HTTPException(status_code=404, detail="Flight not found")

@app.post("/api/flights/book")
async def book_flight(flight_id: str, user_id: str = "user_001"):
    """Book a flight"""
    user = USERS_DB.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    for flight in SAMPLE_FLIGHTS:
        if flight.id == flight_id:
            if flight.price > user.wallet_balance:
                raise HTTPException(status_code=400, detail="Insufficient balance")
            
            # Deduct balance
            user.wallet_balance -= flight.price
            
            # Add HP reward (1% of booking)
            hp_earned = flight.price / 1000 * 0.01
            user.hp_balance += hp_earned
            
            return {
                "booking_id": f"BK{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                "flight": flight.model_dump(),
                "amount_paid": flight.price,
                "hp_earned": hp_earned,
                "remaining_balance": user.wallet_balance
            }
    
    raise HTTPException(status_code=404, detail="Flight not found")

# ============================================================================
# HOTEL ENDPOINTS
# ============================================================================

@app.post("/api/hotels/search")
async def search_hotels(search: HotelSearch):
    """Search for hotels"""
    return {
        "search_params": search.model_dump(),
        "hotels": [h.model_dump() for h in SAMPLE_HOTELS],
        "total_results": len(SAMPLE_HOTELS)
    }

@app.get("/api/hotels/{hotel_id}")
async def get_hotel(hotel_id: str):
    """Get hotel details"""
    for hotel in SAMPLE_HOTELS:
        if hotel.id == hotel_id:
            return hotel
    raise HTTPException(status_code=404, detail="Hotel not found")

# ============================================================================
# CRICKET ENDPOINTS
# ============================================================================

@app.get("/api/cricket/live")
async def get_live_scores():
    """Get live cricket scores"""
    return {
        "matches": [m.model_dump() for m in SAMPLE_MATCHES],
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/cricket/matches/{match_id}")
async def get_match_details(match_id: str):
    """Get match details"""
    for match in SAMPLE_MATCHES:
        if match.id == match_id:
            return match
    raise HTTPException(status_code=404, detail="Match not found")

@app.get("/api/cricket/predictions/{match_id}")
async def get_match_prediction(match_id: str):
    """Get AI prediction for a match"""
    for match in SAMPLE_MATCHES:
        if match.id == match_id:
            # Get fresh AI prediction
            prediction_prompt = f"""
            Predict the winner of this cricket match:
            {match.team1} vs {match.team2}
            Venue: {match.venue}
            Current score: {match.team1}: {match.score1}, {match.team2}: {match.score2}
            Status: {match.status}
            
            Provide a JSON response with: winner, confidence (0-1), and key_factors (list).
            """
            
            ai_response = get_ollama_response(prediction_prompt)
            
            return {
                "match_id": match_id,
                "prediction": match.ai_prediction,
                "ai_analysis": ai_response
            }
    
    raise HTTPException(status_code=404, detail="Match not found")

# ============================================================================
# WALLET ENDPOINTS
# ============================================================================

@app.get("/api/wallet/balance")
async def get_wallet_balance(user_id: str = "user_001"):
    """Get wallet balance"""
    user = USERS_DB.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "wallet_balance": user.wallet_balance,
        "hp_balance": user.hp_balance,
        "hp_value_inr": user.hp_balance * 1000,
        "total_balance": user.wallet_balance + (user.hp_balance * 1000)
    }

@app.post("/api/wallet/add")
async def add_money(amount: float, user_id: str = "user_001"):
    """Add money to wallet"""
    user = USERS_DB.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.wallet_balance += amount
    
    return {
        "status": "success",
        "added_amount": amount,
        "new_balance": user.wallet_balance
    }

@app.post("/api/wallet/hp/convert")
async def convert_hp(convert: HPConvert, user_id: str = "user_001"):
    """Convert between Happy Paisa and INR"""
    user = USERS_DB.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    rate = 1000  # 1 HP = ₹1000
    
    if convert.from_currency == "HP" and convert.to_currency == "INR":
        if user.hp_balance < convert.amount:
            raise HTTPException(status_code=400, detail="Insufficient HP balance")
        
        user.hp_balance -= convert.amount
        user.wallet_balance += convert.amount * rate
        
        return {
            "converted_amount": convert.amount * rate,
            "from": "HP",
            "to": "INR",
            "rate": rate,
            "new_hp_balance": user.hp_balance,
            "new_wallet_balance": user.wallet_balance
        }
    
    elif convert.from_currency == "INR" and convert.to_currency == "HP":
        if user.wallet_balance < convert.amount:
            raise HTTPException(status_code=400, detail="Insufficient wallet balance")
        
        hp_amount = convert.amount / rate
        user.wallet_balance -= convert.amount
        user.hp_balance += hp_amount
        
        return {
            "converted_amount": hp_amount,
            "from": "INR",
            "to": "HP",
            "rate": rate,
            "new_hp_balance": user.hp_balance,
            "new_wallet_balance": user.wallet_balance
        }
    
    raise HTTPException(status_code=400, detail="Invalid conversion")

@app.get("/api/wallet/transactions")
async def get_transactions(user_id: str = "user_001"):
    """Get transaction history"""
    # In production, fetch from database
    return {
        "transactions": [
            {
                "id": "TXN001",
                "type": "debit",
                "amount": 4500.0,
                "description": "Flight booking - AI-302",
                "timestamp": "2026-03-06T10:30:00"
            },
            {
                "id": "TXN002",
                "type": "credit",
                "amount": 0.5,
                "description": "HP Earned - Flight booking",
                "timestamp": "2026-03-06T10:30:00"
            }
        ]
    }

# ============================================================================
# AI CHAT ENDPOINT
# ============================================================================

@app.post("/api/ai/chat")
async def chat_with_ai(chat: ChatMessage):
    """Chat with Mr. Happy AI"""
    
    system_prompt = """You are Mr. Happy, the Digital CEO of AXZORA Digital Corporation.
    
You are an AI assistant for the AXZORA Super App. You can help users with:
- Flight bookings and search
- Hotel reservations
- Cricket scores and predictions
- Wallet operations and Happy Paisa
- General assistance

Happy Paisa (HP) is AXZORA's reward currency:
- 1 HP = ₹1,000 INR
- Users earn HP on bookings (1% of amount)
- HP can be used for payments and discounts

Be helpful, friendly, and concise. Always think step by step.
"""
    
    response = get_ollama_response(chat.message, system_prompt)
    
    return {
        "response": response,
        "agent": "Mr. Happy",
        "timestamp": datetime.utcnow().isoformat()
    }

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║        🚀 AXZORA SUPER APP API 🚀                            ║
║                                                              ║
║     Backend API for Super App                               ║
║                                                              ║
║     API Docs: http://localhost:8001/docs                     ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    uvicorn.run(app, host="0.0.0.0", port=8001)
