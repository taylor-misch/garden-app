# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.


from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import Optional
from datetime import datetime
from database import Database

app = FastAPI(title="Garden Activity Logger", version="1.0.0")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Database instance
db = Database()

# Helper function to get current garden from session/query params
def get_current_garden_id(request: Request) -> int:
    """Get current garden ID from query params or default to first garden"""
    garden_id = request.query_params.get('garden_id')
    if garden_id:
        return int(garden_id)

    # Default to first garden
    gardens = db.get_gardens()
    if gardens:
        return gardens[0]['id']

    # If no gardens exist, create a default one
    return db.add_garden("My Garden", "Default garden", datetime.now().year)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page with garden selection and navigation"""
    gardens = db.get_gardens()
    current_garden_id = get_current_garden_id(request)
    current_garden = db.get_garden_by_id(current_garden_id)

    return templates.TemplateResponse("index.html", {
        "request": request,
        "gardens": gardens,
        "current_garden": current_garden
    })

# Garden CRUD endpoints
@app.get("/gardens", response_class=HTMLResponse)
async def gardens_page(request: Request):
    """Gardens management page"""
    gardens = db.get_gardens()
    return templates.TemplateResponse("gardens.html", {
        "request": request,
        "gardens": gardens
    })

@app.post("/gardens")
async def add_garden(request: Request, name: str = Form(...), description: str = Form(""), 
                     year: int = Form(...), location: str = Form("")):
    """Add a new garden"""
    db.add_garden(name, description, year, location)
    gardens = db.get_gardens()
    return templates.TemplateResponse("partials/gardens_list.html", {
        "request": request,
        "gardens": gardens
    })

@app.get("/gardens/{garden_id}/edit", response_class=HTMLResponse)
async def edit_garden_form(request: Request, garden_id: int):
    """Get edit form for garden"""
    garden = db.get_garden_by_id(garden_id)
    if not garden:
        raise HTTPException(status_code=404, detail="Garden not found")

    return templates.TemplateResponse("partials/garden_edit_form.html", {
        "request": request,
        "garden": garden
    })

@app.put("/gardens/{garden_id}")
async def update_garden(request: Request, garden_id: int, name: str = Form(...), 
                       description: str = Form(""), year: int = Form(...), location: str = Form("")):
    """Update a garden"""
    success = db.update_garden(garden_id, name, description, year, location)
    if not success:
        raise HTTPException(status_code=404, detail="Garden not found")

    gardens = db.get_gardens()
    return templates.TemplateResponse("partials/gardens_list.html", {
        "request": request,
        "gardens": gardens
    })

@app.delete("/gardens/{garden_id}")
async def delete_garden(request: Request, garden_id: int):
    """Delete a garden"""
    success = db.delete_garden(garden_id)
    if not success:
        raise HTTPException(status_code=404, detail="Garden not found")

    gardens = db.get_gardens()
    return templates.TemplateResponse("partials/gardens_list.html", {
        "request": request,
        "gardens": gardens
    })

# Plant Types CRUD endpoints
@app.get("/plant-types", response_class=HTMLResponse)
async def plant_types_page(request: Request):
    """Plant types management page"""
    current_garden_id = get_current_garden_id(request)
    current_garden = db.get_garden_by_id(current_garden_id)
    plant_types = db.get_plant_types(current_garden_id)
    gardens = db.get_gardens()

    return templates.TemplateResponse("plant_types.html", {
        "request": request,
        "plant_types": plant_types,
        "current_garden": current_garden,
        "gardens": gardens
    })

@app.post("/plant-types")
async def add_plant_type(request: Request, garden_id: int = Form(...), name: str = Form(...), description: str = Form("")):
    """Add a new plant type"""
    try:
        db.add_plant_type(garden_id, name, description)
        plant_types = db.get_plant_types(garden_id)
        current_garden = db.get_garden_by_id(garden_id)
        return templates.TemplateResponse("partials/plant_types_list.html", {
            "request": request,
            "plant_types": plant_types,
            "current_garden": current_garden
        })
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/plant-types/{plant_type_id}/edit", response_class=HTMLResponse)
async def edit_plant_type_form(request: Request, plant_type_id: int):
    """Get edit form for plant type"""
    plant_type = db.get_plant_type_by_id(plant_type_id)
    if not plant_type:
        raise HTTPException(status_code=404, detail="Plant type not found")

    return templates.TemplateResponse("partials/plant_type_edit_form.html", {
        "request": request,
        "plant_type": plant_type
    })

@app.put("/plant-types/{plant_type_id}")
async def update_plant_type(request: Request, plant_type_id: int, name: str = Form(...), description: str = Form("")):
    """Update a plant type"""
    plant_type = db.get_plant_type_by_id(plant_type_id)
    if not plant_type:
        raise HTTPException(status_code=404, detail="Plant type not found")

    success = db.update_plant_type(plant_type_id, name, description)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to update plant type")

    plant_types = db.get_plant_types(plant_type['garden_id'])
    current_garden = db.get_garden_by_id(plant_type['garden_id'])
    return templates.TemplateResponse("partials/plant_types_list.html", {
        "request": request,
        "plant_types": plant_types,
        "current_garden": current_garden
    })

@app.delete("/plant-types/{plant_type_id}")
async def delete_plant_type(request: Request, plant_type_id: int):
    """Delete a plant type"""
    plant_type = db.get_plant_type_by_id(plant_type_id)
    if not plant_type:
        raise HTTPException(status_code=404, detail="Plant type not found")

    success = db.delete_plant_type(plant_type_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to delete plant type")

    plant_types = db.get_plant_types(plant_type['garden_id'])
    current_garden = db.get_garden_by_id(plant_type['garden_id'])
    return templates.TemplateResponse("partials/plant_types_list.html", {
        "request": request,
        "plant_types": plant_types,
        "current_garden": current_garden
    })

# Harvest CRUD endpoints
@app.get("/harvests", response_class=HTMLResponse)
async def harvests_page(request: Request):
    """Harvests logging page"""
    current_garden_id = get_current_garden_id(request)
    current_garden = db.get_garden_by_id(current_garden_id)
    plant_types = db.get_plant_types(current_garden_id)
    harvests = db.get_harvests(current_garden_id)
    gardens = db.get_gardens()

    return templates.TemplateResponse("harvests.html", {
        "request": request,
        "plant_types": plant_types,
        "harvests": harvests,
        "current_garden": current_garden,
        "gardens": gardens
    })

@app.post("/harvests")
async def add_harvest(
    request: Request,
    plant_type_id: int = Form(...),
    quantity: float = Form(...),
    unit: str = Form(...),
    harvest_date: str = Form(...),
    notes: str = Form("")
):
    """Add a new harvest record"""
    # Get garden_id from plant_type
    plant_type = db.get_plant_type_by_id(plant_type_id)
    garden_id = plant_type['garden_id'] if plant_type else 1

    db.add_harvest(garden_id, plant_type_id, quantity, unit, harvest_date, notes)

    harvests = db.get_harvests(garden_id)
    return templates.TemplateResponse("partials/harvests_list.html", {
        "request": request,
        "harvests": harvests,
        "current_garden": db.get_garden_by_id(garden_id)
    })

@app.get("/harvests/{harvest_id}/edit", response_class=HTMLResponse)
async def edit_harvest_form(request: Request, harvest_id: int):
    """Get edit form for harvest"""
    harvest = db.get_harvest_by_id(harvest_id)
    if not harvest:
        raise HTTPException(status_code=404, detail="Harvest not found")

    plant_type = db.get_plant_type_by_id(harvest['plant_type_id'])
    plant_types = db.get_plant_types(plant_type['garden_id'])

    return templates.TemplateResponse("partials/harvest_edit_form.html", {
        "request": request,
        "harvest": harvest,
        "plant_types": plant_types
    })

@app.put("/harvests/{harvest_id}")
async def update_harvest(
    request: Request,
    harvest_id: int,
    plant_type_id: int = Form(...),
    quantity: float = Form(...),
    unit: str = Form(...),
    harvest_date: str = Form(...),
    notes: str = Form("")
):
    """Update a harvest record"""
    success = db.update_harvest(harvest_id, plant_type_id, quantity, unit, harvest_date, notes)
    if not success:
        raise HTTPException(status_code=404, detail="Harvest not found")

    plant_type = db.get_plant_type_by_id(plant_type_id)
    garden_id = plant_type['garden_id'] if plant_type else 1

    harvests = db.get_harvests(garden_id)
    return templates.TemplateResponse("partials/harvests_list.html", {
        "request": request,
        "harvests": harvests,
        "current_garden": db.get_garden_by_id(garden_id)
    })

@app.delete("/harvests/{harvest_id}")
async def delete_harvest(request: Request, harvest_id: int):
    """Delete a harvest record"""
    harvest = db.get_harvest_by_id(harvest_id)
    if not harvest:
        raise HTTPException(status_code=404, detail="Harvest not found")

    plant_type = db.get_plant_type_by_id(harvest['plant_type_id'])
    garden_id = plant_type['garden_id'] if plant_type else 1

    success = db.delete_harvest(harvest_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to delete harvest")

    harvests = db.get_harvests(garden_id)
    return templates.TemplateResponse("partials/harvests_list.html", {
        "request": request,
        "harvests": harvests,
        "current_garden": db.get_garden_by_id(garden_id)
    })

# Harvest summary endpoint
@app.get("/harvest-summary", response_class=HTMLResponse)
async def harvest_summary_page(request: Request):
    """Harvest summary page"""
    current_garden_id = get_current_garden_id(request)
    current_garden = db.get_garden_by_id(current_garden_id)
    summary = db.get_harvest_summary(current_garden_id)
    gardens = db.get_gardens()

    return templates.TemplateResponse("harvest_summary.html", {
        "request": request,
        "summary": summary,
        "current_garden": current_garden,
        "gardens": gardens
    })

# Garden activities CRUD endpoints
@app.get("/activities", response_class=HTMLResponse)
async def activities_page(request: Request):
    """Garden activities (watering/fertilizing) page"""
    current_garden_id = get_current_garden_id(request)
    current_garden = db.get_garden_by_id(current_garden_id)
    activities = db.get_garden_activities(current_garden_id)
    gardens = db.get_gardens()

    return templates.TemplateResponse("activities.html", {
        "request": request,
        "activities": activities,
        "current_garden": current_garden,
        "gardens": gardens
    })

@app.post("/activities")
async def add_activity(
    request: Request,
    garden_id: int = Form(...),
    activity_type: str = Form(...),
    activity_date: str = Form(...),
    notes: str = Form("")
):
    """Add a new garden activity"""
    db.add_garden_activity(garden_id, activity_type, activity_date, notes)
    activities = db.get_garden_activities(garden_id)
    current_garden = db.get_garden_by_id(garden_id)
    return templates.TemplateResponse("partials/activities_list.html", {
        "request": request,
        "activities": activities,
        "current_garden": current_garden
    })

@app.get("/activities/{activity_id}/edit", response_class=HTMLResponse)
async def edit_activity_form(request: Request, activity_id: int):
    """Get edit form for activity"""
    activity = db.get_garden_activity_by_id(activity_id)
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    return templates.TemplateResponse("partials/activity_edit_form.html", {
        "request": request,
        "activity": activity
    })

@app.put("/activities/{activity_id}")
async def update_activity(
    request: Request,
    activity_id: int,
    activity_type: str = Form(...),
    activity_date: str = Form(...),
    notes: str = Form("")
):
    """Update a garden activity"""
    activity = db.get_garden_activity_by_id(activity_id)
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    success = db.update_garden_activity(activity_id, activity_type, activity_date, notes)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to update activity")

    activities = db.get_garden_activities(activity['garden_id'])
    current_garden = db.get_garden_by_id(activity['garden_id'])
    return templates.TemplateResponse("partials/activities_list.html", {
        "request": request,
        "activities": activities,
        "current_garden": current_garden
    })

@app.delete("/activities/{activity_id}")
async def delete_activity(request: Request, activity_id: int):
    """Delete a garden activity"""
    activity = db.get_garden_activity_by_id(activity_id)
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    success = db.delete_garden_activity(activity_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to delete activity")

    activities = db.get_garden_activities(activity['garden_id'])
    current_garden = db.get_garden_by_id(activity['garden_id'])
    return templates.TemplateResponse("partials/activities_list.html", {
        "request": request,
        "activities": activities,
        "current_garden": current_garden
    })

# Individual plants CRUD endpoints
@app.get("/plants", response_class=HTMLResponse)
async def plants_page(request: Request):
    """Individual plants management page"""
    current_garden_id = get_current_garden_id(request)
    current_garden = db.get_garden_by_id(current_garden_id)
    plants = db.get_plants(current_garden_id)
    plant_types = db.get_plant_types(current_garden_id)
    gardens = db.get_gardens()

    return templates.TemplateResponse("plants.html", {
        "request": request,
        "plants": plants,
        "plant_types": plant_types,
        "current_garden": current_garden,
        "gardens": gardens
    })

@app.post("/plants")
async def add_plant(
    request: Request,
    plant_type_id: int = Form(...),
    name: str = Form(...),
    planted_date: str = Form(""),
    location: str = Form("")
):
    """Add a new individual plant"""
    plant_type = db.get_plant_type_by_id(plant_type_id)
    garden_id = plant_type['garden_id'] if plant_type else 1

    db.add_plant(garden_id, plant_type_id, name, planted_date, location)

    plants = db.get_plants(garden_id)
    current_garden = db.get_garden_by_id(garden_id)
    return templates.TemplateResponse("partials/plants_list.html", {
        "request": request,
        "plants": plants,
        "current_garden": current_garden
    })

@app.get("/plants/{plant_id}/edit", response_class=HTMLResponse)
async def edit_plant_form(request: Request, plant_id: int):
    """Get edit form for plant"""
    plant = db.get_plant_by_id(plant_id)
    if not plant:
        raise HTTPException(status_code=404, detail="Plant not found")

    plant_type = db.get_plant_type_by_id(plant['plant_type_id'])
    plant_types = db.get_plant_types(plant_type['garden_id'])

    return templates.TemplateResponse("partials/plant_edit_form.html", {
        "request": request,
        "plant": plant,
        "plant_types": plant_types
    })

@app.put("/plants/{plant_id}")
async def update_plant(
    request: Request,
    plant_id: int,
    plant_type_id: int = Form(...),
    name: str = Form(...),
    planted_date: str = Form(""),
    location: str = Form(""),
    status: str = Form("active")
):
    """Update a plant"""
    success = db.update_plant(plant_id, plant_type_id, name, planted_date, location, status)
    if not success:
        raise HTTPException(status_code=404, detail="Plant not found")

    plant_type = db.get_plant_type_by_id(plant_type_id)
    garden_id = plant_type['garden_id'] if plant_type else 1

    plants = db.get_plants(garden_id)
    current_garden = db.get_garden_by_id(garden_id)
    return templates.TemplateResponse("partials/plants_list.html", {
        "request": request,
        "plants": plants,
        "current_garden": current_garden
    })

@app.delete("/plants/{plant_id}")
async def delete_plant(request: Request, plant_id: int):
    """Delete a plant"""
    plant = db.get_plant_by_id(plant_id)
    if not plant:
        raise HTTPException(status_code=404, detail="Plant not found")

    plant_type = db.get_plant_type_by_id(plant['plant_type_id'])
    garden_id = plant_type['garden_id'] if plant_type else 1

    success = db.delete_plant(plant_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to delete plant")

    plants = db.get_plants(garden_id)
    current_garden = db.get_garden_by_id(garden_id)
    return templates.TemplateResponse("partials/plants_list.html", {
        "request": request,
        "plants": plants,
        "current_garden": current_garden
    })

# Plant journal CRUD endpoints
@app.get("/plants/{plant_id}/journal", response_class=HTMLResponse)
async def plant_journal_page(request: Request, plant_id: int):
    """Plant journal page for specific plant"""
    plant = db.get_plant_by_id(plant_id)
    if not plant:
        raise HTTPException(status_code=404, detail="Plant not found")

    journal_entries = db.get_plant_journal_entries(plant_id)
    return templates.TemplateResponse("plant_journal.html", {
        "request": request,
        "plant": plant,
        "journal_entries": journal_entries
    })

@app.post("/plants/{plant_id}/journal")
async def add_journal_entry(
    request: Request,
    plant_id: int,
    entry_date: str = Form(...),
    notes: str = Form(...)
):
    """Add a journal entry for a specific plant"""
    plant = db.get_plant_by_id(plant_id)
    plant_type = db.get_plant_type_by_id(plant['plant_type_id'])
    garden_id = plant_type['garden_id'] if plant_type else 1

    db.add_journal_entry(garden_id, plant_id, entry_date, notes)
    journal_entries = db.get_plant_journal_entries(plant_id)
    return templates.TemplateResponse("partials/journal_entries_list.html", {
        "request": request,
        "journal_entries": journal_entries,
        "plant_id": plant_id
    })

@app.get("/journal/{journal_id}/edit", response_class=HTMLResponse)
async def edit_journal_form(request: Request, journal_id: int):
    """Get edit form for journal entry"""
    journal = db.get_journal_entry_by_id(journal_id)
    if not journal:
        raise HTTPException(status_code=404, detail="Journal entry not found")

    return templates.TemplateResponse("partials/journal_edit_form.html", {
        "request": request,
        "journal": journal
    })

@app.put("/journal/{journal_id}")
async def update_journal_entry(
    request: Request,
    journal_id: int,
    entry_date: str = Form(...),
    notes: str = Form(...)
):
    """Update a journal entry"""
    journal = db.get_journal_entry_by_id(journal_id)
    if not journal:
        raise HTTPException(status_code=404, detail="Journal entry not found")

    success = db.update_journal_entry(journal_id, entry_date, notes)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to update journal entry")

    journal_entries = db.get_plant_journal_entries(journal['plant_id'])
    return templates.TemplateResponse("partials/journal_entries_list.html", {
        "request": request,
        "journal_entries": journal_entries,
        "plant_id": journal['plant_id']
    })

@app.delete("/journal/{journal_id}")
async def delete_journal_entry(request: Request, journal_id: int):
    """Delete a journal entry"""
    journal = db.get_journal_entry_by_id(journal_id)
    if not journal:
        raise HTTPException(status_code=404, detail="Journal entry not found")

    success = db.delete_journal_entry(journal_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to delete journal entry")

    journal_entries = db.get_plant_journal_entries(journal['plant_id'])
    return templates.TemplateResponse("partials/journal_entries_list.html", {
        "request": request,
        "journal_entries": journal_entries,
        "plant_id": journal['plant_id']
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
