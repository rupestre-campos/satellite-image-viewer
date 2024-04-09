from model.boost_resolution import BoostResolution

class ResolutionBooster:
    def __init__(self):
        self.resolution_boost = BoostResolution()

    def image_resolution_booster(self, image):
        return self.resolution_boost.boost_image_resolution(image)