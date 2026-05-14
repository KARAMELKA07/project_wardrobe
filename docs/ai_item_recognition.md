# AI-assisted item recognition

## What is implemented now

The project now supports a hybrid clothing-image analysis flow:

1. `rembg` removes the background from the uploaded image;
2. the backend first tries to use a **local DeepFashion-based classifier**;
3. if the local classifier is unavailable or uncertain, the backend falls back to a zero-shot classifier;
4. dominant colors are extracted from the processed image;
5. the wardrobe form receives structured suggestions for the item card.

This keeps the existing outfit-ranking core intact and strengthens the digitization stage of the wardrobe.

## Why DeepFashion was added

The previous MVP used only a generic zero-shot model. That was enough to demonstrate intelligent methods, but it was not accurate enough for similar clothing classes.

DeepFashion is integrated as a training source for a local classifier. This gives the project a more realistic path to higher fashion-specific accuracy without rebuilding the rest of the system.

## What the DeepFashion integration covers

The project now contains:

- a DeepFashion dataset parser;
- a mapping from DeepFashion raw categories to the project wardrobe taxonomy;
- a training script for a local classifier;
- runtime support for loading a trained local checkpoint;
- a safe fallback to the previous zero-shot recognizer.

## Expected DeepFashion dataset structure

Default path:

`backend/Category and Attribute Prediction Benchmark`

The dataset folder should contain:

- `Anno_coarse/`
- `Eval/`
- `img/` or `Img/img/`

Important: annotations alone are not enough. The `Clothes Images` archive must also be downloaded and unpacked.

## What is used from DeepFashion

For this project the most useful DeepFashion parts are:

- category annotations;
- bounding boxes;
- train / val / test partitions;
- clothes images.

These are enough to train a local classifier for clothing type recognition.

## How categories are used

DeepFashion raw categories are mapped to the internal wardrobe taxonomy. Examples:

- `Button-Down` -> `shirt`
- `Blazer` -> `blazer`
- `Blouse` -> `blouse`
- `Cardigan` -> `cardigan`
- `Hoodie` -> `hoodie`
- `Tee` -> `t_shirt`
- `Turtleneck` -> `turtleneck`
- `Jeans` -> `jeans`
- `Joggers` -> `joggers`
- `Skirt` -> `skirt`
- `Shorts` -> `shorts`
- `Coat` -> `coat`
- `Jacket` -> `jacket`
- `Parka` -> `parka`

Unsupported full-body classes are intentionally skipped because the current outfit generator works with separated wardrobe categories.

## Training a local model

Added script:

`backend/scripts/train_deepfashion_classifier.py`

The script:

- reads supported classes from DeepFashion;
- applies bbox cropping;
- trains `EfficientNet-B0` or `ResNet50`;
- saves a local checkpoint and metadata.

Expected outputs:

- `backend/model_artifacts/deepfashion_classifier.pt`
- `backend/model_artifacts/deepfashion_classifier.metadata.json`

## Runtime flow in the web service

When the user uploads a new item image:

1. the image is sent to `POST /api/items/analyze-image`;
2. background removal is applied;
3. the local DeepFashion model is used first;
4. if it is missing or gives low confidence, the zero-shot fallback is used;
5. the backend returns suggested `category`, `subcategory`, `colors` and derived metadata.

## Current practical limitation

If the dataset folder contains only annotations and no image folder, the local model cannot be trained yet.

The backend still works in this case, but it will remain in fallback mode until:

1. `Clothes Images` are unpacked;
2. the local classifier is trained;
3. the checkpoint files are created.

## Main backend entry point

- `POST /api/items/analyze-image`

## Related project files

- `backend/app/services/fashion_image_service.py`
- `backend/app/services/deepfashion_dataset.py`
- `backend/app/services/deepfashion_classifier.py`
- `backend/scripts/train_deepfashion_classifier.py`
