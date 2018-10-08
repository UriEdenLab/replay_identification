"""Calculates the evidence of being in a replay state based on the
current speed and the speed in the previous time step.

"""
from functools import partial

import numpy as np
from patsy import dmatrices
from statsmodels.api import GLM, families
from statsmodels.tsa.tsatools import lagmat

FAMILY = families.Gaussian(link=families.links.log)
FORMULA = 'speed ~ lagged_speed - 1'


def speed_likelihood_ratio(speed, lagged_speed, replay_coefficients,
                           replay_scale, no_replay_coefficients,
                           no_replay_scale, speed_threshold=4.0):
    """Calculates the evidence of being in a replay state based on the
    current speed and the speed in the previous time step.

    Parameters
    ----------
    speed : ndarray, shape (n_time,)
    lagged_speed : ndarray, shape (n_time,)
    replay_speed_std : float
    no_replay_speed_std : float
    speed_threshold : float, optional

    Returns
    -------
    speed_likelihood_ratio : ndarray, shape (n_time, 1)

    """
    no_replay_prediction = _predict(no_replay_coefficients, lagged_speed)
    replay_prediction = _predict(replay_coefficients, lagged_speed)

    replay_log_likelihood = FAMILY.loglike_obs(
        speed, replay_prediction, scale=replay_scale)
    no_replay_log_likelihood = FAMILY.loglike_obs(
        speed, no_replay_prediction, scale=no_replay_scale)
    log_likelihood_ratio = replay_log_likelihood - no_replay_log_likelihood

    likelihood_ratio = np.exp(log_likelihood_ratio)
    likelihood_ratio[np.isposinf(likelihood_ratio)] = 1.0

    return likelihood_ratio[:, np.newaxis]


def fit_speed_likelihood_ratio(speed, is_replay, speed_threshold=4.0):
    """Fits the standard deviation of the change in speed for the replay and
    non-replay state.

    Parameters
    ----------
    speed : ndarray, shape (n_time,)
    is_replay : ndarray, shape (n_time,)
    speed_threshold : float, optional

    Returns
    -------
    speed_likelihood_ratio : function

    """
    lagged_speed = lagmat(speed, 1)
    replay_coefficients, replay_scale = fit_speed_model(
        speed[is_replay], lagged_speed[is_replay])
    no_replay_coefficients, no_replay_scale = fit_speed_model(
        speed[~is_replay], lagged_speed[~is_replay])
    return partial(speed_likelihood_ratio,
                   replay_coefficients=replay_coefficients,
                   replay_scale=replay_scale,
                   no_replay_coefficients=no_replay_coefficients,
                   no_replay_scale=no_replay_scale,
                   speed_threshold=speed_threshold)


def fit_speed_model(speed, lagged_speed):
    response, design_matrix = dmatrices(
        FORMULA, dict(speed=speed, lagged_speed=lagged_speed))
    results = GLM(response, design_matrix, family=FAMILY).fit()
    return results.params, results.scale


def _predict(coefficients, lagged_speed):
    return FAMILY.link.inverse(lagged_speed * coefficients)
