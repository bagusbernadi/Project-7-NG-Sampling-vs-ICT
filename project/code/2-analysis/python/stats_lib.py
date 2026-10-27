"""Fungsi statistik kecil: interval Wilson dan kebutuhan jumlah unit."""
import math

Z95 = 1.959963984540054


def wilson(k, n, z=Z95):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - h) / d, (c + h) / d)


def n_needed(p, margin, z=Z95):
    """Jumlah unit agar setengah lebar interval normal <= margin pada NG rate p."""
    return math.ceil(z * z * p * (1 - p) / (margin * margin))
