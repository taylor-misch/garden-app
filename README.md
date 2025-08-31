# Garden Activity Logger 🌱

A comprehensive web application for tracking garden activities throughout the growing season. Built with FastAPI, HTMX, and SQLite.

## Features

### 🌿 Plant Type Management
- Add and manage different types of plants you're growing
- Include descriptions for each plant type

### 🥕 Harvest Logging
- Record daily harvest quantities with dates
- Support for multiple units (pounds, ounces, kilograms, pieces, etc.)
- Add notes for each harvest entry

### 📊 Production Summary
- View total production quantities for each plant type
- Get an overview of your garden's productivity

### 💧 Garden Activity Tracking
- Log watering and fertilizing activities
- Track dates and add notes for each activity

### 🪴 Individual Plant Management
- Track individual plants with unique names/IDs
- Record planting dates and locations
- Maintain growing journals for each plant

### 📖 Plant Journals
- Add detailed journal entries for individual plants
- Record observations, care activities, and progress notes
- View chronological history of each plant

## Technology Stack

- **Backend**: FastAPI (Python 3.13)
- **Frontend**: HTMX with Jinja2 templates
- **Database**: SQLite
- **Styling**: Custom CSS with responsive design

## Installation

1. **Create and activate virtual environment**:
   ```bash
   python -m venv .venv
   # On Windows:
   .venv\Scripts\activate
   # On macOS/Linux:
   source .venv/bin/activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**:
   ```bash
   python main.py
   ```

4. **Access the application**:
   Open your browser and navigate to `http://localhost:8000`

## Usage Guide

### Getting Started

1. **Add Plant Types**: Start by adding the types of plants you're growing (tomatoes, lettuce, carrots, etc.)

2. **Track Activities**: Log your daily garden activities like watering and fertilizing

3. **Record Harvests**: Log your harvest quantities with dates and units

4. **Manage Individual Plants**: Add specific plants with names/IDs for detailed tracking

5. **Maintain Journals**: Keep detailed growing journals for individual plants

### Navigation

- **Home**: Overview and quick access to all features
- **Plant Types**: Manage plant varieties
- **Log Harvest**: Record harvest quantities
- **Harvest Summary**: View total production
- **Garden Activities**: Track watering and fertilizing
- **My Plants**: Manage individual plants and journals

## Database Schema

The application uses SQLite with the following tables:

- `plant_types`: Store plant varieties
- `harvests`: Record harvest quantities and dates
- `garden_activities`: Track watering and fertilizing
- `plants`: Individual plant tracking
- `plant_journals`: Detailed journal entries for plants

## Features in Detail

### Plant Types
- Add unlimited plant varieties
- Include optional descriptions
- Used as dropdown options throughout the app

### Harvest Logging
- Multiple unit support (weight, count, bunches)
- Date tracking for seasonal analysis
- Optional notes for each harvest

### Production Summary
- Aggregate totals by plant type and unit
- Visual cards showing total production
- Quick overview of garden productivity

### Garden Activities
- Separate tracking for watering and fertilizing
- Date-based logging
- Optional notes for each activity

### Individual Plants
- Unique identification for each plant
- Planting date and location tracking
- Status monitoring (active, harvested, etc.)

### Plant Journals
- Detailed entries with dates
- Observation and care notes
- Historical timeline for each plant

## Development

### Project Structure
