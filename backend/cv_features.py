from __future__ import annotations

import io
from pathlib import Path
from typing import BinaryIO

import numpy as np
from PIL import Image, ImageFilter, ImageStat
from skimage.color import rgb2gray
from skimage.feature import hog


IMAGE_SIZE = (128, 128)
HISTOGRAM_BINS = 16


def open_rgb_image(image_path_or_bytes: str | Path | bytes | BinaryIO) -> Image.Image:
    if isinstance(image_path_or_bytes, (str, Path)):
        return Image.open(image_path_or_bytes).convert("RGB")
    if isinstance(image_path_or_bytes, bytes):
        return Image.open(io.BytesIO(image_path_or_bytes)).convert("RGB")
    return Image.open(image_path_or_bytes).convert("RGB")


def color_shape_features(image: Image.Image) -> np.ndarray:
    width, height = image.size
    resized = image.resize(IMAGE_SIZE)
    arr = np.asarray(resized, dtype=np.float32) / 255.0
    stat = ImageStat.Stat(resized)

    means = np.asarray(stat.mean, dtype=np.float32) / 255.0
    stds = np.asarray(stat.stddev, dtype=np.float32) / 255.0
    extrema = np.asarray(stat.extrema, dtype=np.float32).reshape(-1) / 255.0
    aspect_ratio = np.asarray([width / max(height, 1), height / max(width, 1)], dtype=np.float32)

    histograms = []
    for channel in range(3):
        hist, _ = np.histogram(arr[:, :, channel], bins=HISTOGRAM_BINS, range=(0.0, 1.0), density=True)
        histograms.append(hist.astype(np.float32))

    edges = resized.convert("L").filter(ImageFilter.FIND_EDGES)
    edge_arr = np.asarray(edges, dtype=np.float32) / 255.0
    edge_features = np.asarray([edge_arr.mean(), edge_arr.std()], dtype=np.float32)

    return np.concatenate([aspect_ratio, means, stds, extrema, edge_features, *histograms]).astype(np.float32)


def hog_features(image: Image.Image) -> np.ndarray:
    resized = image.resize(IMAGE_SIZE)
    arr = np.asarray(resized, dtype=np.float32) / 255.0
    gray = rgb2gray(arr)
    return hog(
        gray,
        orientations=9,
        pixels_per_cell=(16, 16),
        cells_per_block=(2, 2),
        block_norm="L2-Hys",
        feature_vector=True,
    ).astype(np.float32)


def extract_features(image_path_or_bytes: str | Path | bytes | BinaryIO, feature_set: str = "hybrid") -> np.ndarray:
    image = open_rgb_image(image_path_or_bytes)
    if feature_set == "color_shape":
        return color_shape_features(image)
    if feature_set == "hog":
        return hog_features(image)
    if feature_set == "hybrid":
        return np.concatenate([color_shape_features(image), hog_features(image)]).astype(np.float32)
    raise ValueError(f"Unsupported feature_set: {feature_set}")
