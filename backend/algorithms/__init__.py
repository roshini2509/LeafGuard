"""
The four algorithms of LeafGuard, each implemented from scratch in its own module:

    kmeans.py                   K-Means colour clustering
    hsv_segmentation.py         manual RGB->HSV conversion + threshold segmentation
    histogram_equalization.py   histogram, CDF, transformation table
    canny.py                    Gaussian, Sobel, NMS, double threshold, hysteresis

Each run_* function receives a COPY of the original uploaded image (never another
algorithm's output).
"""
