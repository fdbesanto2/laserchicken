import os
import random
import time
import unittest

import numpy as np

from laserchicken import compute_neighbors, feature_extractor, keys, read_las, utils
from laserchicken.feature_extractor.abc import AbstractFeatureExtractor
from laserchicken.test_tools import create_point_cloud
from laserchicken.utils import copy_point_cloud
from laserchicken.volume_specification import InfiniteCylinder
from .eigenvals_feature_extractor import EigenValueVectorizeFeatureExtractor


class TestExtractEigenValues(unittest.TestCase):
    def test_eigenvalues_in_cylinders(self):
        """Test provenance added (This should actually be part the general feature extractor test suite)."""
        random.seed(102938482634)
        point_cloud = read_las.read(
            os.path.join('testdata', 'AHN3.las'))
        num_all_pc_points = len(point_cloud[keys.point]["x"]["data"])
        rand_indices = [random.randint(0, num_all_pc_points)
                        for _ in range(20)]
        target_point_cloud = utils.copy_point_cloud(point_cloud, rand_indices)
        n_targets = len(target_point_cloud[keys.point]["x"]["data"])
        radius = 2.5
        neighbors = compute_neighbors.compute_cylinder_neighborhood(
            point_cloud, target_point_cloud, radius)

        target_idx_base = 0
        for x in neighbors:
            feature_extractor.compute_features(point_cloud, x, target_idx_base, target_point_cloud,
                                               ["eigenv_1", "eigenv_2", "eigenv_3"], InfiniteCylinder(5))
            target_idx_base += len(x)

        self.assertEqual("laserchicken.feature_extractor.eigenvals_feature_extractor",
                         target_point_cloud[keys.provenance][0]["module"])

    @staticmethod
    def test_eigenvalues_of_too_few_points_results_in_0():
        """If there are too few points to calculate the eigen values don't output NaN or inf."""
        a = np.array([5])
        pc = create_point_cloud(a, a, a)

        feature_extractor.compute_features(
            pc, [[0]], 0, pc, ["eigenv_1", "eigenv_2", "eigenv_3"], InfiniteCylinder(5))

        eigen_val_123 = np.array(
            [pc[keys.point]['eigenv_{}'.format(i)]['data'] for i in [1, 2, 3]])
        assert not np.any(np.isnan(eigen_val_123))
        assert not np.any(np.isinf(eigen_val_123))


class TestExtractEigenvaluesComparison(unittest.TestCase):
    point_cloud = None

    def test_eigen_multiple_neighborhoods(self):
        """
        Test and compare the serial and vectorized eigenvalues.

        Eigenvalues are computed for a list of neighborhoods in real data. A vectorized implementation and a serial
        implementation are compared and timed. Any difference in result between the two methods is definitely
        unexpected (except maybe in ordering of eigen values).
        """
        # vectorized version
        t0 = time.time()
        extract_vect = EigenValueVectorizeFeatureExtractor()
        eigvals_vect = extract_vect.extract(self.point_cloud, self.neigh, None, None, None)
        print('Timing Vectorize : {}'.format((time.time() - t0)))
        eigvals_vect = np.vstack(eigvals_vect[:3]).T

        # serial version
        eigvals = []
        t0 = time.time()
        for n in self.neigh:
            extract = EigenValueSerial()
            eigvals.append(extract.extract(self.point_cloud, n, None, None, None))
        print('Timing Serial : {}'.format((time.time() - t0)))
        eigvals = np.array(eigvals)

        np.testing.assert_allclose(eigvals_vect, eigvals)

    def setUp(self):
        """
        Set up the test.

        Load in a bunch of real data from AHN3.
        """
        np.random.seed(1234)

        _TEST_FILE_NAME = 'AHN3.las'
        _TEST_DATA_SOURCE = 'testdata'

        _CYLINDER = InfiniteCylinder(4)
        _PC_260807 = read_las.read(os.path.join(_TEST_DATA_SOURCE, _TEST_FILE_NAME))
        _PC_1000 = copy_point_cloud(_PC_260807, array_mask=(
            np.random.choice(range(len(_PC_260807[keys.point]['x']['data'])), size=1000, replace=False)))
        _1000_NEIGHBORHOODS_IN_260807 = next(compute_neighbors.compute_neighborhoods(_PC_260807, _PC_1000, _CYLINDER))

        self.point_cloud = _PC_260807
        self.neigh = _1000_NEIGHBORHOODS_IN_260807


class TestExtractNormalPlaneArtificialData(unittest.TestCase):
    def test_from_eigen(self):
        extractor = EigenValueVectorizeFeatureExtractor()
        n1, n2, n3, slope_fit = extractor.extract(
            self.pc, self.neighborhood, None, None, None)[3:]
        np.testing.assert_allclose(self.nvect[0], n1[0])
        np.testing.assert_allclose(self.nvect[1], n2[0])
        np.testing.assert_allclose(self.nvect[2], n3[0])
        np.testing.assert_allclose(slope_fit, self.slope)

    def setUp(self):
        """Generate some points in a plane."""
        self.zaxis = np.array([0., 0., 1.])
        self.nvect = np.array([1., 2., 3.])
        self.nvect /= np.linalg.norm(self.nvect)
        self.slope = np.dot(self.nvect, self.zaxis)
        point = _generate_random_points_in_plane(self.nvect, dparam=0, npts=100)
        self.pc = {keys.point: {'x': {'type': 'double', 'data': point[:, 0]},
                                'y': {'type': 'double', 'data': point[:, 1]},
                                'z': {'type': 'double', 'data': point[:, 2]}}}
        self.neighborhood = [[3, 4, 5, 6, 7], [1, 2, 7, 8, 9], [1, 2, 7, 8, 9], [1, 2, 7, 8, 9], [1, 2, 7, 8, 9]]


def _generate_random_points_in_plane(nvect, dparam, npts, eps=0.0):
    """
    Generate a series of point all belonging to a plane.

    :param nvect: normal vector of the plane
    :param dparam: zero point value of the plane
    :param npts: number of points
    :param eps: std of the gaussian noise added to the z values of the planes
    :return: x,y,z coordinate of the points
    """
    np.random.seed(12345)
    a, b, c = nvect / np.linalg.norm(nvect)
    x, y = np.random.rand(npts), np.random.rand(npts)
    z = (dparam - a * x - b * y) / c
    if eps > 0:
        z += np.random.normal(loc=0., scale=eps, size=npts)
    return np.column_stack((x, y, z))


class EigenValueSerial(AbstractFeatureExtractor):
    """Old serial implementation. Used to test the current (vectorized) implementation against."""

    @classmethod
    def requires(cls):
        return []

    @classmethod
    def provides(cls):
        return ["eigenv_1", "eigenv_2", "eigenv_3"]

    def extract(self, sourcepc, neighborhood, targetpc, targetindex, volume):
        nbptsX, nbptsY, nbptsZ = utils.get_point(sourcepc, neighborhood)
        matrix = np.column_stack((nbptsX, nbptsY, nbptsZ))

        try:
            eigenvals, eigenvecs = self._structure_tensor(matrix)
        except ValueError as err:
            if str(err) == 'Not enough points to compute eigenvalues/vectors.':
                return [0, 0, 0]
            else:
                raise

        return [eigenvals[0], eigenvals[1], eigenvals[2]]

    @staticmethod
    def _structure_tensor(points):
        """
        Computes the structure tensor of points by computing the eigenvalues
        and eigenvectors of the covariance matrix of a point cloud.
        Parameters
        ----------
        points : (Mx3) array
            X, Y and Z coordinates of points.
        Returns
        -------
        eigenvalues : (1x3) array
            The eigenvalues corresponding to the eigenvectors of the covariance
            matrix.
        eigenvectors : (3,3) array
            The eigenvectors of the covariance matrix.
        """
        if points.shape[0] > 3:
            cov_mat = np.cov(points, rowvar=False)
            eigenvalues, eigenvectors = np.linalg.eig(cov_mat)
            order = np.argsort(-eigenvalues)
            eigenvalues = eigenvalues[order]
            eigenvectors = eigenvectors[:, order]
            return eigenvalues, eigenvectors
        else:
            raise ValueError('Not enough points to compute eigenvalues/vectors.')
