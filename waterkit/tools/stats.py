import numpy as np
import pandas as pd

class OLSRegressionModel(object):
    """Calcluates the least squares regression of a dataset.

    We don't use pandas.ols for this because it carries an extra dependency
    to scikits.statsmodels, which has been unreliable when building on different
    platforms or against different versions of Numpy.
    """

    def __init__(self, y, x=None):
        """
        Parameters
        ----------
        y : Series
            A Series with the ordinate.
        x : Series, optional
            A series with the abcissa. If this is not provided, the series index
            for the y values will be used.
        """
        self._xs = np.array(x if x is not None else y.index)
        self._ys = np.array(y)
        # Linear regression is the least squares minimization of the overdetermined
        # system (a, 1)x = y
        A = np.array([self._xs, np.ones(len(self._xs))])
        model, residuals, rank, s = np.linalg.lstsq(A.T, self._ys)
        self._model = model
        self._residuals = residuals
        self._rank = rank
        self._singular_values = s

    @property
    def model(self):
        return self._model

    def predict(self, x=None):
        """Use the regression model to predict the values of a series.

        Parameters
        ----------
        x : Series or Series Index
            The model input values. If this is not provided, then the
            x values that were used to build the model are used.

        Returns
        -------
        Series of predicted values.
        """
        if x is None:
            x_input = self._xs
        else:
            x_input = np.array(x)
        return pd.Series(
            self._model[0] * x_input + self._model[1],
            index = x_input
        )

    def __str__(self):
        return "%s, %s, %s, %s" % (
            self._model,
            self._residuals,
            self._rank,
            self._singular_values)
