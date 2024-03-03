import numpy as np


"""
Cubic Hermite curve constructor.

Takes an array of points and constructs a smooth cyclic curve that
passes through all of them using successive approximation.

Properties:

1. Near constant speed, ie magnitude of first differential.
2. Near continuous curvature.

"""


def rotate_vectors_3d(vectors, angles):
    x = vectors.T[0]
    y = vectors.T[1]
    z = vectors.T[2]
    xx = x * np.cos(angles) + y * np.sin(angles)
    yy = -x * np.sin(angles) + y * np.cos(angles)
    result = np.stack([xx, yy, z], axis=1)
    result /= np.linalg.norm(result, axis=1)[..., np.newaxis]
    return result


def rotate_vectors_2d(vectors, angles):
    x = vectors.T[0]
    y = vectors.T[1]
    xx = x * np.cos(angles) + y * np.sin(angles)
    yy = -x * np.sin(angles) + y * np.cos(angles)
    result = np.stack([xx, yy], axis=1)
    result /= np.linalg.norm(result, axis=1)[..., np.newaxis]
    return result


def rotate_vectors(vectors, angles):
    if vectors.shape[1] == 3:
        return rotate_vectors_3d(vectors, angles)
    else:
        return rotate_vectors_2d(vectors, angles)


def cyclic_diff(arr, first, second):
    a = np.roll(arr, -first, axis=0)
    b = np.roll(arr, -second, axis=0)
    return b - a


def m(P0, tangents, lengths):
    P1 = np.roll(P0, -1, axis=0)
    M0 = tangents * lengths[..., np.newaxis]
    M1 = np.roll(tangents, -1, axis=0) * lengths[..., np.newaxis]
    return P1, M0, M1


def coeffs(P0, P1, M0, M1):
    A = (2 * P0) + M0 - (2 * P1) + M1
    B = (-3 * P0) + (-2 * M0) + (3 * P1) - M1
    return A, B


def eval(P0, M0, A, B, lengths, steps: (int, list[int]) = 3):
    P0 = P0[:, np.newaxis, :]
    M0 = M0[:, np.newaxis, :]
    A = A[:, np.newaxis, :]
    B = B[:, np.newaxis, :]
    if isinstance(steps, int):
        t = np.linspace(0, 1, steps)[np.newaxis, :, np.newaxis]
    else:
        t = np.array(steps)[np.newaxis, :, np.newaxis]
    t2 = t ** 2
    t3 = t ** 3
    r = (A * t3) + (B * t2) + (M0 * t) + P0
    dr = (3 * A * t2) + (2 * B * t) + M0
    ddr = (6 * A * t) + (2 * B)
    il = 1 / lengths[..., np.newaxis, np.newaxis]
    return r, dr * il, ddr * il * il


def base_lengths(P0):
    return np.linalg.norm(cyclic_diff(P0, 0, 1), axis=1)


def base_tangents(P0):
    tangents = cyclic_diff(P0, -1, 1)
    tangents /= np.linalg.norm(tangents, axis=1)[..., np.newaxis]
    return tangents


def estimate_lengths(p):
    diff = np.diff(p, axis=1)
    norm = np.linalg.norm(diff, axis=2)
    return np.sum(norm, axis=1).flatten()


def estimate_distances(p):
    diff = np.diff(p, axis=1, prepend=p[:, :1, :])
    norm = np.linalg.norm(diff, axis=2)
    l = np.sum(norm, axis=1).flatten()
    norm[1:, 0] = np.cumsum(l[:-1])
    return np.cumsum(norm, axis=1)


def curvature(dp, ddp):
    num = np.linalg.norm(dp, axis=2)**3
    den = (dp[:, :, 0]*ddp[:, :, 1]) - (dp[:, :, 1]*ddp[:, :, 0])
    return den/num


def discontinuity(dp, ddp):
    c = curvature(dp, ddp)
    return np.roll(c[:, -1], 1, axis=0) - c[:, 0]


def _construct(P0, tangents, lengths):
    P1, M0, M1 = m(P0, tangents, lengths)
    A, B = coeffs(P0, P1, M0, M1)
    return M0, A, B


def construct(P0, tangents=None, lengths=None):
    if tangents is None:
        tangents = base_tangents(P0)
    if lengths is None:
        lengths = base_lengths(P0)

    M0, A, B = _construct(P0, tangents, lengths)
    return M0, A, B, tangents, lengths


def optimize(P0, tangents, lengths, max_opt_its=1, opt_steps=32):
    M0, A, B = _construct(P0, tangents, lengths)

    for n in range(max_opt_its):
        # update length approximation
        p, dp, ddp = eval(P0, M0, A, B, lengths, steps=opt_steps)
        lengths = estimate_lengths(p)
        M0, A, B = _construct(P0, tangents, lengths)

        # turn tangents towards curvature discontinuity
        p, dp, ddp = eval(P0, M0, A, B, lengths, steps=[0, 1])
        e = discontinuity(dp[:, :2], ddp[:, :2])
        if np.sum(np.abs(e)) < 1e-10:
            break

        tangents = rotate_vectors(tangents, e) # FIXME: THIS ONLY WORKS ON 2D VECTORS!

        M0, A, B = _construct(P0, tangents, lengths)

    p, dp, ddp = eval(P0, M0, A, B, lengths, steps=opt_steps)
    lengths = estimate_lengths(p)
    M0, A, B = _construct(P0, tangents, lengths)

    return M0, A, B, tangents, lengths
