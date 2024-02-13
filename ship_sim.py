#!/usr/bin/env python3

"""
This is a simple NMEA based ship simulator for AvNav or SignalK.
It can be used for testing or showcasing these applications.

It simulates a ship by tracking its state (position, heading, speed, ...)
and the state of the environment (wind, current, depth) and integrating its motion over time.
The speed of the ship is calculated from polar data and wind, if sailing mode is enabled.
The speed of the simulation can be increased using the time factor.

The script listens on port 6000/TCP and serves NMEA sentences containing data as they would have been
acquired by the ship's sensors. There is some noise added to the data to make it look more realistic.

It also accepts RMB/APB sentences on the same TCP connection and will steer the supplied bearing.
"""

from datetime import datetime, timedelta
from time import monotonic, sleep
import socket, select
from random import gauss
from math import sin, cos, radians, degrees, atan2, sqrt, copysign, isfinite, asin
import json
from os.path import isfile
from time import monotonic
import numpy, scipy
import sys, re

TIME_FACTOR = 1  # speedup time
NOISE_FACTOR = 1  # scale measurement noise
AUTO_PILOT = 1  # enable autopilot, set to 2 to steer to optimal VMC
AIS_INTERVAL = 10  # interval (s) for emitting AIS sentences
POS_JSON = "position.json"  # read+write position and heading to this file if it exists
TCP_PORT = 6000  # port to listen on
# NMEA sentences with are sent to clients
NMEA_FILTER = [
    "RMC",
    # "GGA",
    # "ZDA",
    # "GLL",
    # "VTG",
    # "HDG",
    "VHW",
    "DBT",
    # "DBS",
    # "MWD",
    "MWV",
    # "ROT",
    # "RSA",
    # "RPM",
    # "VDR",
    "VDM",
]


def main():
    s = Ship()

    # environment
    s.wind_dir_ground = 30
    s.wind_speed_ground = 10

    s.current_set = 300
    s.current_drift = 1

    # ship's properties
    s.position = [54.7, 13.1]
    s.heading_true = 90
    if isfile(POS_JSON):
        s.position, s.heading_true = read(POS_JSON)

    s.sailing = 1
    s.speed_thr_water = 0
    s.rudder_angle = 0
    s.leeway_factor = 8
    s.mag_variation = 4.7

    s.ais_targets = [
        Ship(
            name="SALINA",
            mmsi=211318680,
            position=[deg(54, 40), deg(13, 11)],
            speed_thr_water=7,
            heading_true=340,
            sailing=1,
            ais_class="B",
        ),
        Ship(
            name="Queen Mary 2",
            mmsi=235762000,
            imo=9241061,
            callsign="ZCEF6",
            position=[54.75, 13.1],
            speed_thr_water=10,
            heading_true=150,
            # sailing=1,
        ),
        Ship(
            name="STEN PONTUS",
            mmsi=255951000,
            position=[54.81, 13.1],
            speed_thr_water=11,
            heading_true=72,
            # sailing=1,
        ),
        Ship(
            name="STI HAMMERSMITH",
            mmsi=538005410,
            position=[54.86, 13.1],
            speed_thr_water=13,
            heading_true=252,
            # sailing=1,
        ),
        Ship(
            name="INSEL HIDDENSEE",
            mmsi=211537340,
            position=[54.6, 13.17],
            speed_thr_water=8,
            heading_true=20,
            # sailing=1,
        ),
        Ship(
            name="BAMBERG",
            mmsi=211815680,
            position=[54.62, 12.95],
            speed_thr_water=7,
            heading_true=45,
            # sailing=1,
        ),
        Ship(
            name="LEILA",
            mmsi=211650310,
            position=[deg(54, 43), deg(13, 19)],
            speed_thr_water=6,
            heading_true=250,
            sailing=1,
            ais_class="B",
        ),
        Ship(
            name="TIGER",
            mmsi=253447000,
            position=[deg(54, 43), deg(12, 57)],
            speed_thr_water=15,
            heading_true=90,
            # sailing=1,
        ),
        Ship(
            name="ARKONA",
            mmsi=211130000,
            imo=9285811,
            position=[deg(54, 41), deg(13, 29)],
            speed_thr_water=11,
            heading_true=310,
            # sailing=1,
        ),
        Ship(
            name="MSC RENEE",
            mmsi=477307300,
            imo=9465306,
            position=[deg(54, 48), deg(13, 0)],
            speed_thr_water=20,
            heading_true=72,
            # sailing=1,
        ),
    ]

    server = Server("", TCP_PORT, s.nmea, s.autopilot)

    t0 = monotonic()
    while True:
        t1 = monotonic()
        s.update()
        if t1 - t0 > 1:
            print(s)
            if isfile(POS_JSON):
                write(POS_JSON, [s.position, s.heading_true])
            server.serve(s)
            t0 = t1
        sleep(1 / TIME_FACTOR)


class Ship:
    def __init__(self, **kwargs):
        self.time = datetime.utcnow()
        self.position = [0, 0]  # LAT/LON degrees
        self.heading_true = 0  # degrees
        self.speed_thr_water = 0  # knots
        self.sailing = False  # if to calculate boat speed from wind via polar
        self.rate_of_turn = 0  # deg/sec
        self.mag_deviation = 0
        self.mag_variation = 0
        self.rudder_angle = 0
        self.engine_rpm = 0
        self.depth = 10
        self.wind_speed_ground = 0
        self.wind_dir_ground = 0
        self.current_set = 0
        self.current_drift = 0
        self.leeway_factor = 8
        self.polar = Polar("polar.json")
        self.pheel = Polar("heel.json")
        self.sign = 0  # used by autopilot

        self.mmsi = 0
        self.imo = 0
        self.callsign = ""
        self.name = ""
        self.destination = ""
        self.ais_class = "A"
        self.ais_targets = []
        for k, v in kwargs.items():
            self.__dict__[k] = v
        self.ais_time = 0  # used for tracking AIS interval
        self.update(0)

    def update(self, delta_t=1):
        "update state, simple forward integration of motion to new position"
        self.time = self.time + timedelta(seconds=delta_t)

        if isfinite(self.rudder_angle):
            # rudder angle causes rate of turn, but proportional to speed
            rot = self.rudder_angle * max(0.2, min(2, self.speed_thr_water / 2)) / 4
            b = 0.2  # delayed change (exponential smoothing)
            self.rate_of_turn += b * (rot - self.rate_of_turn)

        self.heading_true = to360(self.heading_true + self.rate_of_turn * delta_t)
        self.heading_mag = to360(self.heading_true - self.mag_variation)
        # simple deviation model to simulate compass heading
        self.mag_deviation = 3 * sin(radians(self.heading_mag + 52))
        self.heading_cmp = to360(self.heading_mag - self.mag_deviation)

        self.wind_angle_ground = to180(self.wind_dir_ground - self.heading_true)

        self.wind_dir_true, self.wind_speed_true = add_polar(
            (self.current_set, self.current_drift),
            (self.wind_dir_ground, self.wind_speed_ground),
        )
        self.wind_angle_true = to180(self.wind_dir_true - self.heading_true)

        if self.sailing:
            # boat speed from true wind from polar data
            stw = self.polar.value(self.wind_angle_true, self.wind_speed_true)
            b = 0.05  # delayed change
            self.speed_thr_water += b * (stw - self.speed_thr_water)

            self.heel_angle = self.pheel.value(
                self.wind_angle_true, self.wind_speed_true
            )
            self.leeway = (
                clamp(
                    self.leeway_factor * self.heel_angle / self.speed_thr_water**2,
                    (-30, +30),
                )
                if self.speed_thr_water
                else 0
            )
        else:
            self.heel_angle, self.leeway = 0, 0

        self.course_thr_water = self.heading_true + self.leeway

        self.course_over_ground, self.speed_over_ground = add_polar(
            (self.current_set, self.current_drift),
            (self.course_thr_water, self.speed_thr_water),
        )

        distance = self.speed_over_ground * delta_t / 3600
        self.position = project(self.position, self.course_over_ground, distance)

        self.wind_dir_app, self.wind_speed_app = add_polar(
            (self.course_over_ground, self.speed_over_ground),
            (self.wind_dir_ground, self.wind_speed_ground),
        )
        self.wind_angle_app = to180(self.wind_dir_app - self.heading_true)

        for s in self.ais_targets:
            s.current_set = self.current_set
            s.current_drift = self.current_drift
            s.wind_dir_ground = self.wind_dir_ground
            s.wind_speed_ground = self.wind_speed_ground
            s.update(delta_t)

    def __str__(self):
        return "\n".join(
            [
                f"TME {self.time}",
                f"POS {self.position}",
                f"MAG {self.mag_deviation}D {self.mag_variation}V",
                f"HDG {self.heading_true}T {self.heading_mag}M {self.heading_cmp}C  ROT {self.rate_of_turn}",
                f"LEE {self.leeway}  HEL {self.heel_angle}",
                f"CRS {self.course_thr_water}  STW {self.speed_thr_water}",
                f"SET {self.current_set}  DRF {self.current_drift}",
                f"COG {self.course_over_ground}  SOG {self.speed_over_ground}",
                f"GWD {self.wind_dir_ground}  GWA {self.wind_angle_ground}  GWS {self.wind_speed_ground}",
                f"TWD {self.wind_dir_true}  TWA {self.wind_angle_true}  TWS {self.wind_speed_true}",
                f"AWD {self.wind_dir_app}  AWA {self.wind_angle_app}  AWS {self.wind_speed_app}",
                f"DPT {self.depth}  RUD {self.rudder_angle}  RPM {self.engine_rpm}",
            ]
        )

    def nmea(self):
        # https://gpsd.gitlab.io/gpsd/NMEA.html
        t = self.time
        hhmmss = f"{t.hour:02d}{t.minute:02d}{t.second:02d}"
        hhmmssss = hhmmss + f"{t.microsecond*1e-6:.2f}"[1:]
        ddmmyy = f"{t.day:02d}{t.month:02d}{t.year%100:02d}"
        sats = 12
        fix_quality = 8  # 0=NO 1=GPS 2=DGPS 8=SIM
        hdop = noisy(1, relative=10)
        lat = noisy(self.position[0], absolute=hdop / 1852 / 60)
        latdeg, latmin = divmod(abs(lat) * 60, 60)
        latsgn = "S" if lat < 0 else "N"
        lon = noisy(self.position[1], absolute=hdop / 1852 / 60 * cos(radians(lat)))
        londeg, lonmin = divmod(abs(lon) * 60, 60)
        lonsgn = "W" if lon < 0 else "E"
        sog = noisy(self.speed_over_ground)
        cog = noisy(self.course_over_ground, absolute=1)
        stw = noisy(self.speed_thr_water)
        altitude = noisy(3)
        rot = noisy(self.rate_of_turn * 60)
        depth = noisy(self.depth)  # below transducer

        magdev = self.mag_deviation
        magdevdir = "W" if magdev < 0 else "E"
        magvar = self.mag_variation
        magvardir = "W" if magvar < 0 else "E"

        heading = noisy(self.heading_true, absolute=1)
        heading_mag = noisy(self.heading_mag, absolute=1)
        heading_cmp = noisy(self.heading_cmp, absolute=1)

        wind_speed_true = noisy(self.wind_speed_true)
        wind_dir_true = noisy(to360(self.wind_dir_true), absolute=1)
        wind_angle_true = noisy(to360(self.wind_angle_true), absolute=1)
        wind_speed_app = noisy(self.wind_speed_app)
        wind_angle_app = noisy(to360(self.wind_angle_app), absolute=1)

        sentences = [
            f"GPRMC,{hhmmssss},A,{latdeg:02.0f}{latmin:06.3f},{latsgn},{londeg:03.0f}{lonmin:06.3f},{lonsgn},{sog:05.1f},{cog:05.1f},{ddmmyy},{abs(magvar):.1f},{magvardir}",
            f"GPGGA,{hhmmssss},{latdeg:02.0f}{latmin:05.2f},{latsgn},{londeg:03.0f}{lonmin:05.2f},{lonsgn},{fix_quality},{sats:02d},{hdop:03.1f},{altitude:.1f},M,{0:.1f},M,,",
            f"GPZDA,{hhmmssss},{t.day:02d},{t.month:02d},{t.year:04d},{1:02d},{0:02d}",
            f"GPGLL,{latdeg:02.0f}{latmin:07.04f},{latsgn},{londeg:03.0f}{lonmin:07.04f},{lonsgn},{hhmmssss},A",
            f"GPVTG,{cog:.1f},T,,,{sog:.1f},N,,",
            f"HCHDG,{heading_cmp:.1f},{abs(magdev):.1f},{magdevdir},{abs(magvar):.1f},{magvardir}",
            f"VWVHW,{heading:.1f},T,{heading_mag:.1f},M,{stw:.1f},N,,",
            f"SDDBT,,,{depth:.1f},M,,",  # below transducer
            f"SDDBS,,,{depth:.1f},M,,",  # below surface
            f"WIMWD,{wind_dir_true:.1f},T,,,{wind_speed_true:.1f},N,,",
            f"WIMWV,{wind_angle_true:.1f},T,{wind_speed_true:.1f},N,A",
            f"WIMWV,{wind_angle_app:.1f},R,{wind_speed_app:.1f},N,A",
            f"HCROT,{rot:.1f},A",
            f"RIRSA,{self.rudder_angle:.1f},A,,",
            f"ERRPM,E,1,{noisy(self.engine_rpm):.1f},,A",
            f"CCVDR,{self.current_set:.1f},T,,,{self.current_drift:.1f},N",
        ]

        t = monotonic()
        if (t - self.ais_time) * TIME_FACTOR > AIS_INTERVAL:
            self.ais_time = t
            for s in self.ais_targets:
                sentences += ais(s)
                s.ais_time = t

        return "".join(
            [
                f"{'!' if s.startswith('AIVDM') else '$'}{s}*{nmea_crc(s):02x}\n"
                for s in sentences
                if s[2:5] in NMEA_FILTER
            ]
        )

    def autopilot(self, data):
        # receive waypoint to steer to
        if not data or not AUTO_PILOT:
            return
        nmea = decode_nmea(data)
        if not nmea:
            return
        brg, xte = nmea
        cts = brg  # course to steer
        brg_twd = to180(brg - self.wind_dir_true)  # BRG from TWD
        msg = ""
        if self.sailing:
            max_xte = 1
            big_xte = abs(xte) > max_xte
            if AUTO_PILOT == 2 and 15 < abs(brg_twd) < 170 and not big_xte:
                cts = self.polar.vmc_angle(
                    self.wind_dir_true, self.wind_speed_true, brg
                )
                self.sign = 0
                msg = "OPTVMC"
            else:
                min_twa = self.polar.angle(self.wind_speed_true, True)
                max_twa = self.polar.angle(self.wind_speed_true, False)
                if abs(brg_twd) < min_twa:  # too high upwind
                    if not self.sign or big_xte:
                        self.sign = copysign(1, xte if big_xte else brg_twd)
                    cts = to360(self.wind_dir_true + self.sign * min_twa)
                    msg = "upwind layline"
                elif abs(brg_twd) > max_twa:  # too low downwind
                    if not self.sign or big_xte:
                        self.sign = copysign(1, -xte if big_xte else brg_twd)
                    cts = to360(self.wind_dir_true + self.sign * max_twa)
                    msg = "downwind layline"
                else:
                    self.sign = 0
        crs = self.heading_true  # if s.sign or hdt_cog > 60 else s.cog
        cer = to180(cts - crs)  # course error
        if TIME_FACTOR > 2:
            self.rudder_angle = 0
            self.heading_true = to360(self.heading_true + cer)
        else:
            self.rudder_angle = round(copysign(min(10, 0.2 * abs(cer)), cer))
            print("CTS", cts, "XTE", xte, "CER", cer, "RUD", self.rudder_angle, msg)


class Polar:
    def __init__(self, filename):
        with open(filename) as f:
            self.data = json.load(f)
        self.spl = None

    def has_angle(self, upwind):
        return ("beat_angle" if upwind else "run_angle") in self.data

    def angle(self, tws, upwind):
        angle = self.data["beat_angle" if upwind else "run_angle"]
        return numpy.interp(tws, self.data["TWS"], angle)

    def value(self, twa, tws):
        if not self.spl:
            val = "STW" if "STW" in self.data else "heel"
            self.spl = scipy.interpolate.RectBivariateSpline(
                self.data["TWA"], self.data["TWS"], self.data[val]
            )
        return max(0.0, float(self.spl(abs(twa), tws)))

    def vmc_angle(self, twd, tws, brg, s=1):
        brg_twd = to180(brg - twd)  # BRG from wind

        def vmc(twa):
            # negative sign for minimizer
            return -self.value(twa, tws) * cos(radians(s * twa - abs(brg_twd)))

        res = scipy.optimize.minimize_scalar(vmc, bounds=(0, 180))

        if res.success:
            return to360(twd + s * copysign(res.x, brg_twd))


class Server:
    def __init__(self, addr, port, send, receive):
        self.send = send
        self.receive = receive
        if socket.has_dualstack_ipv6():
            self.server = socket.create_server(
                (addr, port), family=socket.AF_INET6, dualstack_ipv6=True
            )
        else:
            self.server = socket.create_server((addr, port))

        self.conns = []

    def serve(self, ship):
        try:
            rx, tx, er = select.select([self.server], [], [self.server], 0)
            # print("server", rx, tx, er)
            for so in rx:
                conn, addr = so.accept()
                print("accepted", conn, file=sys.stderr)
                conn.setblocking(False)
                self.conns.append(conn)

            if not self.conns:
                return

            rx, tx, er = select.select(self.conns, self.conns, self.conns, 0)
            # print("connections", rx, tx, er)

            if tx:
                data = self.send()
                print(data, file=sys.stderr)
                for co in tx:
                    try:
                        # print("TX", co)
                        co.send(data.encode())
                        # print(data, file=sys.stderr)
                    except Exception as x:
                        print(x, co, file=sys.stderr)
                        self.conns.remove(co)

            for co in rx:
                try:
                    # print("RX", co)
                    data = co.recv(4096).decode()
                    if data:
                        print(data, file=sys.stderr)
                        self.receive(data)
                except Exception as x:
                    print(x, co, file=sys.stderr)
                    self.conns.remove(co)

            for co in er:
                print("ERROR", co, file=sys.stderr)
                self.conns.remove(co)

        except Exception as x:
            print(x, file=sys.stderr)


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


def project(point, bearing, distance):
    "great circle projection: point -(bearing,distance)-> point"
    lat1, lon1 = (radians(a) for a in point)
    bearing = radians(bearing)
    distance *= 1852  # to meters
    distance /= 6371008.8  # angular distance

    lat2 = asin(sin(lat1) * cos(distance) + cos(lat1) * sin(distance) * cos(bearing))
    y = sin(bearing) * sin(distance) * cos(lat1)
    x = cos(distance) - sin(lat1) * sin(lat2)
    lon2 = lon1 + atan2(y, x)

    return [to180(degrees(a)) for a in (lat2, lon2)]


def nmea_crc(senctence):
    crc = 0
    for c in senctence:
        crc = crc ^ ord(c)
    return crc & 0xFF


def write(filename, data):
    with open(filename, "w") as f:
        # f.write(data)
        json.dump(data, f)


def read(filename):
    with open(filename) as f:
        return json.load(f)


def noisy(value, absolute=0, relative=1):
    "add gaussian random to simulate measurement noise"
    return (
        gauss(
            value,
            NOISE_FACTOR * (absolute if absolute else abs(value * relative / 100)),
        )
        if NOISE_FACTOR
        else value
    )


def decode_nmea(data):
    if __name__ == "__main__":
        for l in data.splitlines():
            try:
                # print(l)
                # $GPRMB,A,1.70,L,8,9,5509.36,N,01335.04,E,7.8,261.9,5.7,V,A*51
                # $GPAPB,A,A,1.70,L,N,V,,274.5,T,9,261.9,T,261.9,T*4F
                m = re.match(
                    "\$..(APB|RMB)" + ",([^,]*)" * 14 + "\*..",
                    l,
                )
                if m:
                    # print(m, m.groups())
                    o = 0 if m.group(1) == "RMB" else 1
                    return (
                        float(m.group(12)),  # BRG
                        float(m.group(3 + o))  # XTE
                        * (-1 if m.group(4 + o) == "L" else 1),
                    )

            except Exception as x:
                print(x, file=sys.stderr)


def clamp(x, limits):
    "limit x to limits [a,b]"
    a, b = limits
    assert a < b, limits
    return max(a, min(b, x))


def deg(d, m=0, s=0):
    return d + m / 60 + s / 3600


import struct

AIS_CODE = "0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVW`abcdefghijklmnopqrstuvw"
AIS_ASCII = "@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_ !\"#$%&'()*+,-./0123456789:;<=>?"


def list_to_int(data):
    i = 0
    for v in data:
        assert 0 <= v < 64
        i = i << 6 | v
    # print(f"{i} {i:x} {i:b}")
    return i


def int_to_list(i):
    l = []
    while i:
        l.insert(0, i & 0b111111)
        i = i >> 6
    # print(l)
    return l


def ais_encode(data):
    if type(data) == str:
        assert "@" not in data
        return list(AIS_ASCII.index(v) for v in data.upper() + "@")
    else:
        return "".join([AIS_CODE[v] for v in data])


def ais_decode(data):
    if type(data) == str:
        return list(AIS_CODE.index(v) for v in data)
    else:
        s = "".join([AIS_ASCII[v] for v in data])
        s = s.strip()
        return s[0 : s.index("@")]


type1 = 6, 2, 30, 4, 8, 10, 1, 28, 27, 12, 9, 6, 2, 3, 1, 19


def ais_a(s):
    data = (
        1,  # type
        0,  # repeat
        s.mmsi,
        5 if s.speed_over_ground < 0.2 else 8 if s.sailing else 0,  # navstat
        0,  # rot
        int(10 * s.speed_over_ground),
        0,  # posacc
        int(600000 * s.position[1]),  # lon
        int(600000 * s.position[0]),  # lat
        int(10 * s.course_over_ground),
        int(s.heading_true),
        60,  # time
        0,  # maneuver
        0,  # spare
        0,  # raim
        0,  # radiostat
    )
    return ais_nmea(type1, data)


type5 = (6, 2, 30, 2, 30, 42, 120, 8, 9, 9, 6, 6, 4, 4, 5, 5, 6, 8, 120, 1, 1)


def ais_a2(s):
    data = (
        5,  # type
        0,  # repeat
        s.mmsi,
        0,  # ais version
        s.imo,  # IMO number
        ais_str(s.callsign, 7),  # callsign
        ais_str(s.name, 20),
        36 if s.sailing else 70,  # ship type 70=cargo 80=tanker 90=other
        100,  # to bow
        100,  # to stern
        25,  # to port
        25,  # to starboard
        3,  # fix type 0=undef 1=gps 2=glonass 3=1+2
        0,  # ETA month
        0,  # ETA day
        0,  # ETA hour
        0,  # ETA minute
        int(10 * 5),  # draught
        ais_str(s.destination, 20),  # destination
        0,  # dte
        0,  # spare
    )
    return ais_nmea(type5, data)


type18 = 6, 2, 30, 8, 10, 1, 28, 27, 12, 9, 6, 2, 1, 1, 1, 1, 1, 1, 1, 20


def ais_b(s):
    data = (
        18,  # type
        0,  # repeat
        s.mmsi,
        0,  # reserved
        int(10 * s.speed_over_ground),
        0,  # pos accuracy
        int(600000 * s.position[1]),  # lon
        int(600000 * s.position[0]),  # lat
        int(10 * s.course_over_ground),
        int(s.heading_true),
        60,  # timestamp
        0,  # reserved
        0,  # cs unit
        1,  # display
        1,  # dsc
        0,  # band flag
        0,  # msg22 flag
        0,  # assigned
        0,  # raim
        0,  # radio status
    )
    return ais_nmea(type18, data)


type19 = 6, 2, 30, 8, 10, 1, 28, 27, 12, 9, 6, 4, 120, 8, 9, 9, 6, 6, 4, 1, 1, 1, 4


def ais_b2(s):
    data = (
        19,  # type
        0,  # repeat
        s.mmsi,
        0,  # reserved
        int(10 * s.speed_over_ground),
        0,  # pos accuracy
        int(600000 * s.position[1]),  # lon
        int(600000 * s.position[0]),  # lat
        int(10 * s.course_over_ground),
        int(s.heading_true),
        60,  # timestamp
        0,  # reserved
        ais_str(s.name, 20),  # name
        36 if s.sailing else 37,  # ship type
        5,  # to bow
        5,  # to stern
        2,  # to port
        2,  # to starboard
        1,  # fix type
        0,  # raim
        0,  # dte
        0,  # assigned
        0,  # spare
    )
    return ais_nmea(type19, data)


def ais_str(string, chars):
    l = ais_encode(string)[:chars]
    # print(l, len(l))
    i = list_to_int(l)
    n = 6 * len(l)
    m = (1 << n) - 1
    return (i & m) << (chars * 6 - n)


def ais_nmea(atype, data):
    assert sum(atype) % 8 == 0
    assert len(atype) == len(data)
    p = 0
    n = sum(atype)
    while (n + p) % 6 or (n + p) % 8:
        p += 1
    b = 0
    for i, n in enumerate(atype):
        m = (1 << n) - 1
        b = b << n | (data[i] & m)
    b = b << p
    # print(f"{b:b}")
    l = int_to_list(b)
    # print(l)
    # print(" ".join(f"{v:06b}" for v in l))
    e = ais_encode(l)
    # print(e)
    return f"AIVDM,1,1,,B,{e},{p}"


def ais(s):
    if s.ais_class == "A":
        return (ais_a(s), ais_a2(s))
    else:
        return (ais_b2(s),)


if __name__ == "__main__":
    main()
