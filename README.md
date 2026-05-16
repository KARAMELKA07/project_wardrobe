# Веб-сервис подбора образов и ведения гардероба

Проект представляет собой веб-сервис для ведения цифрового гардероба, автоматической оцифровки вещей по фотографии и подбора образов с учетом погоды, события и пользовательских предпочтений.

В сервисе реализованы:
- регистрация и авторизация пользователей;
- ведение цифрового гардероба;
- распознавание вещи по фото;
- удаление фона изображения;
- определение доминирующих цветов;
- автозаполнение характеристик вещи;
- подбор образов;
- сохранение образов;
- краткая аналитика гардероба;
- подгрузка текущей погоды с внешнего сервиса.

## Технологии

- Backend: `Python`, `Flask`, `SQLAlchemy`, `Flask-Migrate`, `JWT`
- Frontend: `React`, `Vite`
- База данных: `MySQL`
- Хранение изображений: локальная папка `uploads/`
- Модуль распознавания:
  - `DeepFashion` для одежды;
  - `FPID` для аксессуаров и проверки платьев;
  - `Zappos` для обуви;
  - `rembg` для удаления фона.

## Структура проекта

```text
project_wardrobe/
├─ backend/
│  ├─ app/
│  │  ├─ api/
│  │  ├─ config/
│  │  ├─ extensions/
│  │  ├─ models/
│  │  ├─ schemas/
│  │  ├─ services/
│  │  └─ utils/
│  ├─ migrations/
│  ├─ model_artifacts/
│  ├─ scripts/
│  ├─ tests/
│  ├─ requirements.txt
│  └─ run.py
├─ frontend/
│  ├─ public/
│  ├─ src/
│  ├─ package.json
│  └─ vite.config.js
├─ uploads/
├─ demo_assets/
│  └─ recognition_samples/
├─ .env.example
├─ .gitignore
└─ README.md
```

## Что важно для запуска после скачивания с GitHub

Чтобы проект можно было поднять сразу после скачивания репозитория:
- в репозитории должны лежать рабочие файлы моделей из папки `backend/model_artifacts/`;
- датасет для обучения `DeepFashion` в репозиторий не добавляется;
- пользовательские изображения, логи и runtime-данные в репозиторий не добавляются.

Рабочие модели, которые используются приложением:
- `backend/model_artifacts/deepfashion_classifier.pt`
- `backend/model_artifacts/deepfashion_classifier.metadata.json`
- `backend/model_artifacts/fpid_classifier.pt`
- `backend/model_artifacts/fpid_classifier.metadata.json`
- `backend/model_artifacts/zappos_classifier.pt`
- `backend/model_artifacts/zappos_classifier.metadata.json`

Если этих файлов нет, распознавание будет работать неполноценно или не будет работать так, как ожидается в демо.

## Подготовка окружения

### 1. Установить зависимости

Нужно иметь:
- `Python 3.11+`
- `Node.js 20+`
- `MySQL 8+`

### 2. Настроить `.env`

Скопируй файл:

```powershell
Copy-Item .env.example .env
```

Минимально проверь и при необходимости измени:

```env
SECRET_KEY=replace-with-a-random-secret
JWT_SECRET_KEY=replace-with-a-random-jwt-secret

FLASK_DEBUG=true
FLASK_RUN_HOST=0.0.0.0
FLASK_RUN_PORT=5000
FRONTEND_URL=http://localhost:5173

MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=1234
MYSQL_DB=wardrobe_mvp

UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=8388608

FASHION_AI_ENABLED=true
FASHION_AI_MODEL_ID=openai/clip-vit-base-patch32
DEEPFASHION_DATASET_DIR=backend/Category and Attribute Prediction Benchmark
DEEPFASHION_CHECKPOINT_PATH=backend/model_artifacts/deepfashion_classifier.pt
DEEPFASHION_METADATA_PATH=backend/model_artifacts/deepfashion_classifier.metadata.json
DEEPFASHION_CONFIDENCE_THRESHOLD=0.55

VITE_API_URL=http://localhost:5000/api
```

## Настройка базы данных

Создай базу данных в MySQL:

```sql
CREATE DATABASE wardrobe_mvp
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;
```

## Запуск backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

$env:FLASK_APP = "run.py"
python -m flask db upgrade
python run.py
```

Backend будет доступен по адресу:

- [http://localhost:5000](http://localhost:5000)
- health-check: [http://localhost:5000/health](http://localhost:5000/health)

## Запуск frontend

```powershell
cd frontend
npm install
npm run dev
```

Frontend будет доступен по адресу:

- [http://localhost:5173](http://localhost:5173)

## Что можно делать на сайте

После запуска сервиса можно:

1. Зарегистрироваться или войти в систему.
2. Добавлять вещи в гардероб.
3. Загружать фото вещи и получать:
   - распознавание типа вещи;
   - удаление фона;
   - определение цветов;
   - автозаполнение характеристик.
4. Просматривать карточки вещей.
5. Редактировать и удалять вещи.
6. Подбирать образы по событию, погоде, температуре и предпочтениям.
7. Сохранять понравившиеся образы.
8. Загружать фото пользователя в сохранённый образ.
9. Смотреть аналитику по гардеробу.

## Как проверить распознавание

Для проверки распознавания:

1. Открой страницу создания вещи.
2. Загрузи фотографию вещи.
3. Дождись результата анализа.
4. Проверь, что:
   - определился тип вещи;
   - определились цвета;
   - подставились характеристики;
   - в форме появились предложенные значения.

Для демонстрационных изображений можно использовать папку:

- `demo_assets/recognition_samples/`

Туда удобно положить:
- примеры одежды;
- примеры обуви;
- примеры аксессуаров;
- отдельные спорные кейсы для демонстрации качества распознавания.

## Демо-аккаунт

Этот блок можно заполнить позже, когда ты создашь тестовый аккаунт:

```text
Логин:
Пароль:
```

## Где хранятся данные

### Новые аккаунты

Новые аккаунты сохраняются в таблице `users` базы данных `MySQL`, указанной в `.env`.

Основные поля пользователя:
- `email`
- `password_hash`
- `name`
- `city`

### Наполнение аккаунта

Наполнение пользователя тоже хранится в `MySQL`:

- вещи — в таблице `clothing_items`
- сохранённые образы — в таблице `outfits`
- состав образов — в таблице `outfit_items`
- обратная связь по образам — в таблице `outfit_feedback`
- предпочтения пользователя — в таблице `user_preferences`

То есть логин и весь “содержательный” профиль пользователя лежат в базе данных.

### Изображения

Изображения вещей и пользовательские фото сохраняются в локальную папку:

- `uploads/`

Туда попадают:
- фото вещей;
- обработанные изображения без фона;
- фото пользователя в образе.

В базе данных при этом хранится путь к файлу, например в поле `image_url` у вещи или `styled_photo_url` у образа.

### Модели распознавания

Файлы обученных моделей лежат в:

- `backend/model_artifacts/`

### Логи распознавания

Логи результатов моделей сохраняются в:

- `backend/logs/fashion_model_predictions.jsonl`

## Что не хранится в GitHub

В репозиторий не должны попадать:
- датасет `DeepFashion`;
- кэш обучения;
- временные логи;
- локальные пользовательские изображения;
- виртуальные окружения;
- `node_modules`.

## Планы на развитие

В дальнейшем проект планируется подготовить к контейнеризации через `Docker`, чтобы запускать backend, frontend и базу данных в согласованной среде без ручной настройки на каждой машине.
