# Training datasets

This project should start with catalog-like datasets because uploaded wardrobe photos are processed as one item with removed background.

## Download first

1. Fashion Product Images Small

Use it first for the main item classifier: item type, family, base color, season, and usage.

Site: https://www.kaggle.com/datasets/paramaggarwal/fashion-product-images-small

Expected files after unpacking:

```text
data/raw/fpid_small/
  images/
  styles.csv
```

PowerShell:

```powershell
pip install kaggle
kaggle auth login
New-Item -ItemType Directory -Force data/raw/fpid_small
kaggle datasets download -d paramaggarwal/fashion-product-images-small -p data/raw/fpid_small
Expand-Archive data/raw/fpid_small/*.zip -DestinationPath data/raw/fpid_small -Force
```

2. Fashion Product Images Full

Use it after the small version works.

Site: https://www.kaggle.com/datasets/paramaggarwal/fashion-product-images-dataset

```powershell
New-Item -ItemType Directory -Force data/raw/fpid_full
kaggle datasets download -d paramaggarwal/fashion-product-images-dataset -p data/raw/fpid_full
Expand-Archive data/raw/fpid_full/*.zip -DestinationPath data/raw/fpid_full -Force
```

3. iMaterialist Fashion Attribute Dataset

Use it later for material, pattern, sleeve, neckline, style, and gender attributes.

Site: https://github.com/visipedia/imat_fashion_comp

Download:

- `train.json`
- `val.json`
- `iMat_fashion_2018_label_map_228.csv`

Images are downloaded separately from URLs inside the JSON files.

4. UT Zappos50K

Use it later as a separate shoe specialist.

Site: https://vision.cs.utexas.edu/projects/finegrained/utzap50k/

Download:

- `readme.txt`
- `ut-zap50k-data.zip`
- `ut-zap50k-images-square.zip`

## Not first

Fashionpedia and DeepFashion2 are useful later for segmentation, clothing parts, and photos with people or complex scenes. They are not required for the first working classifier.

## Local machine estimate

Detected machine:

- CPU: Intel Core i7-11700, 8 cores / 16 threads
- RAM: 32 GB
- GPU: NVIDIA GeForce RTX 3050, 4 GB VRAM
- Current PyTorch: CPU-only, CUDA is not available
- Free disk on `C:`: about 83 GB

Expected first-run training time with `efficientnet_b0` on Fashion Product Images Small:

- CPU-only: roughly 1.5-4 hours for 4 epochs, depending on image count and selected classes.
- RTX 3050 with CUDA PyTorch: roughly 20-60 minutes for 4 epochs.

The full FPID dataset and iMaterialist are much heavier. Train and validate the small FPID model first.

## Recommended first command

From `backend/`:

```powershell
.\.venv\Scripts\python.exe scripts\train_fpid_classifier.py `
  --dataset-dir data\raw\fpid_small `
  --epochs 4 `
  --batch-size 16 `
  --max-classes 40 `
  --num-workers 0
```

The script prints dataset validation, class counts, device, epoch progress, batch progress, ETA, validation accuracy, and final checkpoint paths.

It also writes epoch metrics to:

```text
backend/training_logs/fpid_training_metrics.jsonl
```

The trained checkpoint is saved to the paths already used by the backend image analyzer:

```text
backend/model_artifacts/deepfashion_classifier.pt
backend/model_artifacts/deepfashion_classifier.metadata.json
```

After training, restart the backend and the local classifier will be used before the zero-shot fallback.

## GPU note

The current environment has `torch 2.6.0+cpu`, so CUDA is not available even though the computer has an RTX 3050. To use the GPU, install a CUDA-enabled PyTorch build from the official selector:

https://pytorch.org/get-started/locally/

Pick:

- OS: Windows
- Package: Pip
- Language: Python
- Compute Platform: CUDA

Then run the command shown by PyTorch inside `backend\.venv`.
