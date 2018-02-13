import scipy.stats.stats as stats

from laserchicken.feature_extractor.abc import AbstractFeatureExtractor
from laserchicken.keys import point


class PercentileFeatureExtractor(AbstractFeatureExtractor):
    """Height percentiles feature extractor class."""

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
        return ['perc_' + str(i) for i in range(10, 110, 10)]

    def extract(self, sourcepc, neighborhood, targetpc, targetindex, volume_description):
        """
        Extract the feature value(s) of the point cloud at location of the target.
        :param point_cloud: environment (search space) point cloud
        :param neighborhood: array of indices of points within the point_cloud argument
        :param target_point_cloud: point cloud that contains target point
        :target_index: index of the target point in the target pointcloud
        :return: feature value
        """
        z = sourcepc[point]['z']['data'][neighborhood]
        percentiles = range(10, 110, 10)
        return [stats.scoreatpercentile(z, p) for p in percentiles]

    def get_params(self):
        """
        Return a tuple of parameters involved in the current feature extractor object.

        Needed for provenance.
        """
        return ()
