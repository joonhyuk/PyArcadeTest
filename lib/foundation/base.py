"""
base feature codes
joonhyuk@me.com
"""
import os, sys, json
from random import random
from enum import Enum
from typing import Iterable

# from config import *
from lib.foundation.vector import Vector
from lib.foundation.clock import *

# from lib.foundation.clock import *


class EnumVector(Vector, Enum):
    __class__ = Vector
    
    def __repr__(self) -> Vector:
        return self.value


def get_path(path):
    """return proper path for packaging platform"""
    if sys.platform == 'darwin': return path
    if getattr(sys, 'frozen', False):
        # running in bundle
        return os.path.join(sys._MEIPASS, path)
    else:
        return path

def get_iter(arg, return_type:type = tuple) -> Iterable:
    """return iterable(default : tuple)"""
    if isinstance(arg, str) or not isinstance(arg, Iterable):
        if return_type is tuple:
            return (arg, )
        if return_type is list:
            return [arg]
    if isinstance(arg, Iterable):
        return arg
    
def finterp_to(current:float, 
               target:float, 
               delta_time:float, 
               speed:float = 1.0, 
               precision:float = 0.001):
    if speed <= 0: return target
    delta = target - current
    if abs(delta) < precision: return target
    return current + delta * clamp(delta_time * speed, 0, 1)

def vinterp_to(current:Vector,
               target:Vector,
               delta_time:float, 
               speed:float = 1.0, 
               precision:float = 0.001):
    if speed <= 0: return target
    delta = target - current
    if delta.norm() < precision: return target
    return current + delta * clamp(delta_time * speed, 0, 1)

def rinterp_to(current:float, 
               target:float,
               delta_time:float, 
               speed:float = 1.0,
               precision:float = 0.001):
    '''rotation angle interp. in degrees'''
    delta = get_shortest_angle(current, target)
    if abs(delta) < precision: return target
    a = delta * clamp(delta_time * speed, 0, 1)
    if abs(a) > 180 * delta_time:
        if a < 0: a = -180 * delta_time
        else: a = 180 * delta_time
    return current + a

def get_shortest_angle(start:float,
                       end:float):
    return ((end - start) + 180) % 360 - 180

def get_positive_angle(degrees:float):
    '''convert angle in degrees to 0 <= x < 360'''
    degrees = get_shortest_angle(0, degrees)
    if degrees < 0: degrees += 360
    return degrees

def clamp(value, in_min, in_max):
    return min(in_max, max(in_min, value))

def clamp_abs(value, in_min, in_max):
    result = min(abs(in_max), max(abs(in_min), abs(value)))
    if value < 0 : result *= -1
    return result

def map_range(value, in_min, in_max, out_min, out_max, clamped = False):
    if clamped: value = clamp(value, in_min, in_max)
    return ((value - in_min) / (in_max - in_min)) * (out_max - out_min) + out_min

def map_range_abs(value, in_min, in_max, out_min, out_max, clamped = False):
    if clamped: value = clamp_abs(value, in_min, in_max)
    result = map_range(abs(value), in_min, in_max, out_min, out_max)
    if value < 0: result *= -1
    return result

def map_range_attenuation(value, in_min, in_max, out_start, out_min, out_max):
    ''' need to be revised '''
    if value < in_min:
        return map_range(value, 0, in_min, out_start, out_min)
    return map_range(value, in_min, in_max, out_min, out_max)

def load_json(filepath:str) -> dict:
    with open(get_path(filepath), 'r') as json_file:
        return json.load(json_file)

def save_json(filepath:str, json_data) -> None:
    with open(get_path(filepath), 'w') as json_file:
        json.dump(json_data, json_file, indent = 4)

def flip_coin(prob = 0.5) -> bool:
    return random() <= prob

def get_from_dict(dict:dict, keyword:str, default:... = None):
    if keyword in dict:
        return dict[keyword]
    return default

if __name__ != "__main__":
    print("include", __name__, ":", __file__)
