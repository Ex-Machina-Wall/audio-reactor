import numpy as np

x = None
WIDTH = 17
HEIGHT = 13
NUM_PIXELS = 73
MAPPING = [
    [x,  x,  x,  64, x,  54, x,  44, x,  34, x,  24, x,  14, x,  x,  x],
    [x,  x,  x,  x,  55, x,  x,  x,  35, x,  x,  x,  15, x,  x,  x,  x],
    [x,  71, x,  63, x,  53, x,  43, x,  33, x,  23, x,  13, x,  4,  x],
    [x,  x,  65, x,  x,  x,  45, x,  x,  x,  25, x,  x,  x,  5,  x,  x],
    [x,  70, x,  62, x,  52, x,  42, x,  32, x,  22, x,  12, x,  3,  x],
    [72, x,  x,  x,  56, x,  x,  x,  36, x,  x,  x,  16, x,  x,  x,  0],
    [x,  69, x,  61, x,  51, x,  41, x,  31, x,  21, x,  11, x,  2,  x],
    [x,  x,  66, x,  x,  x,  46, x,  x,  x,  26, x,  x,  x,  6,  x,  x],
    [x,  68, x,  60, x,  50, x,  40, x,  30, x,  20, x,  10, x,  1,  x],
    [x,  x,  x,  x,  57, x,  x,  x,  37, x,  x,  x,  17, x,  x,  x,  x],
    [x,  x,  x,  59, x,  49, x,  39, x,  29, x,  19, x,  9,  x,  x,  x],
    [x,  x,  67, x,  x,  x,  47, x,  x,  x,  27, x,  x,  x,  7,  x,  x],
    [x,  x,  x,  58, x,  48, x,  38, x,  28, x,  18, x,  8,  x,  x,  x]
]


# Sum of the min & max of (a, b, c)
def hilo(a, b, c):
    if c < b:
        b, c = c, b
    if b < a:
        a, b = b, a
    if c < b:
        b, c = c, b
    return a + c


def complement(r, g, b):
    k = hilo(r, g, b)
    return tuple(k - u for u in (r, g, b))


def convert_incoming_color(r, g, b):
    r = int(1.1*int(r))
    g = int(1.1*int(g))
    b = int(1.1*int(b))
    return r, g, b


class LoopBuffer:
    def __init__(self, size, default_value=0):
        self.size = size
        self.buffer = [default_value] * size
        self.index = 0

    def append(self, value):
        self.buffer[self.index] = value
        self.index = (self.index + 1) % self.size

    def max(self) -> float:
        return max(self.buffer)

    def min(self) -> float:
        return min(self.buffer)

    def average(self) -> float:
        return sum(self.buffer) / self.size

    def override_all(self, value):
        self.buffer = [value] * self.size

    def override_last(self, value):
        self.buffer[self.index] = value

    def variance(self) -> float:
        return np.var(self.buffer)

