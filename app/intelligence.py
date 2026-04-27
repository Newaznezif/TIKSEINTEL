import os
import aiohttp
from dotenv import load_dotenv

load_dotenv()

VT_API_KEY = os.getenv("VIRUSTOTAL_API_KEY")
ABUSEIPDB_API_KEY = os.getenv("ABUSEIPDB_API_KEY")

async def get_vt_data(ip: str):
    if not VT_API_KEY or VT_API_KEY == "your_vt_api_key":
        return {"malicious": 0, "suspicious": 0, "harmless": 0}
    
    url = f"https://www.virustotal.com/api/v3/ip_addresses/{ip}"
    headers = {"x-apikey": VT_API_KEY}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                stats = data.get("data", {}).get("attributes", {}).get("last_analysis_stats", {})
                return stats
            return {"malicious": 0, "suspicious": 0, "harmless": 0}

async def get_abuseipdb_data(ip: str):
    if not ABUSEIPDB_API_KEY or ABUSEIPDB_API_KEY == "your_abuseipdb_api_key":
        return {"abuseConfidenceScore": 0, "totalReports": 0}
        
    url = f"https://api.abuseipdb.com/api/v2/check"
    headers = {
        "Key": ABUSEIPDB_API_KEY,
        "Accept": "application/json"
    }
    params = {"ipAddress": ip, "maxAgeInDays": 90}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, params=params) as response:
            if response.status == 200:
                data = await response.json()
                return data.get("data", {})
            return {"abuseConfidenceScore": 0, "totalReports": 0}

async def synthesize_intelligence(ip: str):
    vt_data = await get_vt_data(ip)
    abuse_data = await get_abuseipdb_data(ip)
    
    malicious = vt_data.get("malicious", 0)
    score = abuse_data.get("abuseConfidenceScore", 0)
    
    impact = "Low"
    recommendation = "No immediate action required. Monitor for anomalies."
    description = f"The IP {ip} shows no significant malicious activity across verified sources."
    
    if malicious > 5 or score > 80:
        impact = "Critical"
        recommendation = "Immediate block recommended at the firewall/WAF level."
        description = f"The IP {ip} is heavily reported as malicious, indicating an active threat or botnet node."
    elif malicious > 0 or score > 30:
        impact = "Medium"
        recommendation = "Monitor for lateral movement or repeated scanning. Consider temporary ban if behavior persists."
        description = f"The IP {ip} has some suspicious reports, possibly indicating scanning or proxy activity."
        
    return {
        "description": description,
        "impact": impact,
        "recommendation": recommendation,
        "vt_stats": vt_data,
        "abuseipdb_score": score
    }
