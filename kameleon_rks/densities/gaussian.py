from scipy.linalg.basic import solve_triangular
import scipy.stats as stats
from kameleon_rks.densities.linalg import pdinv, diag_dot
import numpy as np

def log_gaussian_pdf_multiple(X, mu=None, Sigma=None, is_cholesky=False, compute_grad=False, cov_scaling=1.):
    D = X.shape[1]
    
    if mu is None:
        mu = np.zeros(D)
        
    assert len(mu) == D

    if Sigma is not None:
        assert D == Sigma.shape[0]
        assert D == Sigma.shape[1]
    
        if is_cholesky is False:
            L = np.linalg.cholesky(Sigma)
        else:
            L = Sigma
        
        # solve Y=K^(-1)(X-mu) = L^(-T)L^(-1)(X-mu)
        X = np.array(X - mu)
        
        Y = solve_triangular(L, X.T, lower=True)
        Y = solve_triangular(L.T, Y, lower=False) / cov_scaling
        Y = Y.T
        cov_L_diag = np.diag(L)
    else:
        # assume isotropic covariance, solve y=K^(-1)x
        Y = np.array(X - mu) / cov_scaling
        
        cov_L_diag = np.ones(D)
        
    if not compute_grad:
        log_determinant_part = -np.sum(np.log(np.sqrt(cov_scaling) * cov_L_diag))
        quadratic_part = -0.5 * np.sum(X * Y, axis=1)
        const_part = -0.5 * D * np.log(2 * np.pi)
        
        return const_part + log_determinant_part + quadratic_part
    else:
        return -Y

def log_gaussian_pdf(x, mu=None, Sigma=None, is_cholesky=False, compute_grad=False, cov_scaling=1.):
    D = len(x)
    
    if mu is None:
        mu = np.zeros(D)
        
    assert len(mu) == D

    if Sigma is not None:
        assert D == Sigma.shape[0]
        assert D == Sigma.shape[1]
    
        if is_cholesky is False:
            L = np.linalg.cholesky(Sigma)
        else:
            L = Sigma
        
        # solve y=K^(-1)x = L^(-T)L^(-1)x
        x = np.array(x - mu)
        y = solve_triangular(L, x.T, lower=True)
        y = solve_triangular(L.T, y, lower=False) / cov_scaling
        cov_L_diag = np.diag(L)
    else:
        # assume isotropic covariance, solve y=K^(-1)x
        y = np.array(x - mu) / cov_scaling
        cov_L_diag = np.ones(D)
        
    if not compute_grad:
        log_determinant_part = -np.sum(np.log(np.sqrt(cov_scaling) * cov_L_diag))
        quadratic_part = -0.5 * x.dot(y)
        const_part = -0.5 * D * np.log(2 * np.pi)
        
        return const_part + log_determinant_part + quadratic_part
    else:
        return -y

def sample_gaussian(N, mu, Sigma=None, is_cholesky=False, cov_scaling=1.):
    D = len(mu)
    assert len(mu.shape) == 1

    if Sigma is not None:
        assert len(Sigma.shape) == 2
        assert D == Sigma.shape[0]
        assert D == Sigma.shape[1]
    
        if is_cholesky is False:
            L = np.linalg.cholesky(Sigma)
        else:
            L = Sigma
    
        return np.sqrt(cov_scaling) * (L.dot(np.random.randn(D, N)).T) + mu
    else:
        # assume isotropic covariance
        return np.sqrt(cov_scaling) * np.random.randn(N, D) + mu

class mvnorm(object):
    def __init__(self, mu, K, Ki=None, logdet_K=None, L=None): 
        mu = np.atleast_1d(mu).flatten()
        K = np.atleast_2d(K) 
        assert(np.prod(mu.shape) == K.shape[0])
        assert(K.shape[0] == K.shape[1])
        
        self.mu = mu
        self.K = K
        self.dim = K.shape[0]
        # (self.Ki, self.logdet) = (np.linalg.inv(K), np.linalg.slogdet(K)[1])
        (self.Ki, self.L, self.Li, self.logdet) = pdinv(K)
        
        self.lpdf_const = -0.5 * np.float(self.dim * np.log(2 * np.pi)
                                           + self.logdet)
#    def get_theano_logp(self, X):
#        import theano.tensor as T
#        T.matrix("log")
#        d = x - np.atleast_2d(self.mu).T
#        return (self.lpdf_const - 0.5 *d.dot(Ki.dot(d))).T
        
                                       
    def set_mu(self, mu):
        self.mu = np.atleast_1d(mu).flatten()
        
    def ppf(self, component_cum_prob):
        assert(component_cum_prob.shape[1] == self.dim)
        # this is a pointwise ppf
        std_norm = stats.norm(0, 1)
        rval = []
        for r in range(component_cum_prob.shape[0]):
            rval.append(self.mu + self.L.dot(std_norm.ppf(component_cum_prob[r, :])))
        return np.array(rval)
    
    def logpdf(self, x, theano_expr=False):
        if not theano_expr:
            return self.log_pdf_and_grad(x, pdf=True, grad=False)
        else:
            import theano.tensor as T
            return self.log_pdf_and_grad(x, pdf=True, grad=False, T=T)
    
    def logpdf_grad(self, x):
        return self.log_pdf_and_grad(x, pdf=False, grad=True)
    
    def log_pdf_and_grad(self, x, pdf=True, grad=True, T=np):
        assert(pdf or grad)
        
        if T == np:
            x = np.atleast_2d(x)
            if x.shape[1] != self.mu.size:
                x = x.T
            assert(np.sum(np.array(x.shape) == self.mu.size) >= 1)
        
        d = (x - self.mu.reshape((1 , self.mu.size))).T

        Ki_d = T.dot(self.Ki, d)  # vector
        
        if pdf:
            # vector times vector
            res_pdf = (self.lpdf_const - 0.5 * diag_dot(d.T, Ki_d)).T
            if res_pdf.size == 1:
                res_pdf = T.float(res_pdf)
            if not grad:
                return res_pdf
        if grad:
            # nothing
            res_grad = -Ki_d.T  # .flat[:]
            if res_grad.shape[0] <= 1:
                res_grad = res_grad.flatten()
            if not pdf:
                return res_grad
        return (res_pdf, res_grad)    
    
    def rvs(self, n=1):
        rval = self.ppf(stats.uniform.rvs(size=(n, self.dim)))
        if n == 1:
            return rval.flatten()
        else:
            return rval
    
    @classmethod
    def fit(cls, samples, return_instance=False):  # observations expected in rows
        mu = samples.mean(0)
        var = np.atleast_2d(np.cov(samples, rowvar=0))
        if return_instance:
            return mvnorm(mu, var)
        else:
            return (mu, var)
