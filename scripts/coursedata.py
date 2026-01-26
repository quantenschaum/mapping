import re
from math import atan2, cos, degrees, radians, sin, sqrt


class CourseData:
    """
    This class is a container for course data that tries to compute the missing pieces
    from the information that is supplied in the constructor.

    ## Units

    - direction - given in degrees within [0,360), relative to north, measured clockwise
    - angles - as directions, but given in degrees within [-180,+180), relative to HDG
      If you want angles in the range [0,360), set anlges360=True in the constructor.
    - speeds - given in any speed unit (but all the same), usually knots

    ## Definitions

    HDG = heading, unspecified which of the following
    HDT = true heading, direction bow is pointing to, relative to true north (also HDGt)
    HDM = magnetic heading, as reported by a calibrated compass (also HDGm)
    HDC = compass heading, raw reading of the compass (also HDGc)
    VAR = magnetic variation, given in chart or computed from model
    DEV = magnetic deviation, boat specific, depends on HDG
    COG = course over ground, usually from GPS
    SOG = speed over ground, usually from GPS
    SET = set, direction of tide/current, cannot be measured directly
    DFT = drift, rate of tide/current, cannot be measured directly
    STW = speed through water, usually from paddle wheel, water speed vector projected onto HDT (long axis of boat)
    LEE = leeway angle, angle between HDT and direction of water speed vector, usually estimated from wind and/or heel and STW
    AWA = apparent wind angle, measured by wind direction sensor
    AWD = apparent wind direction, relative to true north
    AWS = apparent wind speed, measured by anemometer
    TWA = true wind angle, relative to water, relative to HDT
    TWD = true wind direction, relative to water, relative true north
    TWS = true wind speed, relative to water
    GWA = ground wind angle, relative to ground, relative to HDT
    GWD = ground wind direction, relative to ground, relative true north
    GWS = ground wind speed, relative to ground

    Beware! Wind direction is the direction where the wind is coming FROM, SET,HDG,COG is the direction where the tide/boat is going TO.

    also see https://t1p.de/5th2j and https://t1p.de/628t7

    ## Magnetic Directions

    All directions, except HDM, are relative to true north. This is because a magnetic compass gives you a magnetic
    direction (heading or bearing). You convert it to true using deviation and variation and that's it.

    You could use something like COG magnetic, but it does not make any sense and is error-prone.
    Don't do this! If you do need this for output, then do the conversion to magnetic at the very end,
    after all calculations are done.

    ## Equations

    All of the mentioned quantities are linked together by the following equations. Some of them are
    vector equations, vectors are polar vectors of the form [angle,radius]. The (+) operator denotes the addition of
    polar vectors. see https://math.stackexchange.com/questions/1365622/adding-two-polar-vectors
    An implementation of this addition is given below in add_polar().

    ### Heading

    - HDT = HDM + VAR = HDC + DEV + VAR
    - HDM = HDT - VAR = HDC + DEV

    ### Course, Speed and Tide

    - [COG,SOG] = [HDT+LEE,STW] (+) [SET,DFT]
    - [SET,DFT] = [COG,SOG] (+) [HDT+LEE,-STW]

    ### Wind

    angles and directions are always converted like xWD = xWA + HDT and xWA = xWD - HDT

    - [AWD,AWS] = [GWD,GWS] (+) [COG,SOG]
    - [AWD,AWS] = [TWD,TWS] (+) [HDT+LEE,STW]
    - [AWA,AWS] = [TWA,TWS] (+) [LEE,STW]

    - [TWD,TWS] = [GWD,GWS] (+) [SET,DFT]
    - [TWD,TWS] = [AWD,AWS] (+) [HDT+LEE,-STW]
    - [TWA,TWS] = [AWA,AWS] (+) [LEE,-STW]

    - [GWD,GWS] = [AWD,AWS] (+) [COG,-SOG]

    In the vector equations angle and radius must be transformed together, always!

    ## How to use it

    Create CourseData() with the known quantities supplied in the constructor. Then access the calculated
    quantities as d.TWA or d.["TWA"]. Ask with "TWD" in d if they exist. Just print(d) to see what's inside.
    See test() for examples.
    """

    def __init__(self, **kwargs):
        self._data = kwargs
        self.angles360 = kwargs.get("angles360", False)
        self.compute_missing()

    def compute_missing(self):
        if self.misses("HDM") and self.has("HDC", "DEV"):
            self.HDM = to360(self.HDC + self.DEV)

        if self.misses("HDT") and self.has("HDM", "VAR"):
            self.HDT = to360(self.HDM + self.VAR)

        if self.misses("HDM") and self.has("HDT", "VAR"):
            self.HDM = to360(self.HDT - self.VAR)

        if self.misses("LEE"):
            self.LEE = 0

        if self.misses("SET", "DFT") and self.has("COG", "SOG", "HDT", "STW", "LEE"):
            self.SET, self.DFT = add_polar(
                (self.COG, self.SOG), (self.HDT + self.LEE, -self.STW)
            )
        if self.misses("COG", "SOG") and self.has("SET", "DFT", "HDT", "STW", "LEE"):
            self.COG, self.SOG = add_polar(
                (self.SET, self.DFT), (self.HDT + self.LEE, self.STW)
            )

        if self.misses("TWA", "TWS") and self.has("AWA", "AWS", "STW", "LEE"):
            self.TWA, self.TWS = add_polar((self.AWA, self.AWS), (self.LEE, -self.STW))
            self.TWA = self.angle(self.TWA)

        if self.misses("TWD", "TWS") and self.has("GWD", "GWS", "SET", "DFT"):
            self.TWD, self.TWS = add_polar((self.GWD, self.GWS), (self.SET, self.DFT))

        if self.misses("TWD") and self.has("TWA", "HDT"):
            self.TWD = to360(self.TWA + self.HDT)

        if self.misses("TWA") and self.has("TWD", "HDT"):
            self.TWA = self.angle(self.TWD - self.HDT)

        if self.misses("GWD", "GWS") and self.has("TWD", "TWS", "SET", "DFT"):
            self.GWD, self.GWS = add_polar((self.TWD, self.TWS), (self.SET, -self.DFT))

        if self.misses("GWA") and self.has("GWD", "HDT"):
            self.GWA = self.angle(self.GWD - self.HDT)

        if self.misses("AWA", "AWS") and self.has("TWA", "TWS", "LEE", "STW"):
            self.AWA, self.AWS = add_polar((self.TWA, self.TWS), (self.LEE, self.STW))
            self.AWA = self.angle(self.AWA)

        if self.misses("AWD") and self.has("AWA", "HDT"):
            self.AWD = to360(self.AWA + self.HDT)

    def __getattribute__(self, item):
        if re.match("[A-Z]{3}", item):
            return self._data.get(item)
        return super(CourseData, self).__getattribute__(item)

    def __setattr__(self, key, value):
        if re.match("[A-Z]{3}", key):
            self._data[key] = value
        else:
            self.__dict__[key] = value

    def __getitem__(self, item):
        return self._data.get(item)

    def __setitem__(self, key, value):
        self._data[key] = value

    def __contains__(self, item):
        return self[item] is not None

    def __str__(self):
        return "\n".join(f"{k}={self[k]}" for k in self.keys())

    def keys(self):
        return sorted(filter(self.__contains__, self._data.keys()))

    def has(self, *args):
        return all(x in self for x in args)

    def misses(self, *args):
        return any(x not in self for x in args)

    def angle(self, a):
        return to360(a) if self.angles360 else to180(a)


def test():
    d = CourseData(HDC=1, VAR=-4, DEV=2)
    print(d, "\n")
    assert d.HDT == 1 + 2 - 4 + 360

    d = CourseData(HDT=10, VAR=3)
    print(d, "\n")
    assert d.HDM == 10 - 3

    d = CourseData(HDT=0, STW=0, COG=270, SOG=3)
    print(d, "\n")
    assert d.SET == 270 and d.DFT == 3

    d = CourseData(HDT=90, STW=3, COG=33, SOG=0)
    print(d, "\n")
    assert d.SET == 270 and d.DFT == 3

    d = CourseData(HDT=30, STW=5, COG=20, SOG=6)
    print(d, "\n")
    assert abs(d.SET - 341.09) < 1e-2 and abs(d.DFT - 1.38) < 1e-2

    # simulate data from known values
    d = CourseData(GWD=330, GWS=15, SET=10, DFT=3, HDT=20, VAR=-4, STW=5, LEE=-6)
    print(d, "\n")

    # retrieve data from measured values
    e = CourseData(
        AWA=d.AWA,
        AWS=d.AWS,
        STW=d.STW,
        HDM=d.HDM,
        VAR=d.VAR,
        COG=d.COG,
        SOG=d.SOG,
        LEE=d.LEE,
    )
    print(e, "\n")

    assert d._data.keys() == e._data.keys()
    for k in d._data.keys():
        assert round(d[k], 1) == round(e[k], 1), k


def to360(a):
    "limit a to [0,360)"
    while a < 0:
        a += 360
    return a % 360


def to180(a):
    "limit a to [-180,+180)"
    return to360(a + 180) - 180


def toCart(p):
    # to cartesian with phi going clock-wise from north
    return p[1] * sin(radians(p[0])), p[1] * cos(radians(p[0]))


def toPol(c):
    # to polar with phi going clock-wise from north
    return to360(90 - degrees(atan2(c[1], c[0]))), sqrt(c[0] ** 2 + c[1] ** 2)


def add_polar(a, b):
    "sum of polar vectors (phi,r)"
    a, b = toCart(a), toCart(b)
    s = a[0] + b[0], a[1] + b[1]
    return toPol(s)
