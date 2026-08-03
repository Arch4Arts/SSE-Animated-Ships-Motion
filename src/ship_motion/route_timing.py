from bisect import bisect_right
from dataclasses import dataclass
import math


def unwrap_headings(values):
    if not values:
        return []
    result = [float(values[0])]
    for value in values[1:]:
        candidate = float(value)
        while candidate - result[-1] > math.pi:
            candidate -= 2 * math.pi
        while candidate - result[-1] < -math.pi:
            candidate += 2 * math.pi
        result.append(candidate)
    return result


def smooth_cyclic_headings(values, radius: int):
    values = unwrap_headings(values)
    if radius < 1 or len(values) < 3:
        raise ValueError("cyclic smoothing requires radius >= 1 and three headings")
    count = len(values) - 1
    winding = values[-1] - values[0]
    weights = [radius + 1 - abs(offset) for offset in range(-radius, radius + 1)]
    total = sum(weights)
    smoothed = []
    for index in range(count):
        value = 0.0
        for offset, weight in zip(range(-radius, radius + 1), weights):
            cycle, wrapped = divmod(index + offset, count)
            value += weight * (values[wrapped] + cycle * winding)
        smoothed.append(value / total)
    smoothed.append(smoothed[0] + winding)
    return smoothed


def pchip_tangents(times, values):
    times = [float(x) for x in times]; values = [float(x) for x in values]
    if len(times) != len(values) or len(times) < 2:
        raise ValueError("PCHIP requires matching time/value arrays")
    h = [b-a for a,b in zip(times,times[1:])]
    if any(x <= 0 for x in h):
        raise ValueError("PCHIP times must be strictly increasing")
    delta = [(b-a)/step for a,b,step in zip(values,values[1:],h)]
    tangents = [delta[0]] + [0.0] * (len(values)-2) + [delta[-1]]
    for i in range(1, len(values)-1):
        left, right = delta[i-1], delta[i]
        if left == 0 or right == 0 or left * right <= 0:
            tangents[i] = 0.0
        else:
            w1 = 2*h[i] + h[i-1]; w2 = h[i] + 2*h[i-1]
            tangents[i] = (w1+w2)/(w1/left+w2/right)
    return tangents


@dataclass(frozen=True)
class RouteTimingStats:
    max_curvature_degrees: float
    max_turn_strength: float
    original_duration: float
    mapped_duration: float
    speed_factors: tuple[float, ...]

    @property
    def minimum_speed_factor(self):
        return min(self.speed_factors)


@dataclass(frozen=True)
class LinearHeadingKey:
    time: float
    value: float


@dataclass(frozen=True)
class TimeMap:
    old_times: tuple[float, ...]
    new_times: tuple[float, ...]

    def map_time(self, value: float) -> float:
        if value < self.old_times[0] or value > self.old_times[-1]:
            raise ValueError(f"time outside time-map domain: {value}")
        if value == self.old_times[-1]:
            return self.new_times[-1]
        index = bisect_right(self.old_times, value) - 1
        ratio = (value - self.old_times[index]) / (self.old_times[index + 1] - self.old_times[index])
        return self.new_times[index] + ratio * (self.new_times[index + 1] - self.new_times[index])


def curvature_strength(angle_degrees: float) -> float:
    if angle_degrees <= 3.0:
        return 0.0
    if angle_degrees < 10.0:
        return (angle_degrees - 3.0) / 14.0
    if angle_degrees < 20.0:
        return 0.5 + (angle_degrees - 10.0) / 20.0
    return 1.0


def vertex_angles(points_xy: list[tuple[float, float]]) -> list[float]:
    if len(points_xy) < 2:
        raise ValueError("route requires at least two points")
    result = [0.0] * len(points_xy)
    for index in range(1, len(points_xy) - 1):
        incoming = (points_xy[index][0] - points_xy[index - 1][0], points_xy[index][1] - points_xy[index - 1][1])
        outgoing = (points_xy[index + 1][0] - points_xy[index][0], points_xy[index + 1][1] - points_xy[index][1])
        a = math.hypot(*incoming)
        b = math.hypot(*outgoing)
        if a == 0.0 or b == 0.0:
            raise ValueError("route contains zero-length segment")
        cosine = max(-1.0, min(1.0, (incoming[0] * outgoing[0] + incoming[1] * outgoing[1]) / (a * b)))
        result[index] = math.degrees(math.acos(cosine))
    for left, right in zip(points_xy, points_xy[1:]):
        if left == right:
            raise ValueError("route contains zero-length segment")
    return result


def interval_strengths(points_xy: list[tuple[float, float]], radius: int = 1) -> list[float]:
    strengths = [curvature_strength(value) for value in vertex_angles(points_xy)]
    base = [max(strengths[index], strengths[index + 1]) for index in range(len(points_xy) - 1)]
    return [min(1.0, max(
        base[other] * ((radius + 1 - abs(index-other))/(radius+1))
        for other in range(max(0,index-radius), min(len(base),index+radius+1))
    )) for index in range(len(base))]


def signed_vertex_turns(points_xy: list[tuple[float, float]]) -> list[float]:
    vertex_angles(points_xy)  # validates route and zero-length segments
    headings = [math.atan2(b[1]-a[1], b[0]-a[0]) for a,b in zip(points_xy, points_xy[1:])]
    result = [0.0] * len(points_xy)
    for index in range(1, len(points_xy)-1):
        delta = math.degrees(headings[index] - headings[index-1])
        result[index] = (delta + 180.0) % 360.0 - 180.0
    return result


def interval_turn_angles(points_xy: list[tuple[float, float]], lookahead_segments: int) -> list[float]:
    if lookahead_segments < 1:
        raise ValueError("lookahead must be at least one segment")
    turns = signed_vertex_turns(points_xy)
    count = len(points_xy) - 1
    demand = []
    for interval in range(count):
        ahead = sum(turns[interval+1:min(len(turns)-1, interval+1+lookahead_segments)])
        behind = sum(turns[max(1, interval-lookahead_segments+1):interval+1])
        demand.append(max(abs(ahead), 0.6*abs(behind)))
    return demand


def _linear_value(times, values, time):
    if time >= times[-1]:
        return values[-1]
    index = max(0, bisect_right(times, time)-1)
    ratio = (time-times[index])/(times[index+1]-times[index])
    return values[index] + ratio*(values[index+1]-values[index])


def sample_inertial_headings(source_times, source_headings, duration: float,
                             sigma_seconds: float, step: float = 0.5):
    times = [float(x) for x in source_times]
    headings = unwrap_headings(source_headings)
    if len(times) != len(headings) or len(times) < 2 or any(b <= a for a,b in zip(times,times[1:])):
        raise ValueError("heading times must be matching and strictly increasing")
    if duration <= 0 or sigma_seconds <= 0 or step <= 0:
        raise ValueError("duration, sigma and step must be positive")
    count = math.ceil(duration/step)
    actual_step = duration/count
    grid = [index*actual_step for index in range(count+1)]
    desired = [_linear_value(times, headings, time) for time in grid]
    winding = headings[-1]-headings[0]
    unique = desired[:-1]
    radius = max(1, math.ceil(3*sigma_seconds/actual_step))
    weights = [math.exp(-0.5*((offset*actual_step)/sigma_seconds)**2)
               for offset in range(-radius, radius+1)]
    normalizer = sum(weights)
    filtered = []
    for index in range(count):
        total = 0.0
        for offset, weight in zip(range(-radius, radius+1), weights):
            cycle, wrapped = divmod(index+offset, count)
            total += weight*(unique[wrapped]+cycle*winding)
        filtered.append(total/normalizer)
    filtered.append(filtered[0]+winding)
    return [LinearHeadingKey(time, value) for time,value in zip(grid,filtered)]


def build_time_map(old_times, points_xy, class_time_multiplier: float,
                   lookahead_segments: int = 1, minimum_turn_speed: float = 2/3):
    old = tuple(float(value) for value in old_times)
    if len(old) != len(points_xy):
        raise ValueError("time and point counts differ")
    if any(right <= left for left, right in zip(old, old[1:])):
        raise ValueError("route times must be strictly increasing")
    if class_time_multiplier <= 0.0:
        raise ValueError("class time multiplier must be positive")
    if lookahead_segments < 1:
        raise ValueError("lookahead must be at least one segment")
    if not 0.0 < minimum_turn_speed <= 1.0:
        raise ValueError("minimum turn speed must be in (0, 1]")
    angles = vertex_angles(list(points_xy))
    demands = interval_turn_angles(list(points_xy), lookahead_segments)
    strengths = []
    speeds = []
    for angle in demands:
        x = min(abs(angle)/90.0, 1.0)
        strength = x*x*(3.0-2.0*x)
        strengths.append(strength)
        speeds.append(1.0-(1.0-minimum_turn_speed)*strength)
    mapped = [old[0]]
    for index, speed in enumerate(speeds):
        duration = old[index + 1] - old[index]
        mapped.append(mapped[-1] + duration * class_time_multiplier / speed)
    stats = RouteTimingStats(max(angles), max(strengths), old[-1] - old[0], mapped[-1] - mapped[0], tuple(speeds))
    return TimeMap(old, tuple(mapped)), stats
