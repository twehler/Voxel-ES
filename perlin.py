import numpy as np
import matplotlib.pyplot as plt

def fade(t):
    """Smoothing function: 6t^5 - 15t^4 + 10t^3"""
    return t**3 * (t * (t * 6 - 15) + 10)

def lerp(a, b, x):
    """Linear interpolation"""
    return a + x * (b - a)

def generate_perlin_noise_2d(width, height, scale, seed=42):
    np.random.seed(seed)

    # Create grid of random generated vectors
    # use angles to ensure unit length

    grid_w = int(width * scale)
    grid_h = int(height * scale)
    angles = 2 * np.pi * np.random.rand(grid_w, grid_h) # create random vectors
    gradients = np.stack((np.cos(angles), np.sin(angles)), axis=-1)
