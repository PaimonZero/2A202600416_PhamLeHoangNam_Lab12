import re
from typing import Dict, List, Tuple
from langchain_core.tools import tool

# MOCK DATA - Mock travel system data

FLIGHTS_DB: Dict[Tuple[str, str], List[Dict[str, str | int]]] = {
    ("Hà Nội", "Đà Nẵng"): [
        {"airline": "Vietnam Airlines", "departure": "06:00", "arrival": "07:20", "price": 1450000, "class": "economy"},
        {"airline": "Vietnam Airlines", "departure": "14:00", "arrival": "15:20", "price": 2800000, "class": "business"},
        {"airline": "VietJet Air", "departure": "08:30", "arrival": "09:50", "price": 890000, "class": "economy"},
        {"airline": "Bamboo Airways", "departure": "11:00", "arrival": "12:20", "price": 1200000, "class": "economy"}
    ],
    ("Hà Nội", "Phú Quốc"): [
        {"airline": "Vietnam Airlines", "departure": "07:00", "arrival": "09:15", "price": 2100000, "class": "economy"},
        {"airline": "VietJet Air", "departure": "10:00", "arrival": "12:15", "price": 1350000, "class": "economy"},
        {"airline": "VietJet Air", "departure": "16:00", "arrival": "18:15", "price": 1100000, "class": "economy"}
    ],
    ("Hà Nội", "Hồ Chí Minh"): [
        {"airline": "Vietnam Airlines", "departure": "06:00", "arrival": "08:10", "price": 1600000, "class": "economy"},
        {"airline": "VietJet Air", "departure": "07:30", "arrival": "09:40", "price": 950000, "class": "economy"},
        {"airline": "Bamboo Airways", "departure": "12:00", "arrival": "14:10", "price": 1300000, "class": "economy"},
        {"airline": "Vietnam Airlines", "departure": "18:00", "arrival": "20:10", "price": 3200000, "class": "business"}
    ],
    ("Hồ Chí Minh", "Đà Nẵng"): [
        {"airline": "Vietnam Airlines", "departure": "09:00", "arrival": "10:20", "price": 1300000, "class": "economy"},
        {"airline": "VietJet Air", "departure": "13:00", "arrival": "14:20", "price": 780000, "class": "economy"}
    ],
    ("Hồ Chí Minh", "Phú Quốc"): [
        {"airline": "Vietnam Airlines", "departure": "08:00", "arrival": "09:00", "price": 1100000, "class": "economy"},
        {"airline": "VietJet Air", "departure": "15:00", "arrival": "16:00", "price": 650000, "class": "economy"}
    ]
}

HOTELS_DB: Dict[str, List[Dict[str, str | int | float]]] = {
    "Đà Nẵng": [
        {"name": "Mường Thanh Luxury", "stars": 5, "price_per_night": 1800000, "area": "Mỹ Khê", "rating": 4.5},
        {"name": "Sala Danang Beach", "stars": 4, "price_per_night": 1200000, "area": "Mỹ Khê", "rating": 4.3},
        {"name": "Fivitel Danang", "stars": 3, "price_per_night": 650000, "area": "Sơn Trà", "rating": 4.1},
        {"name": "Memory Hostel", "stars": 2, "price_per_night": 250000, "area": "Hải Châu", "rating": 4.6},
        {"name": "Christina's Homestay", "stars": 2, "price_per_night": 350000, "area": "An Thượng", "rating": 4.7}
    ],
    "Phú Quốc": [
        {"name": "Vinpearl Resort", "stars": 5, "price_per_night": 3500000, "area": "Bãi Dài", "rating": 4.4},
        {"name": "Sol by Meliá", "stars": 4, "price_per_night": 1500000, "area": "Bãi Trường", "rating": 4.2},
        {"name": "Lahana Resort", "stars": 3, "price_per_night": 800000, "area": "Dương Đông", "rating": 4.0},
        {"name": "9Station Hostel", "stars": 2, "price_per_night": 200000, "area": "Dương Đông", "rating": 4.5}
    ],
    "Hồ Chí Minh": [
        {"name": "Rex Hotel", "stars": 5, "price_per_night": 2800000, "area": "Quận 1", "rating": 4.3},
        {"name": "Liberty Central", "stars": 4, "price_per_night": 1400000, "area": "Quận 1", "rating": 4.1},
        {"name": "Cochin Zen Hotel", "stars": 3, "price_per_night": 550000, "area": "Quận 3", "rating": 4.4},
        {"name": "The Common Room", "stars": 2, "price_per_night": 180000, "area": "Quận 1", "rating": 4.6}
    ]
}

@tool
def search_flights(origin: str, destination: str) -> str:
    """Search for flights between two cities."""
    try:
        key = (origin, destination)
        flights = FLIGHTS_DB.get(key)
        
        # Check reverse direction as fallback
        if not flights:
            flights = FLIGHTS_DB.get((destination, origin))
            
        if not flights:
            return f"Không tìm thấy chuyến bay giữa {origin} và {destination}."
        
        res = f"Chuyến bay giữa {origin} và {destination}:\n"
        for flight in flights:
            res += f"- {flight['airline']} ({flight['class']}): {flight['departure']} - {flight['arrival']}, Giá: {flight['price']} VND\n"
        return res
        
    except Exception as e:
        return f"[Lỗi] Cannot finish searching flights: {e}"

@tool
def search_hotels(city: str, max_price_per_night: int = 99999999) -> str:
    """Search for hotels in a city, filtered by max price and sorted by rating (desc)."""
    try:
        hotels = HOTELS_DB.get(city, [])
        if not hotels:
            return f"Không có dữ liệu khách sạn tại thành phố {city}."
        
        # Filter matching price requirements and sort securely based on descending ratings
        filtered = sorted([h for h in hotels if int(h['price_per_night']) <= max_price_per_night], 
                          key=lambda x: float(x['rating']), 
                          reverse=True)

        if not filtered:
            return f"Không tìm thấy khách sạn nào tại {city} với mức giá tối đa là {max_price_per_night} VND."
        
        # Append formatted hotel strings
        return "\n".join([f"- {h['name']} ({h['stars']}*): {int(h['price_per_night']):,} VNĐ/đêm - Rating: {h['rating']}" 
                          for h in filtered])
                          
    except Exception as e:
        return f"[Lỗi] Cannot complete hotel search: {e}"

@tool
def calculate_budget(total_budget: int, expenses: str) -> str:
    """
    Calculate the remaining budget after deducting travel expenses.
    Expected format for expenses: "item: numeric_cost, ..." example -> "vé máy bay: 3000000, khách sạn: 1500000"
    """
    try:
        # Try to parse string strictly separating by commas and pulling numeric blocks after colons
        items = [e.split(':') for e in expenses.split(',')]
        total_spent = sum(int(re.sub(r'[^\d]', '', i[-1])) for i in items if i)
        
        remaining = total_budget - total_spent
        
        if remaining >= 0:
            status = f"Còn lại: {remaining:,} VNĐ" 
        else:
            status = f"Vượt ngân sách {-remaining:,} VNĐ!"
            
        return f"Tổng chi: {total_spent:,} VNĐ. {status}"
        
    except Exception:
        # Provide instructional feedback gracefully without failing the bot
        return "Lỗi định dạng tham số expenses. Tính toán thất bại. Vui lòng định dạng lại theo cấu trúc 'tên mục: số tiền mua'."
