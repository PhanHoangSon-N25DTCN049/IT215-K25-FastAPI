raw_stations = [ 
{"station_code": "S301", "type": "fast", "price_per_kwh": 5000, "status": "available"}, 
{"station_code": " s101 ", "type": "normal", "price_per_kwh": 3000, "status": "available"}, 
{"station_code": "S202", "type": "ultra_fast", "price_per_kwh": 7000, "status": 
"occupied"}, 
{"station_code": "S102", "type": "normal", "price_per_kwh": 3200, "status": 
"maintenance"}, 
{"station_code": "S302", "type": "fast", "price_per_kwh": 5500, "status": "available"} 
] 


def clean_and_validate_stations(station:list):
    for s in range(0,len(station),1):
        clean_code = str(station[s]["station_code"]).strip().upper()
        station[s]["station_code"] = clean_code
        if not clean_code.startswith("S") or not clean_code[1:].isdigit():
            station.remove(station[s])
      
clean_and_validate_stations(raw_stations)      

def search_stations(price_per_kwh: int, status: str = None):
    list_station = list(raw_stations)
 
    list_station = [s for s in list_station if s["price_per_kwh"] <= price_per_kwh]
    if status:
        list_station = [s for s in list_station if s["status"] == status]
    
    return list_station


    
def sort_stations_by_price_desc(stations: list):
    for i in range(0, len(stations), 1):
        for j in range(i+1, len(stations), 1):
            if stations[i]["price_per_kwh"] < stations[j]["price_per_kwh"]:
                stations[i], stations[j] = stations[j], stations[i]
                
sort_stations_by_price_desc(raw_stations)
