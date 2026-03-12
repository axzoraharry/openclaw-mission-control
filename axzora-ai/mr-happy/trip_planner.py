#!/usr/bin/env python3
"""
Mr Happy Trip Planner - AI-powered travel planning
Uses the Axzora Super-Aggregator API to plan complete trips
"""

import asyncio
import httpx
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

OLLAMA_URL = "http://localhost:11434"
GATEWAY_URL = "http://localhost:8080"
MODEL = "llama3.2:3b"


@dataclass
class TripPlan:
    """Complete trip plan"""
    destination: str
    total_budget: float
    flights: List[Dict]
    hotels: List[Dict]
    events: List[Dict]
    restaurants: List[Dict]
    total_cost: float
    happy_paisa_earned: float
    itinerary: str


class MrHappyTripPlanner:
    """AI-powered trip planner using Axzora Super-Aggregator"""
    
    def __init__(self):
        self.conversation_history = []
    
    async def plan_trip(self, query: str) -> TripPlan:
        """
        Main entry point. User says:
        "Plan a Goa trip under ₹25k"
        Returns a complete trip plan.
        """
        print(f"\n🧠 Mr Happy planning: {query}")
        
        # Extract trip details using LLM
        trip_details = await self._extract_trip_details(query)
        print(f"   Destination: {trip_details.get('destination')}")
        print(f"   Budget: ₹{trip_details.get('budget')}")
        print(f"   Dates: {trip_details.get('dates')}")
        
        # Search all services in parallel
        results = await self._search_all_services(trip_details)
        
        # Select best options
        selected = self._select_best_options(results, trip_details["budget"])
        
        # Generate itinerary
        itinerary = await self._generate_itinerary(selected, trip_details)
        
        # Calculate rewards
        rewards = self._calculate_total_rewards(selected)
        
        return TripPlan(
            destination=trip_details["destination"],
            total_budget=trip_details["budget"],
            flights=selected.get("flights", []),
            hotels=selected.get("hotels", []),
            events=selected.get("events", []),
            restaurants=selected.get("restaurants", []),
            total_cost=selected.get("total_cost", 0),
            happy_paisa_earned=rewards,
            itinerary=itinerary,
        )
    
    async def _extract_trip_details(self, query: str) -> Dict:
        """Use LLM to extract trip details from natural language"""
        prompt = f"""Extract trip details from this request. Return JSON only:
"{query}"

Return format:
{{
    "destination": "city name",
    "budget": number (in INR, just the number),
    "dates": {{
        "check_in": "YYYY-MM-DD",
        "check_out": "YYYY-MM-DD"
    }},
    "travelers": number,
    "preferences": ["list", "of", "preferences"]
}}

If dates not specified, use next weekend. If budget not specified, use 20000.
"""
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{OLLAMA_URL}/api/generate",
                    json={"model": MODEL, "prompt": prompt, "stream": False, "format": "json"},
                    timeout=30.0
                )
                if response.status_code == 200:
                    result = response.json().get("response", "{}")
                    details = json.loads(result)
                    
                    # Defaults
                    if not details.get("destination"):
                        details["destination"] = "Goa"
                    if not details.get("budget"):
                        details["budget"] = 20000
                    if not details.get("dates"):
                        next_sat = datetime.now() + timedelta(days=(5 - datetime.now().weekday()) % 7)
                        details["dates"] = {
                            "check_in": next_sat.strftime("%Y-%m-%d"),
                            "check_out": (next_sat + timedelta(days=2)).strftime("%Y-%m-%d"),
                        }
                    
                    return details
        except Exception as e:
            print(f"[LLM extraction error: {e}]")
        
        # Fallback defaults
        return {
            "destination": "Goa",
            "budget": 20000,
            "dates": {
                "check_in": "2026-03-21",
                "check_out": "2026-03-23",
            },
            "travelers": 1,
            "preferences": [],
        }
    
    async def _search_all_services(self, trip_details: Dict) -> Dict:
        """Search all services in parallel"""
        destination = trip_details["destination"]
        budget = trip_details["budget"]
        dates = trip_details.get("dates", {})
        
        async with httpx.AsyncClient() as client:
            # Parallel searches
            flights_task = client.get(
                f"{GATEWAY_URL}/api/travel/flights",
                params={"origin": "DEL", "destination": "GOI", "date": dates.get("check_in", "2026-03-21"), "budget": budget * 0.4}
            )
            hotels_task = client.get(
                f"{GATEWAY_URL}/api/travel/hotels",
                params={"city": destination, "check_in": dates.get("check_in", "2026-03-21"), "check_out": dates.get("check_out", "2026-03-23"), "budget": budget * 0.4}
            )
            events_task = client.get(
                f"{GATEWAY_URL}/api/events/search",
                params={"q": destination, "city": destination}
            )
            restaurants_task = client.get(
                f"{GATEWAY_URL}/api/food/restaurants",
                params={"q": destination}
            )
            
            responses = await asyncio.gather(flights_task, hotels_task, events_task, restaurants_task, return_exceptions=True)
        
        results = {"flights": [], "hotels": [], "events": [], "restaurants": []}
        
        for i, (key, response) in enumerate(zip(["flights", "hotels", "events", "restaurants"], responses)):
            if isinstance(response, httpx.Response) and response.status_code == 200:
                data = response.json()
                results[key] = data.get("results", [])
        
        return results
    
    def _select_best_options(self, results: Dict, budget: float) -> Dict:
        """Select best options within budget"""
        selected = {
            "flights": [],
            "hotels": [],
            "events": [],
            "restaurants": [],
            "total_cost": 0,
        }
        
        remaining_budget = budget
        
        # Select cheapest flight
        if results["flights"]:
            flight = min(results["flights"], key=lambda x: x.get("price", float("inf")))
            if flight.get("price", 0) <= remaining_budget * 0.4:
                selected["flights"] = [flight]
                selected["total_cost"] += flight.get("price", 0)
                remaining_budget -= flight.get("price", 0)
        
        # Select best value hotel
        if results["hotels"]:
            hotel = min(results["hotels"], key=lambda x: x.get("total_price", float("inf")))
            if hotel.get("total_price", 0) <= remaining_budget * 0.6:
                selected["hotels"] = [hotel]
                selected["total_cost"] += hotel.get("total_price", 0)
                remaining_budget -= hotel.get("total_price", 0)
        
        # Add top events and restaurants
        selected["events"] = results["events"][:3]
        selected["restaurants"] = results["restaurants"][:3]
        
        return selected
    
    async def _generate_itinerary(self, selected: Dict, trip_details: Dict) -> str:
        """Generate day-by-day itinerary using LLM"""
        prompt = f"""Create a fun, concise 2-day itinerary for {trip_details['destination']}.

Available:
- Flight: {selected['flights'][0] if selected['flights'] else 'Not selected'}
- Hotel: {selected['hotels'][0] if selected['hotels'] else 'Not selected'}
- Events: {selected['events']}
- Restaurants: {selected['restaurants']}

Budget: ₹{trip_details['budget']}
Total estimated cost: ₹{selected['total_cost']}

Format as a brief day-by-day plan with times. Keep it under 200 words.
"""
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{OLLAMA_URL}/api/generate",
                    json={"model": MODEL, "prompt": prompt, "stream": False},
                    timeout=30.0
                )
                if response.status_code == 200:
                    return response.json().get("response", "Itinerary generation failed")
        except Exception as e:
            print(f"[Itinerary error: {e}]")
        
        return "Itinerary will be generated based on your preferences."
    
    def _calculate_total_rewards(self, selected: Dict) -> float:
        """Calculate total Happy Paisa rewards"""
        rewards = 0
        
        # Flight booking = 50 HP
        if selected["flights"]:
            rewards += 50
        
        # Hotel booking = 40 HP
        if selected["hotels"]:
            rewards += 40
        
        # Events = 20 HP each
        rewards += len(selected["events"]) * 20
        
        return rewards
    
    def format_plan(self, plan: TripPlan) -> str:
        """Format trip plan for display"""
        output = f"""
╔══════════════════════════════════════════════════════════════════╗
║           🌴 MR HAPPY TRIP PLAN: {plan.destination.upper():^20}          ║
╚══════════════════════════════════════════════════════════════════╝

💰 BUDGET: ₹{plan.total_budget:,}
💵 ESTIMATED COST: ₹{plan.total_cost:,}
🪙 HAPPY PAISA EARNED: {plan.happy_paisa_earned} HP

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✈️  FLIGHTS
"""
        for flight in plan.flights:
            output += f"    {flight.get('airline', 'Airline')} - ₹{flight.get('price', 0):,}\n"
            output += f"    {flight.get('departure', {}).get('airport', '')} → {flight.get('arrival', {}).get('airport', '')}\n"
        
        output += "\n🏨 HOTELS\n"
        for hotel in plan.hotels:
            output += f"    {hotel.get('name', 'Hotel')} - ₹{hotel.get('total_price', 0):,}/stay\n"
            output += f"    Rating: {hotel.get('rating', 'N/A')} ⭐ | Amenities: {', '.join(hotel.get('amenities', []))}\n"
        
        output += "\n🎬 EVENTS\n"
        for event in plan.events:
            output += f"    {event.get('name', 'Event')} - ₹{event.get('price', 0)}\n"
        
        output += "\n🍽️ RESTAURANTS\n"
        for rest in plan.restaurants:
            output += f"    {rest.get('name', 'Restaurant')} - {rest.get('cuisine', 'Cuisine')}\n"
            output += f"    Rating: {rest.get('rating', 'N/A')} ⭐ | Cost for two: ₹{rest.get('cost_for_two', 0)}\n"
        
        output += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📅 ITINERARY
{plan.itinerary}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎉 You'll earn {plan.happy_paisa_earned} Happy Paisa on this trip!
   Contract: 0xf99ae6F3234b5E7f247BD12A8a59668Aa479E560

╚══════════════════════════════════════════════════════════════════╝
"""
        return output


async def main():
    """Interactive trip planner"""
    print("""
╔══════════════════════════════════════════════════════════════════╗
║           MR HAPPY AI TRIP PLANNER                               ║
║           Powered by Axzora Super-Aggregator                     ║
╚══════════════════════════════════════════════════════════════════╝

Examples:
  - "Plan a Goa trip under ₹25k"
  - "Weekend trip to Jaipur, budget 15k"
  - "4-day Kerala trip for 2 people under 50k"

Type 'quit' to exit.
""")
    
    planner = MrHappyTripPlanner()
    
    while True:
        try:
            query = input("\n🧳 Enter your trip request: ").strip()
            if query.lower() in ("quit", "exit", "q"):
                print("\n👋 Happy travels! Goodbye!")
                break
            
            if not query:
                continue
            
            plan = await planner.plan_trip(query)
            print(planner.format_plan(plan))
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
