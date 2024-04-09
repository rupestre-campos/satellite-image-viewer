import os
import cv2
import numpy as np

from cv2 import dnn_superres

parent_dir = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(parent_dir, "data/EDSR_x4.pb")

class BoostResolution:
    def __init__(self):
        self.sr = self.__read_model()

    @staticmethod
    def __read_model():
        sr = dnn_superres.DnnSuperResImpl_create()
        sr.readModel(model_path)
        sr.setModel('edsr', 4)
        return sr

    @staticmethod
    def __resize_mask(mask, new_size_x, new_size_y):
        return cv2.resize(mask, (new_size_x, new_size_y))

    @staticmethod
    def __stack_image_mask(image, mask):
        return np.dstack((image, mask))

    def boost_image_resolution(self, input_image):
        mask = input_image[:,:,-1]
        input_image = input_image[:,:,:3]
        input_image = self.sr.upsample(input_image)
        resized_mask = self.__resize_mask(
            mask,
            input_image.shape[1],
            input_image.shape[0]
        )

        return self.__stack_image_mask(input_image, resized_mask)
