import math
import pytest
import numpy as np
from editor.core import hermite


@pytest.fixture(params=["simple_2D", "simple_3D", "circle_2D", "circle_3D"])
def points(request):
    match request.param:
        case "simple_2D":
            return np.array([[1, 0], [0, 1], [-1, 0], [0, -1]], dtype=float)
        case "simple_3D":
            return np.array([[1, 0, 1], [0, 1, 0], [-1, 0, -1], [0, -1, 0]], dtype=float)
        case "circle_2D":
            rads = ([math.radians(d) for d in range(0, 180, 15)] +
                    [math.radians(d) for d in range(180, 360, 45)])
            return np.array([(math.sin(r), math.cos(r)) for r in rads], dtype=float)
        case "circle_3D":
            rads = ([math.radians(d) for d in range(0, 180, 15)] +
                    [math.radians(d) for d in range(180, 360, 45)])
            return np.array([(math.sin(r), math.cos(r), 0) for r in rads], dtype=float)


@pytest.fixture
def p0(points):
    points.setflags(write=False)
    return points


def test_p_not_writable(p0):
    with pytest.raises(ValueError):
        p0[0] = 1


def test_cyclic_diff():
    result = hermite.cyclic_diff(np.arange(10), 0, 1)
    assert np.all(result[:-1] == 1) and result[-1] == -9


def test_hermite_basic_shapes(p0):
    tangents = hermite.base_tangents(p0)
    assert tangents.shape == p0.shape

    lengths = hermite.base_lengths(p0)
    assert lengths.shape == (p0.shape[0],)

    p1, m0, m1 = hermite.m(p0, tangents, lengths)
    assert p1.shape == p0.shape
    assert m0.shape == p0.shape
    assert m1.shape == p0.shape

    a, b = hermite.coeffs(p0, p1, m0, m1)
    assert a.shape == p0.shape
    assert b.shape == p0.shape

    steps = 9
    p, dp, ddp = hermite.eval(p0, m0, a, b, lengths, steps=steps)
    assert p.shape == (p0.shape[0], steps, p0.shape[1])
    assert dp.shape == (p0.shape[0], steps, p0.shape[1])
    assert ddp.shape == (p0.shape[0], steps, p0.shape[1])

    curvature = hermite.curvature(dp, ddp)
    assert curvature.shape == (p0.shape[0], steps)

    distances = hermite.estimate_distances(p)
    assert distances.shape == (p0.shape[0], steps)

    e_lengths = hermite.estimate_lengths(p)
    assert e_lengths.shape == lengths.shape


def test_hermite_construct_shapes(p0):
    m0, a, b, tangents, lengths = hermite.construct(p0)
    assert m0.shape == p0.shape
    assert b.shape == p0.shape
    assert b.shape == p0.shape
    assert lengths.shape == (p0.shape[0],)

    opt_m0, opt_a, opt_b, opt_tangents, opt_lengths = hermite.optimize(p0, tangents, lengths)
    assert opt_m0.shape == p0.shape
    assert opt_b.shape == p0.shape
    assert opt_b.shape == p0.shape
    assert opt_lengths.shape == lengths.shape
