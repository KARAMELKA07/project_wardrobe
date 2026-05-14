# Публикация проекта на GitHub и переобучение модели на более мощном компьютере

## Почему распознавание сейчас может работать слабо

Для текущего качества распознавания есть несколько вероятных причин.

1. Слабый ноутбук влияет в первую очередь на **скорость и глубину обучения**, а не на итоговую логику модели. Если обучение пришлось останавливать раньше, уменьшать число эпох или использовать более мягкие настройки, качество классификации закономерно падает.

2. Текущий классификатор обучается на `DeepFashion Category and Attribute Prediction Benchmark`. Этот набор данных хорошо подходит для верхов, низов и части верхней одежды, но **не покрывает обувь и аксессуары в том виде, в котором они нужны проекту**. Поэтому плохое распознавание обуви связано не только с мощностью компьютера, но и с составом данных.

3. В проекте цвета определяются отдельным алгоритмом, а не нейросетью. Если тип вещи определяется неверно, автозаполнение характеристик по словарю тоже будет выглядеть слабее, потому что словарь опирается на уже распознанную подкатегорию.

## Что реально улучшит качество

### Для одежды

Переобучение на более мощной машине с:

- более долгим обучением;
- более крупным `batch size`;
- большим числом `workers`;
- качественно распакованным датасетом;
- при необходимости более глубокой архитектурой,

должно заметно улучшить распознавание верхов, низов и верхней одежды.

### Для обуви и аксессуаров

Одного переобучения на текущем `DeepFashion Category and Attribute Prediction Benchmark` недостаточно. Даже если использовать более мощный компьютер и более качественные изображения, обувь всё равно будет распознаваться нестабильно, потому что проблема не только в качестве обучения, но и в **неподходящем покрытии классов**.

Практически разумный путь такой:

1. оставить текущий DeepFashion-классификатор для одежды;
2. сохранить резервный `zero-shot` fallback для сложных или неподдерживаемых случаев;
3. позже, если понадобится, добавить **второй отдельный классификатор для обуви и аксессуаров** на подходящем датасете.

## Что уже подготовлено в проекте

В репозитории уже подготовлены:

- `.gitignore`, исключающий большой датасет, кеш моделей и обученные веса;
- пайплайн обучения локального классификатора:
  - [train_deepfashion_classifier.py](C:/Users/zakir/github%20projects/project_wardrobe/backend/scripts/train_deepfashion_classifier.py)
- загрузчик и маппинг DeepFashion:
  - [deepfashion_dataset.py](C:/Users/zakir/github%20projects/project_wardrobe/backend/app/services/deepfashion_dataset.py)
- локальный runtime-классификатор:
  - [deepfashion_classifier.py](C:/Users/zakir/github%20projects/project_wardrobe/backend/app/services/deepfashion_classifier.py)
- fallback-механизм в рабочем анализе изображения:
  - [fashion_image_service.py](C:/Users/zakir/github%20projects/project_wardrobe/backend/app/services/fashion_image_service.py)

Это значит, что после клонирования на более мощный компьютер тебе не нужно заново строить архитектуру. Понадобится только скачать датасет, обучить модель и подставить новые артефакты.

## Как подготовить репозиторий к GitHub

### 1. Проверить, что тяжелые файлы больше не должны попадать в репозиторий

Теперь в `.gitignore` исключены:

- `backend/Category and Attribute Prediction Benchmark/`
- `backend/.torch-cache/`
- `backend/training_logs/`
- `backend/model_artifacts/*` кроме `.gitkeep`
- `.vs/`
- `backend/.vs/`

### 2. Если тяжелые файлы уже были добавлены в git

В таком случае одного `.gitignore` недостаточно. Нужно убрать их **из индекса git**, но оставить на диске.

Из корня проекта выполни:

```powershell
git -c safe.directory="C:/Users/zakir/github projects/project_wardrobe" rm -r --cached --ignore-unmatch ".vs" "backend/.vs" "backend/.torch-cache" "backend/training_logs" "backend/Category and Attribute Prediction Benchmark" "backend/model_artifacts/deepfashion_classifier.pt" "backend/model_artifacts/deepfashion_classifier.metadata.json"
```

Потом проверь статус:

```powershell
git -c safe.directory="C:/Users/zakir/github projects/project_wardrobe" status
```

После этого можно коммитить проект уже без тяжелых локальных данных.

### 3. Если git ругается на dubious ownership

На этой машине у репозитория уже была такая проблема. Если увидишь похожую ошибку, добавь репозиторий в safe directory:

```powershell
git config --global --add safe.directory "C:/Users/zakir/github projects/project_wardrobe"
```

## Как перенести проект на более мощный компьютер

### 1. Запушить код на GitHub

После очистки индекса:

```powershell
git add .
git commit -m "Prepare project for GitHub and DeepFashion retraining"
git branch -M main
git remote add origin <URL_ТВОЕГО_РЕПОЗИТОРИЯ>
git push -u origin main
```

### 2. Клонировать проект на новом компьютере

```powershell
git clone <URL_ТВОЕГО_РЕПОЗИТОРИЯ>
cd project_wardrobe
```

## Что делать на более мощной машине

### 1. Установить зависимости backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Скачать датасет DeepFashion заново

Положи его по пути:

`backend/Category and Attribute Prediction Benchmark`

Для текущего загрузчика проекта ожидается одна из таких структур:

- `backend/Category and Attribute Prediction Benchmark/img`
- `backend/Category and Attribute Prediction Benchmark/Img/img`
- `backend/Category and Attribute Prediction Benchmark/Img/img/img`

### 3. Переобучить модель

Базовая команда:

```powershell
cd backend
.\.venv\Scripts\python.exe -u scripts\train_deepfashion_classifier.py
```

Рекомендуемая команда для более мощной машины:

```powershell
cd backend
.\.venv\Scripts\python.exe -u scripts\train_deepfashion_classifier.py --architecture efficientnet_b0 --epochs 10 --batch-size 64 --learning-rate 0.0003 --num-workers 8
```

Если памяти и видеопамяти достаточно, можно попробовать `resnet50`:

```powershell
cd backend
.\.venv\Scripts\python.exe -u scripts\train_deepfashion_classifier.py --architecture resnet50 --epochs 10 --batch-size 32 --learning-rate 0.0003 --num-workers 8
```

### 4. Проверить, что модель сохранилась

После обучения должны появиться:

- `backend/model_artifacts/deepfashion_classifier.pt`
- `backend/model_artifacts/deepfashion_classifier.metadata.json`

## Как улучшить результат уже сейчас без переписывания проекта

### 1. Сделать систему осторожнее на сложных фото

Если локальная модель слишком часто уверенно ошибается, можно поднять порог доверия:

```env
DEEPFASHION_CONFIDENCE_THRESHOLD=0.70
```

Тогда в неоднозначных случаях система чаще будет использовать резервный классификатор, а не ошибочный локальный прогноз.

### 2. Проверять модель отдельно по типам вещей

Тестируй минимум на четырёх группах:

- верх;
- низ;
- верхняя одежда;
- обувь.

Так сразу будет видно, что именно улучшилось после переобучения, а что по-прежнему требует отдельного датасета.

### 3. Не ждать, что DeepFashion решит обувь автоматически

Если обувь нужна как полноценная часть проекта, закладывай второй этап развития:

- либо отдельный датасет по обуви;
- либо отдельный классификатор для обуви и аксессуаров;
- либо сохранение `zero-shot` fallback именно для этих групп.

## Как проверить проект после переобучения

1. Запустить backend:

```powershell
cd backend
$env:FLASK_APP = "run.py"
.\.venv\Scripts\python.exe run.py
```

2. Запустить frontend:

```powershell
cd frontend
npm install
npm run dev
```

3. Перейти на страницу добавления вещи:

`http://localhost:5173/wardrobe/add`

4. Загрузить фото вещи и открыть `Network` в браузере.

5. Проверить ответ `POST /api/items/analyze-image`.

Если используется локальная модель, в ответе будет:

```json
"model": "deepfashion-local:efficientnet_b0"
```

или

```json
"model": "deepfashion-local:resnet50"
```

Если сработал резервный вариант, ты увидишь модель fallback-классификатора и предупреждения.

## Рекомендуемый план действий

1. Очистить репозиторий от тяжелых локальных файлов и запушить код на GitHub.
2. Клонировать проект на более мощный компьютер.
3. Снова скачать DeepFashion.
4. Переобучить модель с более сильными настройками.
5. Проверить качество на верхах, низах и верхней одежде.
6. Для обуви пока оставить fallback и отдельно решить, нужен ли второй датасет.

Это самый практичный путь. Он не ломает текущую архитектуру проекта и позволяет улучшать качество распознавания поэтапно.
