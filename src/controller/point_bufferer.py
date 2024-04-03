from model.buffer_point import BufferPoint

class PointBufferer:
    def __init__(self,):
        self.point_buffer = BufferPoint()

    def buffer(self, latitude, longitude, distance):
        return self.point_buffer.buffer(latitude, longitude, distance)