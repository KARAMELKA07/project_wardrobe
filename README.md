# Project Wardrobe MVP

MVP monorepo for a diploma project:

`Development of a web service for outfit and wardrobe selection using intelligent methods`

The project does **not** use LLMs. Outfit generation is based on a transparent recommendation engine that scores combinations using 10 features.

## Stack

- Backend: Python, Flask, Flask-SQLAlchemy, Flask-Migrate, Flask-JWT-Extended
- Database: MySQL
- Frontend: React, JavaScript, Vite
- Image storage: local `uploads/`
- AI-assisted item digitization: `rembg` + local DeepFashion classifier + fallback zero-shot classifier + color extraction

## Repository structure

```text
project-root/
  backend/
    app/
      api/
      config/
      extensions/
      models/
      schemas/
      services/
      utils/
    migrations/
    requirements.txt
    run.py
  frontend/
    src/
      api/
      components/
      context/
      hooks/
      pages/
      styles/
    index.html
    package.json
    vite.config.js
  uploads/
  .env.example
  README.md
```

## Backend setup

### 1. Create a virtual environment and install dependencies

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Create the MySQL database

Example SQL:

```sql
CREATE DATABASE wardrobe_mvp
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;
```

### 3. Configure environment variables

Copy the root example file:

```powershell
cd ..
Copy-Item .env.example .env
```

Update the values in `.env`:

- `SECRET_KEY`
- `JWT_SECRET_KEY`
- `MYSQL_HOST`
- `MYSQL_PORT`
- `MYSQL_USER`
- `MYSQL_PASSWORD`
- `MYSQL_DB`
- `FRONTEND_URL`
- `VITE_API_URL`
- `FASHION_AI_ENABLED`
- `FASHION_AI_MODEL_ID`
- `DEEPFASHION_DATASET_DIR`
- `DEEPFASHION_CHECKPOINT_PATH`
- `DEEPFASHION_METADATA_PATH`
- `DEEPFASHION_CONFIDENCE_THRESHOLD`

Note: the frontend is configured with `envDir: ".."`, so the root `.env` is used by both backend and frontend.

### 4. Initialize and run migrations

From the `backend/` directory:

```powershell
$env:FLASK_APP = "run.py"
flask db init
flask db migrate -m "Initial schema"
flask db upgrade
```

After the first initialization, use only:

```powershell
flask db migrate -m "Describe your schema change"
flask db upgrade
```

### 5. Run the Flask backend

```powershell
python run.py
```

Backend default URL: [http://localhost:5000](http://localhost:5000)

Health check: [http://localhost:5000/health](http://localhost:5000/health)

Note: if a trained local DeepFashion checkpoint is not connected yet, on the first call to image analysis the fallback zero-shot model may be downloaded automatically from Hugging Face. This can take additional time depending on internet speed.

## Frontend setup

### 1. Install dependencies

```powershell
cd frontend
npm install
```

### 2. Run the Vite dev server

```powershell
npm run dev
```

Frontend default URL: [http://localhost:5173](http://localhost:5173)

## Implemented MVP features

- JWT auth: register, login, current user
- Digital wardrobe CRUD with local image upload
- Automatic background removal for uploaded clothing images
- AI-assisted recognition of clothing type with auto-fill suggestions
- Outfit generation from user items
- 10-feature recommendation architecture with weighted scoring
- Explainability without LLMs
- Mock weather service
- Basic wardrobe analytics
- React dashboard, wardrobe pages, outfit generator, saved outfits, analytics

## Recommendation engine

The backend service `backend/app/services/recommendation_engine.py` contains 10 independent scoring functions:

1. `ColorHarmony`
2. `StyleMatch`
3. `EventMatch`
4. `SeasonMatch`
5. `TemperatureMatch`
6. `WeatherConditionMatch`
7. `Completeness`
8. `LayeringCorrectness`
9. `UserPreferenceMatch`
10. `ConstraintsMatch`

Each feature returns a value from `0` to `1`. The final outfit score is a weighted sum of these feature values.

## Main API routes

- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/me`
- `POST /api/items`
- `GET /api/items`
- `GET /api/items/<id>`
- `PUT /api/items/<id>`
- `DELETE /api/items/<id>`
- `POST /api/items/upload`
- `POST /api/items/analyze-image`
- `POST /api/outfits/generate`
- `POST /api/outfits`
- `GET /api/outfits`
- `POST /api/outfits/<id>/feedback`
- `GET /api/analytics/summary`

## Notes for further development

- `MockWeatherService` can be replaced with a real weather API later.
- The current image recognition module first tries to use a local DeepFashion-based checkpoint and then falls back to a zero-shot model if needed.
- User preference editing can be added as a separate profile/settings module.
- The scoring rules and weights are intentionally simple and readable for an MVP and diploma extension work.

## DeepFashion-based item analysis

When a user selects a clothing image in the add/edit form, the frontend sends the file to `POST /api/items/analyze-image`.

The backend then:

1. removes the background with `rembg`;
2. tries to classify the item with a local DeepFashion-based model;
3. if the local model is unavailable or gives low confidence, uses a zero-shot fallback classifier;
4. extracts dominant colors from the processed image;
5. returns suggestions for:
   - `category`
   - `subcategory`
   - `colors`
   - `styles`
   - `season`
   - `formality`
   - `fit`
   - `layer_level`
   - `insulation_rating`
   - `waterproof`
   - `windproof`

The user can review the suggested values before saving the item. If the "remove background on save" option is enabled, the saved image in `uploads/` will be the processed image with removed background.

## Training a local DeepFashion classifier

The project already contains a training pipeline for **DeepFashion Category and Attribute Prediction Benchmark**.

Expected dataset directory:

`backend/Category and Attribute Prediction Benchmark`

Required contents:

- `Anno_coarse/`
- `Eval/`
- `img/` or `Img/img/`

Important: annotation files alone are not enough. You must also unpack `Clothes Images`.

Run training from `backend/`:

```powershell
.\.venv\Scripts\python.exe scripts\train_deepfashion_classifier.py
```

After training, the project will create:

- `backend/model_artifacts/deepfashion_classifier.pt`
- `backend/model_artifacts/deepfashion_classifier.metadata.json`

Then restart the backend:

```powershell
.\.venv\Scripts\python.exe run.py
```

From this point, image analysis will use the local DeepFashion classifier first and only then fall back to the zero-shot model if needed.
