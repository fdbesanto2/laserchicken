import os
import unittest
import random

import pytest
import numpy as np

from laserchicken import keys, read_las, utils
from laserchicken.compute_neighbors import compute_neighborhoods
from laserchicken.volume_specification import Sphere, InfiniteCylinder

from laserchicken.feature_extractor.echo_ratio_feature_extractor import EchoRatioFeatureExtractor


class TestEchoRatioFeatureExtractorArtificialData(unittest.TestCase):
    """Test echo ratio extractor on artificial spherical and cylindric data."""

    point_cloud = None
    target_point_cloud = None

    def test_valid(self):
        """Must pass as we provide everything needed."""

        extractor = EchoRatioFeatureExtractor()
        per = extractor.extract(self.point_cloud, self.index_cyl, self.target_point_cloud, self.indexpc, self.cyl)
        self.assertTrue(np.allclose(per, self.theo_val))

    def test_invalid(self):
        """ Must raise TypeError as we do not provide correct indexes."""

        extractor = EchoRatioFeatureExtractor()
        # target point cloud must not be None
        with pytest.raises(ValueError):
            extractor.extract(self.point_cloud, self.index_cyl, None, self.indexpc, self.cyl)

        # target index must not be None
        with pytest.raises(ValueError):
            extractor.extract(self.point_cloud, self.index_cyl, self.target_point_cloud, None, self.cyl)

        # volume must be a cylinder
        with pytest.raises(ValueError):
            sphere = Sphere(self.radius)
            extractor.extract(self.point_cloud, self.index_cyl, self.target_point_cloud, self.indexpc, sphere)

    @staticmethod
    def _get_pc(xyz):
        return {keys.point: {'x': {'type': 'double', 'data': xyz[:, 0]},
                             'y': {'type': 'double', 'data': xyz[:, 1]},
                             'z': {'type': 'double', 'data': xyz[:, 2]}}}, len(xyz)

    def _set_sphere_data(self):
        """Create a sphere of point."""
        n_theta, n_phi = 11, 11
        self.npt_sphere = n_theta * n_phi
        theta = np.linspace(0.1, 2 * np.pi, n_theta)
        phi = np.linspace(0.1, np.pi, n_phi)
        r = self.radius
        for t in theta:
            for p in phi:
                x = r * np.cos(t) * np.sin(p)
                y = r * np.sin(t) * np.sin(p)
                z = r * np.cos(p)
                self.xyz.append([x, y, z])

    def _set_cylinder_data(self):
        """Create a cylinder of point."""
        # n_height must be even so that the cylinder has no point
        # on the equator of the sphere
        n_theta, n_height = 11, 10
        self.npt_cyl = n_theta * n_height
        r = self.radius
        theta = np.linspace(0.1, 2 * np.pi, n_theta)
        height = np.linspace(-2 * r, 2 * r, n_height)

        for h in height:
            for t in theta:
                x, y, z = r * np.cos(t), r * np.sin(t), h
                self.xyz.append([x, y, z])

    def _get_central_point(self, index):
        """Get the central point."""
        return utils.copy_pointcloud(self.point_cloud, [index])

    def setUp(self):
        """
        Set up the test.

        Create a sphere and a cylinder of points and a central point
        The cylinder has no points on the equator of the sphere
        """

        # create the points
        self.radius = 0.5
        self.xyz = [[0., 0., 0.]]
        self._set_sphere_data()
        self._set_cylinder_data()

        # create the pc
        self.point_cloud, self.npts = self._get_pc(np.array(self.xyz))
        self.target_point_cloud = self._get_central_point(0)
        self.indexpc = 0

        # create the volume/neighborhood
        self.cyl = InfiniteCylinder(self.radius + 1E-3)
        compute_neighborhoods = compute_neighborhoods(self.point_cloud, self.target_point_cloud, self.cyl)

        self.index_cyl = []
        for x in compute_neighborhoods:
          self.index_cyl += x

        # theoretical value of the echo ratio
        self.theo_val = (self.npt_sphere + 1) / (self.npt_sphere + self.npt_cyl + 1) * 100

    def tearDown(self):
        """Tear it down."""
        pass


class TestEchoRatioFeatureExtractorRealData(unittest.TestCase):
    """Test echo ratio extractor on real data and make sure it doesn't crash."""

    _test_file_name = 'AHN3.las'
    _test_data_source = 'testdata'
    point_cloud = None
    targetpc = None
    cyl = None
    targetpc_index = None

    def test_valid(self):
        """Compute the echo ratio for a sphere/cylinder at different target points."""

        # read the data
        self.point_cloud = read_las.read(os.path.join(self._test_data_source, self._test_file_name))

        # get the target point clouds
        random.seed(102938482634)
        self.targetpc = self._get_random_targets()
        self.targetpc_index = 0

        # volume descriptions
        radius = 0.5
        self.cyl = InfiniteCylinder(radius)
        compute_neighborhoods = compute_neighborhoods(self.point_cloud, self.targetpc, self.cyl)

        cylinder_index = []
        for x in compute_neighborhoods:
          cylinder_index += x

        # extractor
        extractor = EchoRatioFeatureExtractor()
        for index in zip(cylinder_index):
            extractor.extract(self.point_cloud, index, self.targetpc, self.targetpc_index, self.cyl)

    def _get_random_targets(self):
        """Get a random target pc."""
        num_all_pc_points = len(self.point_cloud[keys.point]["x"]["data"])
        rand_indices = [random.randint(0, num_all_pc_points) for p in range(20)]
        return utils.copy_pointcloud(self.point_cloud, rand_indices)


if __name__ == '__main__':
    unittest.main()
