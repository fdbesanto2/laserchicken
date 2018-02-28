"""Calculate echo ratio.

See https://github.com/eEcoLiDAR/eEcoLiDAR/issues/21
"""

import numpy as np

from laserchicken.feature_extractor.abc import AbstractFeatureExtractor
from laserchicken.keys import point


class EchoRatioFeatureExtractor(AbstractFeatureExtractor):
    """Feature extractor for the point density."""

    @classmethod
    def requires(cls):
        """
        Get a list of names of the point attributes that are needed for this feature extraction.

        For simple features, this could be just x, y, and z. Other features can build on again
        other features to have been computed first.

        :return: List of feature names
        """
        return []

    @classmethod
    def provides(cls):
        """
        Get a list of names of the feature values.

        This will return as many names as the number feature values that will be returned.
        For instance, if a feature extractor returns the first 3 Eigen values, this method
        should return 3 names, for instance 'eigen_value_1', 'eigen_value_2' and 'eigen_value_3'.

        :return: List of feature names
        """
        return ['echo_ratio']

    def extract(self, point_cloud, neighborhood, target_point_cloud, target_index, volume_description):
        """
        Extract the feature value(s) of the point cloud at location of the target.

        :param point_cloud: environment (search space) point cloud
        :param neighborhood: array of indices of points within the point_cloud argument
        :param target_point_cloud: point cloud that contains target point
        :param target_index: index of the target point in the target point cloud
        :param volume_description: volume object that describes the shape and size of the search volume
        :return: feature value
        """
        if volume_description.TYPE != 'infinite cylinder':
            raise ValueError('The volume must be a cylinder')

        if target_point_cloud is None:
            raise ValueError('Target point cloud required')

        if target_index is None:
            raise ValueError('Target point index required')

        xyz = self.get_neighborhood_positions(point_cloud, neighborhood)
        n_cylinder = xyz.shape[0]

        xyz0 = self.get_target_position(target_point_cloud, target_index)

        n_sphere = np.sum(np.sum((xyz - xyz0) ** 2, 1) <= volume_description.radius ** 2)
        return n_sphere / n_cylinder * 100.

    @staticmethod
    def get_target_position(target_point_cloud, target_index):
        x0 = target_point_cloud[point]['x']['data'][target_index]
        y0 = target_point_cloud[point]['y']['data'][target_index]
        z0 = target_point_cloud[point]['z']['data'][target_index]
        return np.array([x0, y0, z0])

    @staticmethod
    def get_neighborhood_positions(point_cloud, neighborhood):
        x = point_cloud[point]['x']['data'][neighborhood]
        y = point_cloud[point]['y']['data'][neighborhood]
        z = point_cloud[point]['z']['data'][neighborhood]
        return np.column_stack((x, y, z))

    def get_params(self):
        """
        Return a tuple of parameters involved in the current feature extractorobject.

        Needed for provenance.
        """
        return ()
