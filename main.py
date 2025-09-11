from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List, Dict, Optional
import uvicorn
import json
import re

app = FastAPI(title="Backyard Monsters Upgrade Tracker")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

def parse_time_to_seconds(time_str):
    """Parse time string like '1d 12h 30m 45s' to total seconds"""
    if not time_str or time_str == "Instant":
        return 0
    
    total_seconds = 0
    
    # Extract days
    days_match = re.search(r'(\d+)d', time_str)
    if days_match:
        total_seconds += int(days_match.group(1)) * 24 * 3600
    
    # Extract hours
    hours_match = re.search(r'(\d+)h', time_str)
    if hours_match:
        total_seconds += int(hours_match.group(1)) * 3600
    
    # Extract minutes
    minutes_match = re.search(r'(\d+)m', time_str)
    if minutes_match:
        total_seconds += int(minutes_match.group(1)) * 60
    
    # Extract seconds
    seconds_match = re.search(r'(\d+)s', time_str)
    if seconds_match:
        total_seconds += int(seconds_match.group(1))
    
    return total_seconds

def format_time_from_seconds(total_seconds):
    """Format seconds to display highest 2 time units"""
    if total_seconds == 0:
        return "Instant"
    
    days = total_seconds // (24 * 3600)
    hours = (total_seconds % (24 * 3600)) // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    
    # Collect non-zero units
    units = []
    if days > 0:
        units.append(f"{days}d")
    if hours > 0:
        units.append(f"{hours}h")
    if minutes > 0:
        units.append(f"{minutes}m")
    if seconds > 0:
        units.append(f"{seconds}s")
    
    # Return highest 2 units, or at least 1 unit
    if len(units) >= 2:
        return " ".join(units[:2])
    elif len(units) == 1:
        return units[0]
    else:
        return "0s"

def get_town_hall_image(level):
    """Get town hall image URL based on level"""
    return f"/static/images/town_hall_level_{level}.png"

def load_game_data():
    with open("game_data.json", "r") as f:
        return json.load(f)

def load_user_data():
    with open("user_data.json", "r") as f:
        return json.load(f)

def save_user_data(data):
    with open("user_data.json", "w") as f:
        json.dump(data, f, indent=2)

def get_building_with_progress(building_name, building_id, user_buildings, game_data):
    # Find user progress for this building
    user_building = next((b for b in user_buildings if b["id"] == building_id), None)
    if not user_building:
        return None
    
    # Get game data for this building type
    game_building = game_data["buildings"].get(building_name)
    if not game_building:
        return None
    
    current_level = user_building["current_level"]
    max_level = game_building["max_level"]
    
    # Get next upgrade cost if not maxed
    next_upgrade = None
    if current_level < max_level:
        next_upgrade = game_building["upgrade_costs"][current_level]  # 0-indexed
    
    return {
        "id": building_id,
        "name": building_name,
        "category": game_building["category"],
        "current_level": current_level,
        "max_level": max_level,
        "image_url": game_building["image_url"],
        "next_upgrade": next_upgrade,
        "all_upgrades": game_building["upgrade_costs"]
    }

def get_monster_with_progress(monster_name, monster_id, user_monsters, game_data):
    user_monster = next((m for m in user_monsters if m["id"] == monster_id), None)
    if not user_monster:
        return None
    
    game_monster = game_data["monsters"].get(monster_name)
    if not game_monster:
        return None
    
    current_level = user_monster["current_level"]
    max_level = game_monster["max_level"]
    unlocked = user_monster["unlocked"]
    
    next_upgrade = None
    if not unlocked:
        next_upgrade = {"putty": game_monster["unlock_cost_putty"], "time": "Instant"}
    elif current_level < max_level:
        next_upgrade = game_monster["upgrade_costs"][current_level]
    
    return {
        "id": monster_id,
        "name": monster_name,
        "category": game_monster["category"],
        "current_level": current_level,
        "max_level": max_level,
        "unlocked": unlocked,
        "unlock_cost_putty": game_monster["unlock_cost_putty"],
        "image_url": game_monster["image_url"],
        "next_upgrade": next_upgrade,
        "all_upgrades": game_monster["upgrade_costs"]
    }

def get_champion_with_progress(champion_name, champion_id, user_champions, game_data):
    user_champion = next((c for c in user_champions if c["id"] == champion_id), None)
    if not user_champion:
        return None
    
    game_champion = game_data["champions"].get(champion_name)
    if not game_champion:
        return None
    
    current_level = user_champion["current_level"]
    max_level = game_champion["max_level"]
    
    next_level_requirement = None
    if current_level < max_level:
        next_level_requirement = game_champion["level_requirements"][current_level]
    
    # Calculate total goo cost for next level
    next_feeding_goo_cost = 0
    if next_level_requirement:
        for monster in next_level_requirement["monsters_per_feeding"]:
            next_feeding_goo_cost += monster["goo_cost"] * monster["count"]
        next_feeding_goo_cost *= next_level_requirement["feedings_needed"]
    
    # Calculate remaining upgrades with goo costs
    remaining_upgrades = []
    total_remaining_goo = 0
    
    for level in range(current_level, max_level):
        if level < len(game_champion["level_requirements"]):
            level_req = game_champion["level_requirements"][level]
            level_goo_cost = 0
            for monster in level_req["monsters_per_feeding"]:
                level_goo_cost += monster["goo_cost"] * monster["count"]
            level_goo_cost *= level_req["feedings_needed"]
            
            remaining_upgrades.append({
                "level": level + 1,
                "feedings_needed": level_req["feedings_needed"],
                "goo_cost": level_goo_cost,
                "monsters_per_feeding": level_req["monsters_per_feeding"]
            })
            total_remaining_goo += level_goo_cost
    
    return {
        "id": champion_id,
        "name": champion_name,
        "current_level": current_level,
        "max_level": max_level,
        "image_url": game_champion["image_url"],
        "feeding_cooldown": game_champion["feeding_cooldown"],
        "next_level_requirement": next_level_requirement,
        "next_feeding_goo_cost": next_feeding_goo_cost,
        "remaining_upgrades": remaining_upgrades,
        "total_remaining_goo": total_remaining_goo
    }

# Routes
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    user_data = load_user_data()
    game_data = load_game_data()
    
    # Get town hall upgrade cost
    th_level = user_data["profile"]["town_hall_level"]
    th_upgrade = None
    if th_level < game_data["town_hall"]["max_level"]:
        th_upgrade = game_data["town_hall"]["upgrade_costs"][th_level]
    
    user_profile = {
        "username": user_data["profile"]["username"],
        "town_hall_level": th_level,
        "town_hall_image": get_town_hall_image(th_level),
        "th_upgrade": th_upgrade,
        "th_upgrade_cost_twigs": th_upgrade["twigs"] if th_upgrade else 0,
        "th_upgrade_cost_pebbles": th_upgrade["pebbles"] if th_upgrade else 0,
        "th_upgrade_time": format_time_from_seconds(parse_time_to_seconds(th_upgrade["time"])) if th_upgrade else "Max Level"
    }
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "user": user_profile
    })

@app.get("/api/buildings/{category}")
async def get_buildings(category: str, request: Request):
    user_data = load_user_data()
    game_data = load_game_data()
    
    # Get all buildings for this category
    buildings_with_progress = []
    for user_building in user_data["buildings"]:
        building_data = get_building_with_progress(
            user_building["name"], 
            user_building["id"], 
            user_data["buildings"], 
            game_data
        )
        if building_data and building_data["category"] == category:
            buildings_with_progress.append(building_data)
    
    # Group by building name and calculate totals
    grouped_buildings = {}
    category_totals = {"twigs": 0, "pebbles": 0, "putty": 0, "gems": 0}
    
    for building in buildings_with_progress:
        building_name = building["name"]
        if building_name not in grouped_buildings:
            grouped_buildings[building_name] = {
                "instances": [],
                "total_twigs": 0,
                "total_pebbles": 0,
                "total_time_seconds": 0,
                "image_url": building["image_url"]
            }
        
        # Calculate remaining upgrades for this building instance
        remaining_upgrades = []
        instance_total_twigs = 0
        instance_total_pebbles = 0
        instance_total_seconds = 0
        
        for level in range(building["current_level"], building["max_level"]):
            if level < len(building["all_upgrades"]):
                upgrade = building["all_upgrades"][level]
                formatted_time = format_time_from_seconds(parse_time_to_seconds(upgrade["time"]))
                remaining_upgrades.append({
                    "level": level + 1,
                    "twigs": upgrade["twigs"],
                    "pebbles": upgrade["pebbles"],
                    "time": formatted_time
                })
                instance_total_twigs += upgrade["twigs"]
                instance_total_pebbles += upgrade["pebbles"]
                instance_total_seconds += parse_time_to_seconds(upgrade["time"])
        
        # Add this instance
        building_instance = {
            "id": building["id"],
            "current_level": building["current_level"],
            "max_level": building["max_level"],
            "remaining_upgrades": remaining_upgrades[:3],  # Show first 3
            "more_upgrades": max(0, len(remaining_upgrades) - 3),
            "instance_total_twigs": instance_total_twigs,
            "instance_total_pebbles": instance_total_pebbles,
            "instance_total_time": format_time_from_seconds(instance_total_seconds)
        }
        
        grouped_buildings[building_name]["instances"].append(building_instance)
        grouped_buildings[building_name]["total_twigs"] += instance_total_twigs
        grouped_buildings[building_name]["total_pebbles"] += instance_total_pebbles
        grouped_buildings[building_name]["total_time_seconds"] += instance_total_seconds
        
        # Add to category totals
        category_totals["twigs"] += instance_total_twigs
        category_totals["pebbles"] += instance_total_pebbles
    
    for building_name in grouped_buildings:
        grouped_buildings[building_name]["total_time"] = format_time_from_seconds(
            grouped_buildings[building_name]["total_time_seconds"]
        )
    
    return templates.TemplateResponse("buildings_content.html", {
        "request": request,
        "grouped_buildings": grouped_buildings,
        "category": category,
        "category_totals": category_totals
    })

@app.get("/api/monsters/{category}")
async def get_monsters(category: str, request: Request):
    user_data = load_user_data()
    game_data = load_game_data()
    
    monsters_with_progress = []
    for user_monster in user_data["monsters"]:
        monster_data = get_monster_with_progress(
            user_monster["name"],
            user_monster["id"],
            user_data["monsters"],
            game_data
        )
        if monster_data and monster_data["category"] == category:
            monsters_with_progress.append(monster_data)
    
    return templates.TemplateResponse("monsters_content.html", {
        "request": request,
        "monsters": monsters_with_progress,
        "category": category
    })

@app.get("/api/champions")
async def get_champions(request: Request):
    user_data = load_user_data()
    game_data = load_game_data()
    
    champions_with_progress = []
    for user_champion in user_data["champions"]:
        champion_data = get_champion_with_progress(
            user_champion["name"],
            user_champion["id"],
            user_data["champions"],
            game_data
        )
        if champion_data:
            champions_with_progress.append(champion_data)
    
    return templates.TemplateResponse("champions_content.html", {
        "request": request,
        "champions": champions_with_progress
    })

@app.get("/api/stats")
async def get_stats(request: Request):
    user_data = load_user_data()
    game_data = load_game_data()
    
    # Calculate stats using the new data structure
    total_buildings = len(user_data["buildings"])
    unlocked_monsters = len([m for m in user_data["monsters"] if m["unlocked"]])
    total_champions = len(user_data["champions"])
    
    # Calculate total costs needed for upgrades
    total_twigs = 0
    total_pebbles = 0
    total_putty = 0
    
    # Buildings
    for user_building in user_data["buildings"]:
        building_data = get_building_with_progress(
            user_building["name"], 
            user_building["id"], 
            user_data["buildings"], 
            game_data
        )
        if building_data:
            for i in range(building_data["current_level"], building_data["max_level"]):
                if i < len(building_data["all_upgrades"]):
                    upgrade = building_data["all_upgrades"][i]
                    total_twigs += upgrade["twigs"]
                    total_pebbles += upgrade["pebbles"]
    
    # Monsters
    for user_monster in user_data["monsters"]:
        monster_data = get_monster_with_progress(
            user_monster["name"],
            user_monster["id"],
            user_data["monsters"],
            game_data
        )
        if monster_data:
            if not monster_data["unlocked"]:
                total_putty += monster_data["unlock_cost_putty"]
            else:
                for i in range(monster_data["current_level"], monster_data["max_level"]):
                    if i < len(monster_data["all_upgrades"]):
                        upgrade = monster_data["all_upgrades"][i]
                        total_putty += upgrade["putty"]
    
    stats_data = {
        "total_buildings": total_buildings,
        "total_monsters": unlocked_monsters,
        "total_champions": total_champions,
        "town_hall_level": user_data["profile"]["town_hall_level"],
        "total_twigs": total_twigs,
        "total_pebbles": total_pebbles,
        "total_putty": total_putty,
        "unlocked_monsters": unlocked_monsters,
        "locked_monsters": len([m for m in user_data["monsters"] if not m["unlocked"]])
    }
    
    return templates.TemplateResponse("stats_content.html", {
        "request": request,
        "stats": stats_data
    })

@app.post("/api/upgrade/{item_type}/{item_id}")
async def upgrade_item(item_type: str, item_id: str, request: Request):
    user_data = load_user_data()
    
    if item_type == "building":
        for building in user_data["buildings"]:
            if building["id"] == item_id:
                game_data = load_game_data()
                game_building = game_data["buildings"].get(building["name"])
                if game_building and building["current_level"] < game_building["max_level"]:
                    building["current_level"] += 1
                    save_user_data(user_data)
                    return templates.TemplateResponse("upgrade_success.html", {
                        "request": request,
                        "item_name": building["name"],
                        "new_level": building["current_level"],
                        "item_type": "building"
                    })
    
    elif item_type == "monster":
        for monster in user_data["monsters"]:
            if monster["id"] == item_id:
                game_data = load_game_data()
                game_monster = game_data["monsters"].get(monster["name"])
                if game_monster:
                    if not monster["unlocked"]:
                        monster["unlocked"] = True
                        save_user_data(user_data)
                        return templates.TemplateResponse("upgrade_success.html", {
                            "request": request,
                            "item_name": monster["name"],
                            "new_level": "UNLOCKED",
                            "item_type": "monster"
                        })
                    elif monster["current_level"] < game_monster["max_level"]:
                        monster["current_level"] += 1
                        save_user_data(user_data)
                        return templates.TemplateResponse("upgrade_success.html", {
                            "request": request,
                            "item_name": monster["name"],
                            "new_level": monster["current_level"],
                            "item_type": "monster"
                        })
    
    return templates.TemplateResponse("upgrade_error.html", {
        "request": request,
        "message": "Upgrade failed"
    })

@app.post("/api/feed/{champion_id}")
async def feed_champion(champion_id: str, request: Request):
    user_data = load_user_data()
    
    for champion in user_data["champions"]:
        if champion["id"] == champion_id:
            game_data = load_game_data()
            game_champion = game_data["champions"].get(champion["name"])
            if game_champion and champion["current_level"] < game_champion["max_level"]:
                champion["current_level"] += 1
                save_user_data(user_data)
                return templates.TemplateResponse("upgrade_success.html", {
                    "request": request,
                    "item_name": champion["name"],
                    "new_level": champion["current_level"],
                    "item_type": "champion"
                })
    
    return templates.TemplateResponse("upgrade_error.html", {
        "request": request,
        "message": "Feeding failed"
    })

@app.get("/api/sidebar-totals/{category}")
async def get_sidebar_totals(category: str, request: Request):
    user_data = load_user_data()
    game_data = load_game_data()
    
    # Calculate totals for this category
    total_twigs = 0
    total_pebbles = 0
    total_putty = 0
    total_goo = 0
    total_gems = 0
    total_seconds = 0
    
    if category in ["resources", "buildings", "defensive"]:
        # Building categories
        for user_building in user_data["buildings"]:
            building_data = get_building_with_progress(
                user_building["name"], 
                user_building["id"], 
                user_data["buildings"], 
                game_data
            )
            if building_data and building_data["category"] == category:
                for i in range(building_data["current_level"], building_data["max_level"]):
                    if i < len(building_data["all_upgrades"]):
                        upgrade = building_data["all_upgrades"][i]
                        total_twigs += upgrade["twigs"]
                        total_pebbles += upgrade["pebbles"]
                        total_seconds += parse_time_to_seconds(upgrade["time"])
    
    elif category in ["locker", "academy", "lab"]:
        # Monster categories
        for user_monster in user_data["monsters"]:
            monster_data = get_monster_with_progress(
                user_monster["name"],
                user_monster["id"],
                user_data["monsters"],
                game_data
            )
            if monster_data and monster_data["category"] == category:
                if not monster_data["unlocked"]:
                    total_putty += monster_data["unlock_cost_putty"]
                    # Unlock is instant, no time added
                else:
                    for i in range(monster_data["current_level"], monster_data["max_level"]):
                        if i < len(monster_data["all_upgrades"]):
                            upgrade = monster_data["all_upgrades"][i]
                            total_putty += upgrade["putty"]
                            total_seconds += parse_time_to_seconds(upgrade["time"])
    
    elif category == "champs":
        for user_champion in user_data["champions"]:
            champion_data = get_champion_with_progress(
                user_champion["name"],
                user_champion["id"],
                user_data["champions"],
                game_data
            )
            if champion_data:
                total_goo += champion_data["total_remaining_goo"]
                # Add feeding cooldown time multiplied by total feedings needed
                for upgrade in champion_data["remaining_upgrades"]:
                    cooldown_seconds = parse_time_to_seconds(champion_data["feeding_cooldown"])
                    total_seconds += cooldown_seconds * upgrade["feedings_needed"]
    
    total_time_display = format_time_from_seconds(total_seconds)
    
    html_content = f"""<div class="text-sm text-gray-600 mb-1">🪓 Twigs: {total_twigs:,}</div>
<div class="text-sm text-gray-600 mb-1">🥌 Pebbles: {total_pebbles:,}</div>
<div class="text-sm text-gray-600 mb-1">🧪 Putty: {total_putty:,}</div>
<div class="text-sm text-gray-600 mb-1">🟢 Goo: {total_gems:,}</div>
<div class="text-sm font-semibold mt-2">🕰 Total Time: {total_time_display}</div>"""
    
    return HTMLResponse(content=html_content)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
