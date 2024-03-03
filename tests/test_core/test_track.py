import pytest
import numpy as np

from editor.core.track import Track, TrackException


@pytest.fixture(params=['default', 'reserialized'])
def track(request):
    t = Track()
    if request.param == 'reserialized':
        s = t.serialize()
        t.deserialize(s)
    return Track()


@pytest.fixture
def track_selected(track):
    track.select([0, 1, 2, 3])
    return track


def test_edit_no_selection(track):
    with pytest.raises(TrackException):
        track.subdivide()
    with pytest.raises(TrackException):
        track.dissolve()
    with pytest.raises(TrackException):
        track.add_before()
    with pytest.raises(TrackException):
        track.add_after()
    with pytest.raises(TrackException):
        track.delete()
    with pytest.raises(TrackException):
        track._subdivide([])
    with pytest.raises(TrackException):
        track._delete([])


def test_delete(track_selected):
    track_selected.delete()
    assert track_selected.P.shape[0] == 6


def test_add_before(track_selected):
    track_selected.add_before()
    assert track_selected.P.shape[0] == 14


def test_add_after(track_selected):
    track_selected.add_after()
    assert track_selected.P.shape[0] == 14


def test_subdivide(track_selected):
    track_selected.subdivide()
    assert track_selected.P.shape[0] == 13


def test_dissolve(track_selected):
    track_selected.dissolve()
    assert track_selected.P.shape[0] == 8


def test_min_points(track):
    track.select(None) # None means select everything
    with pytest.raises(TrackException):
        track.delete()


def test_undo(track_selected):
    track_selected.dissolve()
    assert track_selected.P.shape[0] == 8
    track_selected.undo()
    assert track_selected.P.shape[0] == 10


def test_styles(track):
    track.S[0] = 1
    track.select([0])
    track.add_after()
    assert track.S[1] == 1


def test_total_length(track):
    assert abs(track.total_length - track._len.sum()) < 0.01
    assert abs(track.total_length - 1000) < 0.5


def test_write(track):
    track.P[0] = 0
    assert np.all(track.P[0] == 0)

