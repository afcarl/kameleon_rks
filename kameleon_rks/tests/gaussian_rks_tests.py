from numpy.ma.testutils import assert_close
from numpy.testing.utils import assert_allclose
from sklearn.kernel_approximation import RBFSampler

from kameleon_rks.gaussian_rks import feature_map, feature_map_single, \
    feature_map_derivative_d, feature_map_derivative2_d, \
    feature_map_derivatives_loop, feature_map_derivatives, \
    feature_map_derivatives2_loop, feature_map_derivatives2, \
    feature_map_grad_single
import numpy as np


def test_feature_map_equals_scikit_learn():
    sigma = 2.
    gamma = sigma ** 2
    
    N = 10
    D = 20
    m = 3
    X = np.random.randn(N, D)
    np.random.seed(1)
    omega = sigma * np.random.randn(D, m)
    u = np.random.uniform(0, 2 * np.pi, m)
    
    # make sure basis is the same
    np.random.seed(1)
    rbf_sampler = RBFSampler(gamma, m, random_state=1)
    rbf_sampler.fit(X)
    assert_allclose(rbf_sampler.random_weights_, omega)
    assert_allclose(rbf_sampler.random_offset_, u)
    
    phi_scikit = rbf_sampler.transform(X)
    phi_mine = feature_map(X, omega, u)
    
    assert_allclose(phi_scikit, phi_mine)

def test_feature_map():
    x = 3.
    u = 2.
    omega = 2.
    phi = feature_map_single(x, omega, u)
    phi_manual = np.cos(omega * x + u) * np.sqrt(2.)
    assert_close(phi, phi_manual)

def test_feature_map_single_equals_feature_map():
    N = 10
    D = 20
    m = 3
    X = np.random.randn(N, D)
    omega = np.random.randn(D, m)
    u = np.random.uniform(0, 2 * np.pi, m)
    
    phis = feature_map(X, omega, u)
    
    for i, x in enumerate(X):
        phi = feature_map_single(x, omega, u)
        assert_allclose(phis[i], phi)

def test_feature_map_derivative_d_1n():
    X = np.array([[1.]])
    u = np.array([2.])
    omega = np.array([[2.]])
    d = 0
    phi_derivative = feature_map_derivative_d(X, omega, u, d)
    phi_derivative_manual = -np.sin(X * omega + u) * omega[:, d] * np.sqrt(2.)
    assert_close(phi_derivative, phi_derivative_manual)

def test_feature_map_derivative_d_2n():
    X = np.array([[1.], [3.]])
    u = np.array([2.])
    omega = np.array([[2.]])
    d = 0
    phi_derivative = feature_map_derivative_d(X, omega, u, d)
    phi_derivative_manual = -np.sin(X * omega + u) * omega[:, d] * np.sqrt(2.)
    assert_close(phi_derivative, phi_derivative_manual)

def test_feature_map_derivative2_d():
    X = np.array([[1.]])
    u = np.array([2.])
    omega = np.array([[2.]])
    d = 0
    phi_derivative2 = feature_map_derivative2_d(X, omega, u, d)
    phi_derivative2_manual = -feature_map(X, omega, u) * (omega[:, d] ** 2)
    assert_close(phi_derivative2, phi_derivative2_manual)

def test_feature_map_derivatives_loop_equals_map_derivative_d():
    N = 10
    D = 20
    m = 3
    X = np.random.randn(N, D)
    omega = np.random.randn(D, m)
    u = np.random.uniform(0, 2 * np.pi, m)
    
    derivatives = feature_map_derivatives_loop(X, omega, u)
    
    for d in range(D):
        derivative = feature_map_derivative_d(X, omega, u, d)
        assert_allclose(derivatives[d], derivative)

def test_feature_map_derivatives_equals_feature_map_derivatives_loop():
    N = 10
    D = 20
    m = 3
    X = np.random.randn(N, D)
    omega = np.random.randn(D, m)
    u = np.random.uniform(0, 2 * np.pi, m)
    
    derivatives = feature_map_derivatives(X, omega, u)
    derivatives_loop = feature_map_derivatives_loop(X, omega, u)
    
    assert_allclose(derivatives_loop, derivatives)

def test_feature_map_derivatives2_loop_equals_map_derivative2_d():
    N = 10
    D = 20
    m = 3
    X = np.random.randn(N, D)
    omega = np.random.randn(D, m)
    u = np.random.uniform(0, 2 * np.pi, m)
    
    derivatives = feature_map_derivatives2_loop(X, omega, u)
    
    for d in range(D):
        derivative = feature_map_derivative2_d(X, omega, u, d)
        assert_allclose(derivatives[d], derivative)

def test_feature_map_derivatives2_equals_feature_map_derivatives2_loop():
    N = 10
    D = 20
    m = 3
    X = np.random.randn(N, D)
    omega = np.random.randn(D, m)
    u = np.random.uniform(0, 2 * np.pi, m)
    
    derivatives = feature_map_derivatives2(X, omega, u)
    derivatives_loop = feature_map_derivatives2_loop(X, omega, u)
    
    assert_allclose(derivatives_loop, derivatives)

def test_feature_map_grad_single_equals_feature_map_derivative_d():
    D = 2
    m = 3
    omega = np.random.randn(D, m)
    u = np.random.uniform(0, 2 * np.pi, m)
    x = np.random.randn(D)
    
    grad = feature_map_grad_single(x, omega, u)
    
    grad_manual = np.zeros((D, m))
    for d in range(D):
        grad_manual[d, :] = feature_map_derivative_d(x, omega, u, d)
    
    assert_allclose(grad_manual, grad)
