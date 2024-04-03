from model.buffer_point import BufferPoint

def test_point_to_buffer():
    latitude = 20
    longitude = 23

    buffer_distance = 100
    point_buffer = BufferPoint()
    buffer_geometry = point_buffer.buffer(latitude, longitude, buffer_distance)
    assert isinstance(buffer_geometry, dict)
