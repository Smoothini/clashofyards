from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List, Dict, Optional
import uvicorn

app = FastAPI(title="Backyard Monsters Upgrade Tracker")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Data Models
class Building(BaseModel):
    id: str
    name: str
    category: str  # resources, buildings, defensive
    current_level: int
    max_level: int
    upgrade_cost_twigs: int
    upgrade_cost_pebbles: int
    upgrade_time: str
    image_url: str

class Monster(BaseModel):
    id: str
    name: str
    category: str  # locker, lab, academy
    unlocked: bool
    unlock_cost_goo: int
    current_level: int
    max_level: int
    upgrade_cost_goo: int
    upgrade_time: str
    image_url: str

class Champion(BaseModel):
    id: str
    name: str
    current_level: int
    max_level: int
    feeding_cost: int
    feeding_time: str
    image_url: str

class UserProfile(BaseModel):
    username: str
    town_hall_level: int
    th_upgrade_cost_twigs: int
    th_upgrade_cost_pebbles: int
    th_upgrade_time: str

# Sample Data
user_profile = UserProfile(
    username="MonsterMaster123",
    town_hall_level=8,
    th_upgrade_cost_twigs=50000,
    th_upgrade_cost_pebbles=25000,
    th_upgrade_time="3d 12h"
)

buildings_data = [
    # Defensive Buildings
    Building(
        id="cannon_tower_1",
        name="Cannon Tower",
        category="defensive",
        current_level=5,
        max_level=8,
        upgrade_cost_twigs=15000,
        upgrade_cost_pebbles=8000,
        upgrade_time="2h 30m",
        image_url="/static/images/cannon_tower.png"
    ),
    Building(
        id="cannon_tower_2",
        name="Cannon Tower",
        category="defensive",
        current_level=3,
        max_level=8,
        upgrade_cost_twigs=15000,
        upgrade_cost_pebbles=8000,
        upgrade_time="2h 30m",
        image_url="/static/images/cannon_tower.png"
    ),
    Building(
        id="sniper_tower_1",
        name="Sniper Tower",
        category="defensive",
        current_level=3,
        max_level=8,
        upgrade_cost_twigs=12000,
        upgrade_cost_pebbles=6000,
        upgrade_time="1h 45m",
        image_url="/static/images/sniper_tower.png"
    ),
    Building(
        id="sniper_tower_2",
        name="Sniper Tower",
        category="defensive",
        current_level=6,
        max_level=8,
        upgrade_cost_twigs=12000,
        upgrade_cost_pebbles=6000,
        upgrade_time="1h 45m",
        image_url="/static/images/sniper_tower.png"
    ),
    
    # Resource Buildings
    Building(
        id="twig_harvester_1",
        name="Twig Harvester",
        category="resources",
        current_level=6,
        max_level=8,
        upgrade_cost_twigs=8000,
        upgrade_cost_pebbles=4000,
        upgrade_time="1h 15m",
        image_url="/static/images/twig_harvester.png"
    ),
    Building(
        id="twig_harvester_2",
        name="Twig Harvester",
        category="resources",
        current_level=4,
        max_level=8,
        upgrade_cost_twigs=8000,
        upgrade_cost_pebbles=4000,
        upgrade_time="1h 15m",
        image_url="/static/images/twig_harvester.png"
    ),
    Building(
        id="pebble_mine_1",
        name="Pebble Mine",
        category="resources",
        current_level=4,
        max_level=8,
        upgrade_cost_twigs=10000,
        upgrade_cost_pebbles=5000,
        upgrade_time="2h",
        image_url="/static/images/pebble_mine.png"
    ),
    
    # Other Buildings
    Building(
        id="housing_1",
        name="Monster Housing",
        category="buildings",
        current_level=7,
        max_level=8,
        upgrade_cost_twigs=20000,
        upgrade_cost_pebbles=10000,
        upgrade_time="4h",
        image_url="/static/images/housing.png"
    ),
    Building(
        id="housing_2",
        name="Monster Housing",
        category="buildings",
        current_level=5,
        max_level=8,
        upgrade_cost_twigs=20000,
        upgrade_cost_pebbles=10000,
        upgrade_time="4h",
        image_url="/static/images/housing.png"
    )
]

monsters_data = [
    # Monster Locker
    Monster(
        id="pokey",
        name="Pokey",
        category="locker",
        unlocked=True,
        unlock_cost_goo=0,
        current_level=3,
        max_level=5,
        upgrade_cost_goo=5000,
        upgrade_time="30m",
        image_url="/static/images/pokey.png"
    ),
    Monster(
        id="bolt",
        name="Bolt",
        category="locker",
        unlocked=False,
        unlock_cost_goo=15000,
        current_level=0,
        max_level=5,
        upgrade_cost_goo=8000,
        upgrade_time="45m",
        image_url="/static/images/bolt.png"
    ),
    Monster(
        id="brain",
        name="Brain",
        category="locker",
        unlocked=False,
        unlock_cost_goo=25000,
        current_level=0,
        max_level=6,
        upgrade_cost_goo=12000,
        upgrade_time="1h 15m",
        image_url="/static/images/brain.png"
    ),
    
    # Academy
    Monster(
        id="fink",
        name="Fink",
        category="academy",
        unlocked=True,
        unlock_cost_goo=0,
        current_level=2,
        max_level=4,
        upgrade_cost_goo=3000,
        upgrade_time="20m",
        image_url="/static/images/fink.png"
    ),
    Monster(
        id="eye_ra",
        name="Eye-Ra",
        category="academy",
        unlocked=True,
        unlock_cost_goo=5000,
        current_level=1,
        max_level=4,
        upgrade_cost_goo=4000,
        upgrade_time="25m",
        image_url="/static/images/eye_ra.png"
    ),
    Monster(
        id="bandito",
        name="Bandito",
        category="academy",
        unlocked=False,
        unlock_cost_goo=18000,
        current_level=0,
        max_level=5,
        upgrade_cost_goo=6000,
        upgrade_time="35m",
        image_url="/static/images/bandito.png"
    ),
    
    # Monster Lab
    Monster(
        id="gorgo",
        name="Gorgo",
        category="lab",
        unlocked=True,
        unlock_cost_goo=10000,
        current_level=2,
        max_level=6,
        upgrade_cost_goo=15000,
        upgrade_time="2h",
        image_url="/static/images/gorgo.png"
    ),
    Monster(
        id="d_a_v_e",
        name="D.A.V.E",
        category="lab",
        unlocked=False,
        unlock_cost_goo=50000,
        current_level=0,
        max_level=8,
        upgrade_cost_goo=25000,
        upgrade_time="4h",
        image_url="/static/images/dave.png"
    ),
    Monster(
        id="zafreeti",
        name="Zafreeti",
        category="lab",
        unlocked=False,
        unlock_cost_goo=75000,
        current_level=0,
        max_level=10,
        upgrade_cost_goo=35000,
        upgrade_time="6h",
        image_url="/static/images/zafreeti.png"
    )
]

champions_data = [
    Champion(
        id="drull",
        name="Drull",
        current_level=15,
        max_level=25,
        feeding_cost=2500,
        feeding_time="6h",
        image_url="/static/images/drull.png"
    ),
    Champion(
        id="gorgo_champ",
        name="Gorgo Champion",
        current_level=12,
        max_level=25,
        feeding_cost=3000,
        feeding_time="8h",
        image_url="/static/images/gorgo_champ.png"
    ),
    Champion(
        id="king_wormzer",
        name="King Wormzer",
        current_level=8,
        max_level=20,
        feeding_cost=2000,
        feeding_time="4h",
        image_url="/static/images/king_wormzer.png"
    )
]

# Routes
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "user": user_profile
    })

@app.get("/api/buildings/{category}")
async def get_buildings(category: str, request: Request):
    filtered_buildings = [b for b in buildings_data if b.category == category]
    
    grouped_buildings = {}
    for building in filtered_buildings:
        if building.name not in grouped_buildings:
            grouped_buildings[building.name] = []
        grouped_buildings[building.name].append(building)
    
    return templates.TemplateResponse("buildings_content.html", {
        "request": request,
        "grouped_buildings": grouped_buildings,
        "category": category
    })

@app.get("/api/monsters/{category}")
async def get_monsters(category: str, request: Request):
    filtered_monsters = [m for m in monsters_data if m.category == category]
    return templates.TemplateResponse("monsters_content.html", {
        "request": request,
        "monsters": filtered_monsters,
        "category": category
    })

@app.get("/api/champions")
async def get_champions(request: Request):
    return templates.TemplateResponse("champions_content.html", {
        "request": request,
        "champions": champions_data
    })

@app.get("/api/stats")
async def get_stats(request: Request):
    total_buildings = len(buildings_data)
    total_monsters = len([m for m in monsters_data if m.unlocked])
    total_champions = len(champions_data)
    
    # Calculate total costs
    total_twigs = sum((b.max_level - b.current_level) * b.upgrade_cost_twigs for b in buildings_data)
    total_pebbles = sum((b.max_level - b.current_level) * b.upgrade_cost_pebbles for b in buildings_data)
    total_goo = sum((m.max_level - m.current_level) * m.upgrade_cost_goo for m in monsters_data if m.unlocked)
    total_goo += sum(m.unlock_cost_goo for m in monsters_data if not m.unlocked)
    
    # Calculate progress percentages
    building_progress = sum(b.current_level for b in buildings_data) / sum(b.max_level for b in buildings_data) * 100
    monster_progress = sum(m.current_level for m in monsters_data if m.unlocked) / sum(m.max_level for m in monsters_data if m.unlocked) * 100 if any(m.unlocked for m in monsters_data) else 0
    champion_progress = sum(c.current_level for c in champions_data) / sum(c.max_level for c in champions_data) * 100
    
    stats_data = {
        "total_buildings": total_buildings,
        "total_monsters": total_monsters,
        "total_champions": total_champions,
        "town_hall_level": user_profile.town_hall_level,
        "total_twigs": total_twigs,
        "total_pebbles": total_pebbles,
        "total_goo": total_goo,
        "building_progress": round(building_progress, 1),
        "monster_progress": round(monster_progress, 1),
        "champion_progress": round(champion_progress, 1),
        "unlocked_monsters": len([m for m in monsters_data if m.unlocked]),
        "locked_monsters": len([m for m in monsters_data if not m.unlocked])
    }
    
    return templates.TemplateResponse("stats_content.html", {
        "request": request,
        "stats": stats_data,
        "champions": champions_data
    })

@app.post("/api/upgrade/{item_type}/{item_id}")
async def upgrade_item(item_type: str, item_id: str, request: Request):
    if item_type == "building":
        # Find and upgrade the building
        for building in buildings_data:
            if building.id == item_id and building.current_level < building.max_level:
                building.current_level += 1
                return templates.TemplateResponse("upgrade_success.html", {
                    "request": request,
                    "item_name": building.name,
                    "new_level": building.current_level,
                    "item_type": "building"
                })
    
    elif item_type == "monster":
        for monster in monsters_data:
            if monster.id == item_id:
                if not monster.unlocked:
                    # Unlock the monster
                    monster.unlocked = True
                    return templates.TemplateResponse("upgrade_success.html", {
                        "request": request,
                        "item_name": monster.name,
                        "new_level": "UNLOCKED",
                        "item_type": "monster"
                    })
                elif monster.current_level < monster.max_level:
                    # Upgrade the monster
                    monster.current_level += 1
                    return templates.TemplateResponse("upgrade_success.html", {
                        "request": request,
                        "item_name": monster.name,
                        "new_level": monster.current_level,
                        "item_type": "monster"
                    })
    
    return templates.TemplateResponse("upgrade_error.html", {
        "request": request,
        "message": "Upgrade failed"
    })

@app.post("/api/feed/{champion_id}")
async def feed_champion(champion_id: str, request: Request):
    for champion in champions_data:
        if champion.id == champion_id and champion.current_level < champion.max_level:
            champion.current_level += 1
            return templates.TemplateResponse("upgrade_success.html", {
                "request": request,
                "item_name": champion.name,
                "new_level": champion.current_level,
                "item_type": "champion"
            })
    
    return templates.TemplateResponse("upgrade_error.html", {
        "request": request,
        "message": "Feeding failed"
    })

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

    ##1d232a put ts as bg rose
