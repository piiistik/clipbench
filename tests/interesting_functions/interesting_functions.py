from typing import Tuple
import math


def square_with_minima(pt: Tuple[int, int]) -> float:
    """
    Like your original, but the four 'corner' local minima are moved inward
    (so they are visibly away from the exact corners) and given wider sigma
    so each local well forms a visible neighborhood.
    """
    x, y = pt
    if not (isinstance(x, int) and isinstance(y, int)):
        raise TypeError("Inputs must be integers.")
    if not (1 <= x <= 1000 and 1 <= y <= 1000):
        raise ValueError("Inputs must be in range 1..1000 (inclusive).")

    base = 5.0

    # moved inward from true corners so their neighborhoods are visible
    corner_centers = [(100, 100), (100, 900), (900, 100), (900, 900)]
    sigma_corner = 60.0  # wider spread -> visible local basin
    A_corner = 1.2  # slightly deeper so it's clearly visible

    # center global minimum (still much deeper)
    center_x, center_y = 500.5, 500.5
    sigma_center = 120.0  # wider central well
    A_center = 4.0

    def gauss(xx, yy, xc, yc, sigma):
        r2 = (xx - xc) ** 2 + (yy - yc) ** 2
        return math.exp(-r2 / (2 * sigma * sigma))

    value = base
    for cx, cy in corner_centers:
        value -= A_corner * gauss(x, y, cx, cy, sigma_corner)
    value -= A_center * gauss(x, y, center_x, center_y, sigma_center)

    # tiny regularizer to break perfect symmetry (keeps positivity)
    value += 1e-6 * (x - y)

    return float(value)


def square_with_maxima(pt: Tuple[int, int]) -> float:
    """
    Mirrored version: moved-in corner maxima (visible neighborhoods) and a
    strong central global maximum. Structure mirrors square_with_minima.
    """
    x, y = pt
    if not (isinstance(x, int) and isinstance(y, int)):
        raise TypeError("Inputs must be integers.")
    if not (1 <= x <= 1000 and 1 <= y <= 1000):
        raise ValueError("Inputs must be in range 1..1000 (inclusive).")

    base = 1.0

    # moved inward peak centers
    corner_centers = [(100, 100), (100, 900), (900, 100), (900, 900)]
    sigma_corner = 60.0  # visible local hump
    A_corner = 1.2

    center_x, center_y = 500.5, 500.5
    sigma_center = 120.0
    A_center = 4.0

    def gauss(xx, yy, xc, yc, sigma):
        r2 = (xx - xc) ** 2 + (yy - yc) ** 2
        return math.exp(-r2 / (2 * sigma * sigma))

    value = base
    for cx, cy in corner_centers:
        value += A_corner * gauss(x, y, cx, cy, sigma_corner)
    value += A_center * gauss(x, y, center_x, center_y, sigma_center)

    # tiny tilt to avoid exact symmetry
    value += 1e-6 * (x - y)

    return float(value)


# ---------- Helper: logistic / sigmoid ----------
def _sigmoid(t: float) -> float:
    # numerically stable sigmoid
    if t >= 0:
        z = math.exp(-t)
        return 1.0 / (1.0 + z)
    else:
        z = math.exp(t)
        return z / (1.0 + z)


# ---------- 1) cliff_ridge: low everywhere, high on a band (vertical ridge) ----------
def cliff_ridge(pt: Tuple[int, int]) -> float:
    """
    Mostly low values (~base_low) across the plane, with a tall ridge centered
    at x = 300 (vertical band). Ridge has Gaussian cross-section in x so it's localised,
    but it spans the full y-range so it's effectively 'across' the space.
    """
    x, y = pt
    if not (isinstance(x, int) and isinstance(y, int)):
        raise TypeError("Inputs must be integers.")
    if not (1 <= x <= 1000 and 1 <= y <= 1000):
        raise ValueError("Inputs must be in range 1..1000 (inclusive).")

    base_low = 1.0  # base background (low)
    ridge_height = (
        6.0  # height added at the ridge peak (so ridge peak ≈ base_low + ridge_height)
    )
    ridge_x = 300.0  # center of the vertical ridge (away from center)
    sigma_x = 20.0  # narrowness of the ridge in x (smaller -> sharper)

    # vertical band (no y-dependence except tiny smoothing via sigma_y if desired)
    gauss_x = math.exp(-((x - ridge_x) ** 2) / (2 * sigma_x * sigma_x))

    value = base_low + ridge_height * gauss_x

    # tiny asymmetry tilt to avoid exact symmetry
    value += 1e-7 * (x - y)

    return float(value)


# ---------- 2) cliff_step: high -> cliff -> low (vertical step/cliff) ----------
def cliff_step(pt: Tuple[int, int]) -> float:
    """
    Produces a left-side HIGH plateau, a steep vertical 'cliff' around x = 300,
    and a right-side LOW plateau:
        left (x << 300)  -> high_value
        middle (around 300) -> steep transition
        right (x >> 300) -> low_value
    Smooth logistic used for the step; steepness controlled by 'k'.
    """
    x, y = pt
    if not (isinstance(x, int) and isinstance(y, int)):
        raise TypeError("Inputs must be integers.")
    if not (1 <= x <= 1000 and 1 <= y <= 1000):
        raise ValueError("Inputs must be in range 1..1000 (inclusive).")

    low_value = 1.0  # value to the right of the cliff
    high_value = 6.0  # value to the left of the cliff
    cliff_x = 300.0  # location of the vertical cliff
    k = 6.0  # steepness parameter (smaller -> steeper cliff)

    # create a left->right decreasing sigmoid: near 1 for x << cliff_x, near 0 for x >> cliff_x
    t = (x - cliff_x) / k
    left_weight = _sigmoid(-t)  # = 1/(1+exp((x-cliff_x)/k)), near 1 on left, 0 on right

    value = low_value + (high_value - low_value) * left_weight

    # optional modulation so the cliff isn't exactly the same at every y (small)
    # you can comment this out if you want perfectly vertical cliff
    value *= 1.0 + 0.00005 * math.sin(y * 0.02)

    # tiny asymmetry tilt
    value += 1e-7 * (x - y)

    return float(value)


from typing import Tuple

# epsilon to keep positivity
_EPS = 1e-8


def combine_minima_with_ridge(
    pt: Tuple[int, int], w_min: float = 1.0, w_ridge: float = 1.0
) -> float:
    """
    Combine the minima landscape and the vertical ridge by weighted sum.
    Result = w_min * square_with_minima(pt) + w_ridge * cliff_ridge(pt)
    """
    # reuse validation from underlying functions will raise if invalid
    v = w_min * square_with_minima(pt) + w_ridge * cliff_ridge(pt)
    return float(max(v, _EPS))


def combine_maxima_with_ridge(
    pt: Tuple[int, int], w_max: float = 1.0, w_ridge: float = 1.0
) -> float:
    """
    Combine the maxima landscape and the vertical ridge by weighted sum.
    Result = w_max * square_with_maxima(pt) + w_ridge * cliff_ridge(pt)
    """
    v = w_max * square_with_maxima(pt) + w_ridge * cliff_ridge(pt)
    return float(max(v, _EPS))


def combine_minima_with_step(
    pt: Tuple[int, int], w_min: float = 1.0, w_step: float = 1.0
) -> float:
    """
    Combine minima landscape with a step/cliff (plateau -> cliff -> valley).
    Result = w_min * square_with_minima(pt) + w_step * cliff_step(pt)
    """
    v = w_min * square_with_minima(pt) + w_step * cliff_step(pt)
    return float(max(v, _EPS))


def combine_maxima_with_step(
    pt: Tuple[int, int], w_max: float = 1.0, w_step: float = 1.0
) -> float:
    """
    Combine maxima landscape with a step/cliff.
    Result = w_max * square_with_maxima(pt) + w_step * cliff_step(pt)
    """
    v = w_max * square_with_maxima(pt) + w_step * cliff_step(pt)
    return float(max(v, _EPS))


from typing import Tuple
import math


def curved_cliff(
    pt: Tuple[int, int],
    *,
    x0: float = 1.0,
    x1: float = 1000.0,
    amp: float = 2.5,
    cross_sigma: float = 18.0,
    freq1: float = 0.012,  # first sinusoid frequency (controls large bend)
    freq2: float = 0.035,  # second sinusoid frequency (controls smaller wiggles)
    a1: float = 100.0,  # amplitude of first sinusoid (pixels)
    a2: float = 40.0,  # amplitude of second sinusoid (pixels)
    baseline: float = 0.0,  # baseline added to whole field
    sign: float = 1.0,  # +1 => ridge (high values on curve), -1 => trench
) -> float:
    """
    Smooth curved cliff/ridge whose centerline is y_c(x) = center_base + a1*sin(freq1 * x) + a2*sin(freq2 * x).
    The function returns baseline + sign * amp * exp(-dist^2 / (2*cross_sigma^2)), where dist is vertical distance
    from the point (x,y) to the curve y_c(x). This creates a narrow wavy ridge/trench that bends multiple times.

    Parameters
    ----------
    pt : Tuple[int,int]
        integer coordinates in [1,1000]
    x0, x1 : float
        effective domain in x to consider (keeps centerline defined across grid)
    amp : float
        peak amplitude of the ridge (positive). Use sign=-1 for a trench.
    cross_sigma : float
        gaussian spread perpendicular to the centerline (controls sharpness of cliff)
    freq1, freq2, a1, a2 : floats
        parameters of the sum-of-sinusoids centerline; a1 controls the large bending, a2 adds at least a second curvature
    baseline : float
        baseline to add to the whole output (useful when combining)
    sign : float
        +1 = ridge/high band, -1 = trench/low band
    """
    x, y = pt
    if not (isinstance(x, int) and isinstance(y, int)):
        raise TypeError("Inputs must be integers.")
    if not (1 <= x <= 1000 and 1 <= y <= 1000):
        raise ValueError("Inputs must be in range 1..1000 (inclusive).")

    # centerline y coordinate as a function of x — sum of two sinusoids -> at least two bends
    # we pick a base centerline around mid-y so the curve wiggles across the domain
    center_base = 500.0  # around center
    # compute continuous x (float) — clamp into [x0, x1] if needed
    xf = float(min(max(x, x0), x1))

    y_center = center_base + a1 * math.sin(freq1 * xf) + a2 * math.sin(freq2 * xf + 0.6)

    # distance perpendicular approximated by vertical distance since the curve is single-valued y(x)
    # (this is fine when slope is moderate; if you need true perpendicular distance for steep slopes,
    # compute the shortest distance to the parametric curve — but vertical distance is simple and smooth)
    dist = y - y_center

    # gaussian cross-section across the curve
    cross = math.exp(-(dist * dist) / (2.0 * cross_sigma * cross_sigma))

    value = baseline + sign * amp * cross

    # tiny asymmetric tilt to break perfect symmetry (harmless)
    value += 1e-7 * (x - y)

    # ensure returned type is float
    return float(value)


from typing import Tuple
import math


def complex_landscape_with_curved_cliff(pt: Tuple[int, int]) -> float:
    """
    Complex landscape that reuses curved_cliff as one of the cliffs.
    Components:
      - base level
      - two local minima (wells)
      - two local maxima (humps)
      - one vertical ridge (x ≈ 300)
      - one horizontal trench (y ≈ 600)
      - one curved cliff/ridge (from curved_cliff)
    """
    x, y = pt
    if not (isinstance(x, int) and isinstance(y, int)):
        raise TypeError("Inputs must be integers.")
    if not (1 <= x <= 1000 and 1 <= y <= 1000):
        raise ValueError("Inputs must be in range 1..1000 (inclusive).")

    EPS = 1e-8
    base = 4.0

    # two maxima (humps)
    maxima_centers = [(280.0, 680.0), (720.0, 320.0)]
    maxima_sigma = 70.0
    maxima_amp = 1.5

    # two minima (wells)
    minima_centers = [(280.0, 320.0), (720.0, 680.0)]
    minima_sigma = 60.0
    minima_amp = 1.8

    def gauss2(xx, yy, xc, yc, sigma):
        r2 = (xx - xc) ** 2 + (yy - yc) ** 2
        return math.exp(-r2 / (2.0 * sigma * sigma))

    value = base

    # add maxima
    for mx, my in maxima_centers:
        value += maxima_amp * gauss2(x, y, mx, my, maxima_sigma)

    # subtract minima
    for wx, wy in minima_centers:
        value -= minima_amp * gauss2(x, y, wx, wy, minima_sigma)

    # vertical ridge (same as before)
    ridge1_x = 300.0
    ridge1_sigma = 18.0
    ridge1_height = 3.5
    value += ridge1_height * math.exp(
        -((x - ridge1_x) ** 2) / (2.0 * ridge1_sigma * ridge1_sigma)
    )

    # horizontal trench (same as before)
    trench_y = 600.0
    trench_sigma = 25.0
    trench_depth = 2.8
    value -= trench_depth * math.exp(
        -((y - trench_y) ** 2) / (2.0 * trench_sigma * trench_sigma)
    )

    # curved cliff (reuse)
    # choose parameters so the curved cliff is noticeable and crosses the domain wavy
    # sign=+1 => ridge; use sign=-1 to make it a trench; here we add a ridge-like curved band
    value += curved_cliff(
        pt,
        amp=2.2,
        cross_sigma=20.0,
        freq1=0.010,
        freq2=0.028,
        a1=140.0,
        a2=55.0,
        baseline=0.0,
        sign=1.0,
    )

    # small modulation and tilt
    value += 0.06 * math.sin(0.014 * x) * math.cos(0.011 * y)
    value += 1e-7 * (x - y)

    return float(max(value, EPS))
