import numpy as np

from laserchicken import utils
from laserchicken.feature_extractor.abc import AbstractFeatureExtractor
from laserchicken.utils import get_xyz


class EigenValueVectorizeFeatureExtractor(AbstractFeatureExtractor):
    is_vectorized = True

    @classmethod
    def requires(cls):
        return []

    @classmethod
    def provides(cls):
        return ['eigenv_1', 'eigenv_2', 'eigenv_3', 'normal_vector_1', 'normal_vector_2', 'normal_vector_3', 'slope']

    @staticmethod
    def _get_cov(xyz):
        n_max = xyz.shape[2]
        n = (xyz.mask.sum(axis=2, keepdims=True) * -1) + n_max
        m = xyz - xyz.sum(2, keepdims=True) / n
        return np.einsum('ijk,ilk->ijl', m, m) / (n - 1)

    def extract(self, sourcepc, neighborhood, targetpc, targetindex, volume):
        if not isinstance(neighborhood[0], list):
            neighborhood = [neighborhood]

        xyz_grp = get_xyz(sourcepc, neighborhood)
        cov_mat = self._get_cov(xyz_grp)

        eigval, eigvects = np.linalg.eig(cov_mat)

        e = np.sort(eigval, axis=1)[:, ::-1]  # Sorting to make result identical to serial implementation.

        normals = eigvects[:, :, 2]
        slope = np.dot(normals, np.array([0., 0., 1.]))
        return e[:, 0], e[:, 1], e[:, 2], normals[:, 0], normals[:, 1], normals[:, 2], slope
