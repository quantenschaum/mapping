#!/usr/bin/env python3

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

TIME_FACTOR = 10  # speedup time
NOISE_FACTOR = 1  # scale measurement noise
AUTO_PILOT = 2  # enable autopilot
POS_JSON = None  # if set store/restore position
# POS_JSON = "position.json"
TCP_PORT = 6000  # port to listen on


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
    if POS_JSON and isfile(POS_JSON):
        s.position, s.heading_true = read(POS_JSON)

    s.sailing = 1
    s.speed_thr_water = 0
    s.rudder_angle = 0
    s.leeway_factor = 8
    s.mag_variation = 4.7

    s.update()

    server = Server("", TCP_PORT)

    t0 = monotonic()
    while True:
        t1 = monotonic()
        s.update()
        if t1 - t0 > 1:
            print(s)
            if POS_JSON:
                write(POS_JSON, [s.position, s.heading_true])
            server.serve(s)
            t0 = t1
        sleep(1 / TIME_FACTOR)


class Server:
    def __init__(self, addr, port):
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

            data = "\n".join(ship.nmea()) + "\n" if tx else None
            for co in tx:
                try:
                    # print("TX", co)
                    co.send(data.encode())
                    # print(data, file=sys.stderr)
                except Exception as x:
                    print(x, co, file=sys.stderr)
                    self.conns.remove(co)

            data = ""
            for co in rx:
                try:
                    # print("RX", co)
                    data += co.recv(4096).decode() + "\n"
                    # print(data, file=sys.stderr)
                except Exception as x:
                    print(x, co, file=sys.stderr)
                    self.conns.remove(co)

            for co in er:
                print("ERROR", co, file=sys.stderr)
                self.conns.remove(co)

            self.autopilot(data, ship)

        except Exception as x:
            print(x)

    def autopilot(self, data, ship):
        # receive waypoint to steer to
        if not data or not AUTO_PILOT:
            return
        nmea = decode_nmea(data)
        if not nmea:
            return
        brg, xte = nmea
        cts = brg  # course to steer
        brg_twd = to180(brg - ship.wind_dir_water)  # BRG from TWD
        msg = ""
        if ship.sailing:
            max_xte = 1
            big_xte = abs(xte) > max_xte
            if AUTO_PILOT == 2 and 15 < abs(brg_twd) < 170 and not big_xte:
                cts = ship.polar.vmc_angle(
                    ship.wind_dir_water, ship.wind_speed_water, brg
                )
                ship.sign = 0
                msg = "OPTVMC"
            else:
                min_twa = ship.polar.angle(ship.wind_speed_water, True)
                max_twa = ship.polar.angle(ship.wind_speed_water, False)
                if abs(brg_twd) < min_twa:  # too high upwind
                    if not ship.sign or big_xte:
                        ship.sign = copysign(1, xte if big_xte else brg_twd)
                    cts = to360(ship.wind_dir_water + ship.sign * min_twa)
                    msg = "upwind layline"
                elif abs(brg_twd) > max_twa:  # too low downwind
                    if not ship.sign or big_xte:
                        ship.sign = copysign(1, xte if big_xte else brg_twd)
                    cts = to360(ship.wind_dir_water + ship.sign * max_twa)
                    msg = "downwind layline"
                else:
                    ship.sign = 0
        crs = ship.heading_true  # if s.sign or hdt_cog > 60 else s.cog
        err = to180(cts - crs)
        if TIME_FACTOR > 2:
            ship.rudder_angle = 0
            ship.heading_true = to360(ship.heading_true + err)
        else:
            ship.rudder_angle = round(copysign(min(10, 0.2 * abs(err)), err))
        print(">>>", "CTS", cts, "XTE", xte, "ERR", err, "RUD", ship.rudder_angle, msg)


class Ship:
    def __init__(self):
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
        self.sign = 0

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

        self.wind_dir_water, self.wind_speed_water = add_polar(
            (self.current_set, self.current_drift),
            (self.wind_dir_ground, self.wind_speed_ground),
        )
        self.wind_angle_water = to180(self.wind_dir_water - self.heading_true)

        if self.sailing:
            # boat speed from true wind from polar data
            stw = self.polar.speed(self.wind_angle_water, self.wind_speed_water)
            b = 0.05  # delayed change
            self.speed_thr_water += b * (stw - self.speed_thr_water)

        self.heel_angle = self.pheel.heel(self.wind_angle_water, self.wind_speed_water)
        self.leeway = (
            min(
                30,
                max(
                    -30,
                    self.leeway_factor * self.heel_angle / self.speed_thr_water**2,
                ),
            )
            if self.speed_thr_water
            else 0
        )

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
                f"TWD {self.wind_dir_water}  TWA {self.wind_angle_water}  TWS {self.wind_speed_water}",
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

        wind_speed_water = noisy(self.wind_speed_water)
        wind_dir_water = noisy(to360(self.wind_dir_water), absolute=1)
        wind_angle_water = noisy(to360(self.wind_angle_water), absolute=1)
        wind_speed_app = noisy(self.wind_speed_app)
        wind_angle_app = noisy(to360(self.wind_angle_app), absolute=1)

        sentences = [
            f"GPRMC,{hhmmssss},A,{latdeg:02.0f}{latmin:06.3f},{latsgn},{londeg:03.0f}{lonmin:06.3f},{lonsgn},{sog:05.1f},{cog:05.1f},{ddmmyy},{abs(magvar):.1f},{magvardir}",
            # f"GPGGA,{hhmmssss},{latdeg:02.0f}{latmin:05.2f},{latsgn},{londeg:03.0f}{lonmin:05.2f},{lonsgn},{fix_quality},{sats:02d},{hdop:03.1f},{altitude:.1f},M,{0:.1f},M,,",
            # f"GPZDA,{hhmmssss},{t.day:02d},{t.month:02d},{t.year:04d},{1:02d},{0:02d}",
            # f"GPGLL,{latdeg:02.0f}{latmin:07.04f},{latsgn},{londeg:03.0f}{lonmin:07.04f},{lonsgn},{hhmmssss},A",
            # f"GPVTG,{cog:.1f},T,,,{sog:.1f},N,,",
            # f"HCHDG,{heading_cmp:.1f},{abs(magdev):.1f},{magdevdir},{abs(magvar):.1f},{magvardir}",
            f"VWVHW,{heading:.1f},T,{heading_mag:.1f},M,{stw:.1f},N,,",
            # f"SDDBT,,,{depth:.1f},M,,",  # below transducer
            # f"SDDBS,,,{depth:.1f},M,,",# below surface
            # f"WIMWD,{wind_dir_water:.1f},T,,,{wind_speed_water:.1f},N,,",
            # f"WIMWV,{wind_angle_water:.1f},T,{wind_speed_water:.1f},N,A",
            f"WIMWV,{wind_angle_app:.1f},R,{wind_speed_app:.1f},N,A",
            # f"HCROT,{rot:.1f},A",
            # f"RIRSA,{self.rudder_angle:.1f},A,,",
            # f"ERRPM,E,1,{noisy(self.rpm):.1f},,A",
            # f"CCVDR,{self.current_set:.1f},T,,,{self.current_drift:.1f},N",
        ]

        return [f"${s}*{nmea_crc(s):02x}" for s in sentences]


class Polar:
    def __init__(self, filename):
        with open(filename) as f:
            self.data = json.load(f)

    def has_angle(self, upwind):
        return ("beat_angle" if upwind else "run_angle") in self.data

    def angle(self, tws, upwind):
        angle = self.data["beat_angle" if upwind else "run_angle"]
        return numpy.interp(tws, self.data["TWS"], angle)

    def speed(self, twa, tws):
        spl = scipy.interpolate.RectBivariateSpline(
            self.data["TWA"], self.data["TWS"], self.data["STW"]
        )
        return max(0.0, float(spl(abs(twa), tws)))

    def heel(self, twa, tws):
        spl = scipy.interpolate.RectBivariateSpline(
            self.data["TWA"], self.data["TWS"], self.data["heel"]
        )
        return copysign(max(0.0, float(spl(abs(twa), tws))), -twa)

    def vmc_angle(self, twd, tws, brg, s=1):
        brg_twd = to180(brg - twd)  # BRG from wind

        def vmc(twa):
            # negative sign for minimizer
            return -self.speed(twa, tws) * cos(radians(s * twa - abs(brg_twd)))

        res = scipy.optimize.minimize_scalar(vmc, bounds=(0, 180))

        if res.success:
            return to360(twd + s * copysign(res.x, brg_twd))


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
                print(x)


if __name__ == "__main__":
    main()
