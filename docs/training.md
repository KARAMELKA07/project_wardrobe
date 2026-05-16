# Обучение локального классификатора

Данные, которые сейчас готовы к обучению:

- `data/raw/zappos/ut-zap50k-data` и `data/raw/zappos/ut-zap50k-images-square` готовы и дают обувные классы.
- `data/raw/ifashion/imat_fashion_comp-master` пока не готов к обучению: там есть карта меток, README и картинка атрибутов, но нет `train.json`, `val.json` и скачанных изображений.

## 1. Собрать манифест

```powershell
python backend\scripts\prepare_wardrobe_training_manifest.py
```

Скрипт создаст:

- `data/processed/wardrobe_training/manifest.csv`
- `data/processed/wardrobe_training/summary.json`

В `summary.json` будет видно, сколько объектов попало в `train` и `val`, какие классы получились, и почему iFashion пока не добавлен.

## 2. Запустить обучение

Быстрый старт для видеокарты или терпеливого CPU:

```powershell
python backend\scripts\train_wardrobe_manifest_classifier.py --epochs 8 --batch-size 16 --freeze-backbone --log-every 20
```

Если компьютер без интернета и веса EfficientNet еще не скачаны, запусти так:

```powershell
python backend\scripts\train_wardrobe_manifest_classifier.py --epochs 8 --batch-size 16 --freeze-backbone --no-pretrained --log-every 20
```

После обучения модель будет сохранена туда, где ее уже ждет приложение:

- `backend/model_artifacts/deepfashion_classifier.pt`
- `backend/model_artifacts/deepfashion_classifier.metadata.json`

## 3. Отслеживать прогресс

Второй PowerShell можно открыть параллельно и запустить:

```powershell
python backend\scripts\watch_training_progress.py
```

Одноразово посмотреть текущий статус:

```powershell
python backend\scripts\watch_training_progress.py --once
```

Сам лог лежит тут:

```text
backend/training_logs/wardrobe_training_metrics.jsonl
```

## 3.1. Проверить маршрутизацию FPID/Zappos

Из папки `backend`:

```powershell
python scripts\check_classifier_routing.py
```

Ожидаемая логика в выводе:

- обычная вещь: `"model": "fpid-local:efficientnet_b0"` и `"classification_route": "fpid"`
- обувь: `"model": "zappos-local:efficientnet_b0"` и `"classification_route": "fpid_to_zappos_shoes"`
- если FPID ошибся на аксессуаре, но объект похож на туфли: `"classification_route": "fpid_to_zappos_shape_fallback"`

Можно передать свои картинки:

```powershell
python scripts\check_classifier_routing.py C:\path\to\shirt.jpg C:\path\to\sneakers.jpg
```

## 4. Дымовой тест перед долгим обучением

Если хочется проверить пайплайн на маленькой выборке:

```powershell
python backend\scripts\prepare_wardrobe_training_manifest.py --output-dir data\processed\wardrobe_training_smoke --max-samples-per-label 100
python backend\scripts\train_wardrobe_manifest_classifier.py --manifest-path data\processed\wardrobe_training_smoke\manifest.csv --epochs 1 --batch-size 8 --max-train-samples 300 --max-val-samples 80 --no-pretrained --log-every 5
```

## 5. Как подключить iFashion позже

Положи в `data/raw/ifashion/imat_fashion_comp-master`:

- `train.json`
- `val.json`
- скачанные изображения из URL, указанных в JSON

После этого просто заново запусти:

```powershell
python backend\scripts\prepare_wardrobe_training_manifest.py
```

Если изображения лежат в `images`, `train`, `val`, `train_images` или `val_images`, скрипт сам добавит поддержанные iFashion-категории в общий `manifest.csv`.
