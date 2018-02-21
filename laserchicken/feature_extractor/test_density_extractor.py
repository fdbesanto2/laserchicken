import os
import unittest

import random
import numpy as np

from laserchicken import keys, read_las, utils
from laserchicken.compute_neighbors import compute_neighborhoods
from laserchicken.volume_specification import Sphere, InfiniteCylinder
from laserchicken.feature_extractor.density_feature_extractor import PointDensityFeatureExtractor


class TestDensityFeatureExtractorSphere(unittest.TestCase):
    """Test density extractor on artificial spherical data."""

    point_cloud = None

    def test_sphere(self):
        """Compute the density for a sphere given as index of the source pc."""
        neighbors_index = compute_neighborhoods(self.point_cloud,
                                                self.targetpc,
                                                self.sphere)

        extractor = PointDensityFeatureExtractor()
        for index in neighbors_index:
            d = extractor.extract(self.point_cloud, index, None, None, self.sphere)
            self.assertEqual(d, self.voldens)

    def _get_central_point(self):
        """Get the central point."""
        return utils.copy_pointcloud(self.point_cloud, [0])

    def _set_sphere_data(self):
        """Generate a pc of points regularly positionned on a two spheres of radius 1 and 2."""
        nteta, nphi = 11, 11
        self.teta = np.linspace(0.1, 2 * np.pi, nteta)
        self.phi = np.linspace(0.1, np.pi, nphi)
        self.radius = [1., 2.]
        self.points_per_sphere = nteta * nphi
        self.xyz = []
        self.xyz.append([0., 0., 0.])
        for r in self.radius:
            for t in self.teta:
                for p in self.phi:
                    x = r * np.cos(t) * np.sin(p)
                    y = r * np.sin(t) * np.sin(p)
                    z = r * np.cos(p)
                    self.xyz.append([x, y, z])

        self.xyz = np.array(self.xyz)
        self.point_cloud = {keys.point: {'x': {'type': 'double', 'data': self.xyz[:, 0]},
                           'y': {'type': 'double', 'data': self.xyz[:, 1]},
                           'z': {'type': 'double', 'data': self.xyz[:, 2]}}}

    def setUp(self):
        """Set up the test."""
        # get the points
        self._set_sphere_data()

        # get the central point as targetpc
        self.targetpc = self._get_central_point()

        # get the sphere
        self.sphere = Sphere(np.mean(self.radius))

        # get the theoretical value +1 for central point
        npts = self.points_per_sphere + 1
        self.voldens = npts / self.sphere.calculate_volume()

    def tearDown(self):
        pass


class TestDensityFeatureExtractorCylinder(unittest.TestCase):
    """Test density extractor on artificial cylindric data."""

    point_cloud = None

    def test_cylinder(self):
        """Compute the density for a cylinder given as index of source pc."""
        neighbors_index = compute_neighborhoods(self.point_cloud,
                                                self.targetpc,
                                                self.cyl)

        extractor = PointDensityFeatureExtractor()
        for index in neighbors_index:
            d = extractor.extract(self.point_cloud, index, None, None, self.cyl)
            self.assertEqual(d, self.areadens)

    def _get_central_point(self):
        """Get the central point."""
        return utils.copy_pointcloud(self.point_cloud, [0])


    def _set_cylinder_data(self):

        # generate a pc of points regularly
        # positionned on two concentric cylinders
        # plus a central point
        nteta, nheight = 11, 11
        teta = np.linspace(0.01, 2 * np.pi, nteta)
        height = np.linspace(-1, 1, nheight)
        self.radius = [1., 2.]

        self.points_per_cylinder = nteta * nheight
        self.xyz = []
        self.xyz.append([0., 0., 0.])
        for r in self.radius:
            for z in height:
                for t in teta:
                    x = r * np.cos(t)
                    y = r * np.sin(t)
                    self.xyz.append([x, y, z])

        self.xyz = np.array(self.xyz)
        self.point_cloud = {keys.point: {'x': {'type': 'double', 'data': self.xyz[:, 0]},
                           'y': {'type': 'double', 'data': self.xyz[:, 1]},
                           'z': {'type': 'double', 'data': self.xyz[:, 2]}}}

    def setUp(self):
        """Set up the test."""
        # generate the points
        self._set_cylinder_data()

        # get the central point as targetpc
        self.targetpc = self._get_central_point()

        # get the cylinder
        self.cyl = InfiniteCylinder(np.mean(self.radius))

        # get the theoretical value +1 for central point
        npts = self.points_per_cylinder + 1
        self.areadens = npts / self.cyl.calculate_base_area()

    def tearDowm(self):
        pass


class TestDensityFeatureOnRealData(unittest.TestCase):
    """Test density extractor on real data and make sure it doesn't crash."""

    _test_file_name = 'AHN3.las'
    _test_data_source = 'testdata'
    point_cloud = None

    def test_sphere_index(self):
        """Compute the density for a sphere given as index of the source pc."""
        neighbors_index = compute_neighborhoods(self.point_cloud,
                                                self.targetpc,
                                                self.sphere)

        extractor = PointDensityFeatureExtractor()
        for index in neighbors_index:
            extractor.extract(self.point_cloud, index, None, None, self.sphere)


    def test_cylinder_index(self):
        """Compute the density for a cylinder given as index of source pc."""
        neighbors_index = compute_neighborhoods(self.point_cloud,
                                                self.targetpc,
                                                self.cyl)
        extractor = PointDensityFeatureExtractor()
        for index in neighbors_index:
            extractor.extract(self.point_cloud, index, None, None, self.cyl)



    def _get_random_targets(self):
        num_all_pc_points = len(self.point_cloud[keys.point]["x"]["data"])
        rand_indices = [random.randint(0, num_all_pc_points) for p in range(20)]
        return utils.copy_pointcloud(self.point_cloud, rand_indices)

    def setUp(self):
        """Set up the test."""
        self.point_cloud = read_las.read(os.path.join(self._test_data_source, self._test_file_name))

        random.seed(102938482634)
        self.targetpc = self._get_random_targets()

        radius = 0.5
        self.sphere = Sphere(radius)
        self.cyl = InfiniteCylinder(radius)

    def tearDown(self):
        pass


if __name__ == '__main__':
    unittest.main()