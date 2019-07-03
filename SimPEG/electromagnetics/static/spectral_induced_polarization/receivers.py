import numpy as np
import properties

from ....survey import BaseTimeRx, RxLocationArray


class BaseRx(BaseTimeRx):

    orientation = properties.StringChoice(
        "orientation of the receiver. Must currently be 'x', 'y', 'z'",
        ["x", "y", "z"]
    )

    projField = properties.StringChoice(
        "field to be projected in the calculation of the data",
        choices=['phi', 'e', 'j'], default='phi'
    )

    def __init__(self, locations=None, times=None, **kwargs):
        super(BaseRx, self).__init__(locations, times, **kwargs)

    # @property
    # def projField(self):
    #     """Field Type projection (e.g. e b ...)"""
    #     return self.knownRxTypes[self.rxType][0]

    def projGLoc(self, f):
        """Grid Location projection (e.g. Ex Fy ...)"""
        if self.orientation is not None:
            return f._GLoc(self.projField) + self.orientation
        return f._GLoc(self.projField)

    def getTimeP(self, timesall):
        """
            Returns the time projection matrix.

            .. note::

                This is not stored in memory, but is created on demand.
        """
        time_inds = np.in1d(timesall, self.times)
        return time_inds

    def evalDeriv(self, src, mesh, f, v, adjoint=False):
        P = self.getP(mesh, self.projGLoc(f))
        if not adjoint:
            return P*v
        elif adjoint:
            return P.T*v


class Dipole(BaseRx):
    """
    Dipole receiver
    """

    locations = properties.List(
        "list of locations of each electrode in a dipole receiver",
        RxLocationArray("location of electrode", shape=("*", "*")),
        min_length=1, max_length=2
    )

    def __init__(self, locationsM, locationsN, times, **kwargs):
        if locationsM.shape != locationsN.shape:
            raise ValueError(
                'locationsM and locationsN need to be the same size')
        locations = [np.atleast_2d(locationsM), np.atleast_2d(locationsN)]
        super(Dipole, self).__init__(times=times, **kwargs)
        self.locations = locations

    @property
    def nD(self):
        """Number of data in the receiver."""
        return self.locations[0].shape[0]

    @property
    def nRx(self):
        """Number of data in the receiver."""
        # return self.locations[0].shape[0]
        raise Exception("nRx has depreciated. please use rx.nD instead")

    def getP(self, mesh, Gloc):
        if mesh in self._Ps:
            return self._Ps[mesh]

        P0 = mesh.getInterpolationMat(self.locations[0], Gloc)
        P1 = mesh.getInterpolationMat(self.locations[1], Gloc)
        P = P0 - P1

        if self.storeProjections:
            self._Ps[mesh] = P

        return P


class Pole(BaseRx):
    """
    Pole receiver
    """

    def __init__(self, locations, times, **kwargs):
        super(Pole, self).__init__(locations, times, **kwargs)

    @property
    def nD(self):
        """Number of data in the receiver."""
        return self.locations.shape[0]

    @property
    def nRx(self):
        """Number of data in the receiver."""
        raise Exception("nRx has depreciated. please use rx.nD instead")

    def getP(self, mesh, Gloc):
        if mesh in self._Ps:
            return self._Ps[mesh]

        P = mesh.getInterpolationMat(self.locations, Gloc)

        if self.storeProjections:
            self._Ps[mesh] = P

        return P
