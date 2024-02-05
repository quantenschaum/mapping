#!/usr/bin/env python3

from datetime import datetime, timedelta
from lightsectors import project_gc as project
from time import monotonic, sleep
from socket import socket, AF_INET, SOCK_DGRAM, SOCK_STREAM
from random import gauss
from math import sin, cos, radians, degrees, nan, atan2, sqrt, copysign, exp, isfinite
from threading import Lock, Thread
import json


def to360(a):
    "limit a to [0,360)"
    while a < 0:
        a += 360
    return a % 360


def to180(a):
    "limit a to [-180,+180)"
    a = to360(a)
    return a if a < 180 else a - 360


def add_polar(a, b):
    "sum of polar vectors (phi,r)"
    # to cartesian with phi going clock-wise from north
    a = a[1] * sin(radians(a[0])), a[1] * cos(radians(a[0]))
    b = b[1] * sin(radians(b[0])), b[1] * cos(radians(b[0]))
    # sum of cartesian vectors
    s = a[0] + b[0], a[1] + b[1]
    # back to polar with phi going clock-wise from north
    r = sqrt(s[0] ** 2 + s[1] ** 2)
    phi = to360(90 - degrees(atan2(s[1], s[0])))
    return phi, r


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
            noise_factor * (absolute if absolute else abs(value * relative / 100)),
        )
        if noise_factor
        else value
    )


class Ship:
    def __init__(self):
        self.time = datetime.utcnow()
        self.position = [0, 0]  # LAT/LON degrees
        self.heading_true = 0  # HDG degrees true
        self.speed_thr_water = 0  # STW knots
        self.max_speed = 8
        self.sailing = False  #  if to calculate boat speed from wind
        self.rate_of_turn = 0  # ROT deg/sec
        self.mag_deviation = 0
        self.mag_variation = 0
        self.rudder_angle = 0
        self.engine_rpm = 0
        self.depth = nan
        self.wind_speed_ground = 0  # ground wind
        self.wind_dir_ground = 0
        self.current_set = 0  # water current
        self.current_drift = 0
        self.leeway_factor = 8

    def update(self, delta_t=1):
        self.time = self.time + timedelta(seconds=delta_t)

        if isfinite(self.rudder_angle):
            # rudder angle causes rate of turn, but proportional to speed
            rot = self.rudder_angle * min(2, self.speed_thr_water / 2) / 4
            b = 0.2  # change with delay
            self.rate_of_turn += b * (rot - self.rate_of_turn)

        # update heading
        self.heading_true = to360(self.heading_true + self.rate_of_turn * delta_t)
        # magnetic heading from variation HDT=HDM+VAR
        self.heading_mag = to360(self.heading_true - self.mag_variation)
        # simple deviation model to simulate compass heading HDM=HDC+DEV
        self.mag_deviation = 3 * sin(radians(self.heading_true + 52))
        self.heading_cmp = to360(self.heading_mag - self.mag_deviation)

        self.wind_angle_ground = to180(self.wind_dir_ground - self.heading_true)

        # true wind is relative to water: ground wind + set/drift
        self.wind_dir_water, self.wind_speed_water = add_polar(
            (self.current_set, self.current_drift),
            (self.wind_dir_ground, self.wind_speed_ground),
        )
        self.wind_angle_water = to180(self.wind_dir_water - self.heading_true)

        if self.sailing:
            # boat speed from true wind via simple polar
            tws, twa = self.wind_speed_water, abs(self.wind_angle_water)
            stw = self.max_speed / (1 + exp((8 - tws) / 3))
            stw *= sin(0.8 * radians(twa)) ** (1 + (90 - twa) / 300)
            b = 0.05  # speed changes delayed
            self.speed_thr_water += b * (stw - self.speed_thr_water)

        # leeway due to wind
        self.leeway = -self.leeway_factor * copysign(
            min(1, (180 - abs(self.wind_angle_water)) / 140) ** 4, self.wind_angle_water
        )

        # SOG and COG: set/drift + (heading+leeway)/water speed
        self.cog, self.sog = add_polar(
            (self.current_set, self.current_drift),
            (self.heading_true + self.leeway, self.speed_thr_water),
        )

        distance = self.sog * delta_t / 3600  # distance travelled over ground
        self.position = project(self.position, self.cog, distance)  # new position

        # apparent wind, two ways to calculate, same result
        # 1. ground wind + COG/SOG
        # 2. true wind + (heading+leeway)/water speed
        self.wind_dir_app, self.wind_speed_app = add_polar(
            (self.cog, self.sog),
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
                f"STW {self.speed_thr_water}  LEE {self.leeway}",
                f"SOG {self.sog}  COG {self.cog}",
                f"SET {self.current_set}  DRF {self.current_drift}",
                f"GWD {self.wind_dir_ground}  GWA {self.wind_angle_ground}  GWS {self.wind_speed_ground}",
                f"TWD {self.wind_dir_water}  TWA {self.wind_angle_water}  TWS {self.wind_speed_water}",
                f"AWD {self.wind_dir_app}  AWA {self.wind_angle_app}  AWS {self.wind_speed_app}",
                f"DPT {self.depth}  RUD {self.rudder_angle}  RPM {self.engine_rpm}",
            ]
        )

    def nmea(self):
        # https://campar.in.tum.de/twiki/pub/Chair/NaviGpsDemon/nmea.html
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
        sog = noisy(self.sog)
        cog = noisy(self.cog, absolute=1)
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


noise_factor = 0
time_factor = 1
auto_pilot = 0  # enable primitive auto pilot to sail to RMB


def main():
    s = Ship()

    # ship's properties
    s.position = [54.625, 13.18]
    s.heading_true = 0
    # s.position, s.heading_true = read("pos.json")
    s.speed_thr_water = 0
    s.sailing = 1  # calc speed from wind if 1
    s.rudder_angle = 0
    s.leeway_factor = 8
    s.mag_variation = 0  # 4.7
    s.depth = 8
    s.wind_dir_ground = 60
    s.wind_speed_ground = 15
    s.current_set = 90
    s.current_drift = 0

    s.update()

    dest = "openplotter", 10110
    dest = "localhost", 34667
    sock = socket(AF_INET, SOCK_DGRAM)

    def transmit():
        # print(s, end="\n\n")
        n = "\n"
        data = f"{n.join(s.nmea())}{n}"
        # print(data)
        sock.sendto(data.encode("utf8"), dest)
        write("pos.json", [s.position, s.heading_true])

    sock = socket(AF_INET, SOCK_DGRAM)
    sock.bind(("0.0.0.0", 2000))

    def receive():
        while True:
            data, addr = sock.recvfrom(10000)
            # print(">", data)
            for l in data.decode("utf8").splitlines():
                # $GPRMB,A,0.00,R,2,3,5438.68,N,01310.22,E,1.2,343.9,3.4,V,A*4A
                # print(l)
                if l.startswith("$GPRMB"):
                    parts = l.split(",")
                    # print(parts)
            active = parts[1] == "A"
            xte = float(parts[2]) * (-1 if parts[3] == "L" else +1)
            brg = float(parts[11])
            if active and auto_pilot:
                # s.heading_true = brg
                d = round(to180(brg - s.heading_true))
                s.rudder_angle = round(copysign(min(10, 0.3 * abs(d)), d))
                print("STEER", d, "RUDDER", s.rudder_angle)

    if auto_pilot:
        Thread(target=receive, daemon=True).start()

    t0 = monotonic()
    while 1:
        t1 = monotonic()
        s.update()
        if t1 - t0 > 1:
            transmit()
            t0 = t1
        sleep(1 / time_factor)


if __name__ == "__main__":
    main()
