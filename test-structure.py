from __future__ import annotations

from lib.foundation import *


class Member(GameObject):
    pass

class Yuji(Member):
    pass

class Biden(GameObject):
    
    __slots__ = 'hail', 
    
    # def __init__(self, **kwargs) -> None:
    #     super().__init__(**kwargs)
    #     self.hail = GameObject()
    
    def setup(self, **kwargs) -> None:
        self.hail = GameObject()
    
    # def get_slots(self):
    #     if not hasattr(super(), 'get_slots') : return self.__slots__
    #     return super().get_slots() + self.__slots__

class Foo(Biden):
    
    # __slots__ = 'member', 'yuji', 'biden', 'hello'
    
    def setup(self, **kwargs) -> None:
        self.member = Member()
        self.yuji = Yuji()
        self.biden = Biden()
        self.hello = get_from_dict(kwargs, 'hello')
        return super().setup(**kwargs)
    
    # def get_slots(self):
    #     if not hasattr(super(), 'get_slots') : return self.__slots__
    #     return super().get_slots() + self.__slots__


class Bar:
    
    def __init__(self) -> None:
        self.bar = 1
        
b = Bar()
s = get_slots(b)
for a in s:
    print(a)

f = Foo(hello = 'world')
print(f.hail.spawnned)
f.spawn()
print(f.hail.spawnned)

import time

start = time.perf_counter()

for _ in range(10000):
    a = Foo().spawn()
    # a = f.__slots__ + ('hail', 'to', 'the')
    
print('time', time.perf_counter() - start)