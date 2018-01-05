import numpy as np
from functools import wraps


def scaled_likelihood(log_likelihood_func):
    '''Converts a log likelihood to a scaled likelihood with its max value at
    1.

    Used primarily to keep the likelihood numerically stable because more
    observations at a time point will lead to a smaller overall likelihood
    and this can exceed the floating point accuarcy of a machine.

    Parameters
    ----------
    log_likelihood_func : function

    Returns
    -------
    scaled_likelihood : function

    '''
    @wraps(log_likelihood_func)
    def decorated_function(*args, **kwargs):
        log_likelihood = log_likelihood_func(*args, **kwargs)
        return np.exp(log_likelihood - np.max(log_likelihood))

    return decorated_function


def combined_likelihood(log_likelihood_function):
    @wraps(log_likelihood_function)
    def decorated_function(*args, **kwargs):
        try:
            return np.sum(log_likelihood_function(*args, **kwargs),
                          axis=0)
        except ValueError:
            return log_likelihood_function(*args, **kwargs).squeeze()
    return decorated_function
