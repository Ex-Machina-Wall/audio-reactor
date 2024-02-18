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