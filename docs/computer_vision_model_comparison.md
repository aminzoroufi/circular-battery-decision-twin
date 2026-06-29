# Computer Vision Battery Type Classification

## Purpose

I changed the battery type classifier so runtime prediction uses the image pixels, not the file name. Dataset folder names are used only as ground-truth labels during training and evaluation. This avoids label leakage from filenames such as `recybat24_pouch_030_38_4_F_2_po.jpg`.

The model classifies each battery image into one of three visible form factors:

- `cylindrical`
- `pouch`
- `prismatic`

## Dataset

The comparison uses the active RecyBat24 subset in `data/images`:

- 30 cylindrical images
- 30 pouch images
- 30 prismatic images
- 90 images total

## Compared Methods

I compared four computer-vision classification methods:

| Method | Features | Reason for Testing |
|---|---|---|
| Logistic Regression | color, shape, edge density | Fast interpretable baseline |
| Random Forest | color, shape, edge density | Non-linear handcrafted-feature baseline |
| Linear SVM | HOG gradient features | Strong shape-based classifier for small image datasets |
| RBF SVM | HOG + color/shape hybrid | Non-linear classifier using combined visual features |

## Feature Extraction

I implemented shared feature extraction in `backend/cv_features.py`.

The feature sets are:

- `color_shape`: aspect ratio, RGB means, RGB standard deviations, RGB extrema, edge statistics, and RGB histograms.
- `hog`: Histogram of Oriented Gradients from a 128 x 128 grayscale image.
- `hybrid`: concatenation of `color_shape` and `hog`.

HOG was selected as the best feature representation because battery form factor is largely a shape problem. Cylindrical, pouch, and prismatic batteries have different edge and gradient structures.

## Evaluation Method

The script `scripts/train_compare_cv_models.py` performs:

- stratified 70/30 holdout split;
- 5-fold stratified cross-validation;
- accuracy measurement;
- macro F1 measurement;
- confusion matrix generation;
- final model training on all 90 images;
- model artifact export to `backend/trained_models/battery_type_classifier.joblib`;
- evaluation report export to `outputs/model_evaluation/battery_type_model_comparison.json`.

## Results

| Rank | Model | Feature Set | 5-Fold CV Accuracy | 5-Fold Macro F1 | Holdout Accuracy |
|---:|---|---|---:|---:|---:|
| 1 | `linear_svm_hog` | HOG | 98.89% | 98.88% | 96.30% |
| 2 | `logistic_regression_color_shape` | Color + shape | 96.67% | 96.60% | 96.30% |
| 3 | `rbf_svm_hybrid` | HOG + color/shape | 95.56% | 95.52% | 96.30% |
| 4 | `random_forest_color_shape` | Color + shape | 94.44% | 94.36% | 88.89% |

## Selected Model

I selected:

```text
linear_svm_hog
```

The selected model uses:

```text
HOG features + Linear Support Vector Machine
```

The validation trust percentage reported by the system is:

```text
98.89%
```

This percentage is the mean 5-fold cross-validation accuracy on the current RecyBat24 subset.

## Why I Selected This Model

I selected the HOG + Linear SVM model because it achieved the highest cross-validation accuracy and macro F1 score. It is also theoretically appropriate because the classification problem is primarily based on visible shape. HOG captures edge direction and gradient structure, while a linear SVM works well on small datasets with high-dimensional feature vectors.

I did not select the Random Forest because it performed worse on holdout accuracy. I did not select the RBF SVM because it did not improve over the simpler linear SVM. I did not select Logistic Regression because, although it performed well, its cross-validation score was lower than the HOG + Linear SVM model.

## Runtime Behavior

At runtime, `backend/model.py` loads:

```text
backend/trained_models/battery_type_classifier.joblib
```

Then it:

1. opens the uploaded image;
2. extracts HOG features;
3. predicts the class with the trained Linear SVM;
4. returns the predicted class, confidence, model name, validation trust percentage, and class probabilities.

The filename is ignored during prediction.

## Limitations

The current trust percentage is based on a small 90-image subset. It is useful for the prototype, but it should not be interpreted as production accuracy. A production model would require a larger dataset, more lighting conditions, more camera angles, damaged batteries, conveyor backgrounds, external validation, and real factory testing.

## Defense Answer

If asked why I chose this model, I would answer:

> I compared multiple computer-vision classifiers using the same dataset and the same evaluation protocol. The HOG + Linear SVM model achieved the best 5-fold cross-validation accuracy at 98.89%. I selected it because battery type classification is mainly a shape-recognition problem, and HOG is well suited for representing edge and gradient structure. I also preferred it over a deep model at this stage because the available dataset is small, and a lightweight model is easier to explain and validate for a prototype.
