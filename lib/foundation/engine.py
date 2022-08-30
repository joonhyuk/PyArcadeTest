"""
framework wrapper for audio / video / control
might be coupled with base framwork(i.e. arcade, pygame, ...)
joonhyuk@me.com
"""
from __future__ import annotations

import os
import PIL.Image
import PIL.ImageOps
import PIL.ImageDraw

from dataclasses import dataclass
from typing import Union

import arcade
import arcade.key as keys
import arcade.color as colors

from lib.foundation.base import *
from lib.foundation.clock import *
from lib.foundation.physics import *
from lib.foundation.utils import *

from config.engine import *


class DebugTextLayer(dict, metaclass=SingletonType):
    '''
    use text_obj property to access text attributes
    
    bgcolor not working now
    
    '''
    def __init__(self, 
                 font_name = 'Kenney Mini Square', 
                 font_size = 10, 
                 color = (255,255,255,128),
                 bgcolor = None, 
                 topleft_position:Vector = Vector.diagonal(10) 
                 ):
        self.content = ''
        self._position = topleft_position
    
        self.font_name = font_name
        self.font_size = font_size
        self.color = color
        self.bgcolor = bgcolor
        self.text:arcade.Text = None
        self.width = CONFIG.screen_size.x
        
        self.setup()
    
    def setup(self):
        self.width = CONFIG.screen_size.x
        position = Vector(self._position.x, CONFIG.screen_size.y - self._position.y)
        # position.y = CONFIG.screen_size.y - position.y
        self.text = arcade.Text('', *position, self.color, self.font_size, 
                                font_name=self.font_name, 
                                width = self.width, 
                                anchor_y = 'top', 
                                multiline=True)
    
    def draw(self):
        text = ''
        for k, v in self.items():
            text += ' : '.join((k, str(v)))
            text += '\n'
        self.text.value = text
        self.text.draw()
    
    def _set_topleft_position(self, position:Vector):
        self._position = position
        self.setup()
    
    def _get_topleft_position(self):
        return self._position
    
    def perf_start(self, name:str = 'foo'):
        self[name] = CLOCK.perf
    
    def perf_end(self, name:str = 'foo'):
        self[name] = f'{round((CLOCK.perf - self[name]) * 1000,2)} ms'
    
    def perf_check(self, name:str = 'foo'):
        ''' kinda toggle function '''
        if name in self:
            if isinstance(self[name], float): return self.perf_end(name)
        return self.perf_start(name)
    
    def timer_start(self, name:str = 'foo'):
        self[name] = round(CLOCK.timer_start(name),2)
        
    
    def timer_end(self, name:str = 'foo', remain_time:float = 1.0):
        self[name] = round(CLOCK.timer_remove(name),2)
        self.remove_item(name, remain_time)
    
    def show_timer(self, name:str = 'foo'):
        if name not in CLOCK.timers: return None
        self[name] = round(CLOCK.timer_get(name),2)
    
    def remove_item(self, name:str = 'foo', delay:float = 0.0):
        
        def _remove(name:str):
            if name in self: self.pop(name)
        
        if not delay: _remove(name)
        else:
            CLOCK.reserve_exec(delay, self.remove_item, name, 0.0)
    
    position = property(_get_topleft_position, _set_topleft_position)
    ''' topleft position of text box '''


@dataclass
class Environment(metaclass = SingletonType):
    ''' I/O for game
    
    - 디스플레이 정보
        - 렌더링 배율
    - 현재 뷰포트 중앙의 절대 좌표
    - 이동 조작, 카메라 조작
    - 게임패드 입력 raw
    - 마우스 입력 raw
        - 뷰포트 내 상대좌표
        - 월드상의 절대 좌표
    
    (나중에 Window 클래스에 통합시켜버릴 수도 있음)
    '''
    
    delta_time:float = 0.0
    physics_engine:PhysicsEngine = None
    window:App = None
    
    abs_screen_center:Vector = Vector()
    render_scale:float = 1.0
    mouse_screen_position:Vector = Vector()
    gamepad:arcade.joysticks.Joystick = None
    input_move:Vector = Vector()
    key = arcade.key
    key_inputs = []
    debug_text:DebugTextLayer = None
    
    last_abs_pos_mouse_lb_pressed:Vector = vectors.zero
    last_abs_pos_mouse_lb_released:Vector = vectors.zero
    last_mouse_lb_hold_time = 0.0
    
    window_shortside = None
    window_longside = None
    
    def __init__(self) -> None:
        self.set_gamepad()
    
    def set_gamepad(self):
        ''' 게임패드 접속/해제 대응 필요 '''
        self.gamepad = self.get_input_device()
    
    def get_input_device(self, id:int = 0):
        joysticks = arcade.get_joysticks()
        if joysticks:
            gamepad = joysticks[id]
            gamepad.open()
            gamepad.push_handlers(self)
            print(f'Gamepad[{id}] attached')
            return gamepad
        return None
    
    def set_screen(self, window:App):
        ''' should be called after resizing, fullscreen, etc. '''
        self.window = window
        window_x = window.get_size()[0]
        window_y = window.get_size()[1]
        self.window_shortside = min(window_x, window_y)
        self.window_longside = max(window_x, window_y)
        
        self.render_scale = window.get_framebuffer_size()[0] / self.window_longside
    
    def on_key_press(self, key:int, modifiers:int):
        self.key_inputs.append(key)
        # self.key_inputs.append(modifiers)
    
    def on_key_release(self, key:int, modifiers:int):
        self.key_inputs.remove(key)
        # self.key_inputs.remove(modifiers)
    
    
    @property
    def lstick(self) -> Vector:
        ''' returns raw info of left stick (-1, -1) ~ (1, 1) '''
        if not self.gamepad: return None
        x = map_range_abs(self.gamepad.x, CONFIG.gamepad_deadzone_lstick, 1, 0, 1, True)
        y = map_range_abs(self.gamepad.y, CONFIG.gamepad_deadzone_lstick, 1, 0, 1, True) * -1
        return Vector(x, y)
    
    @property
    def rstick(self) -> Vector:
        ''' returns raw info of left stick (-1, -1) ~ (1, 1) '''
        if not self.gamepad: return None
        x = map_range_abs(self.gamepad.rx, CONFIG.gamepad_deadzone_rstick, 1, 0, 1, True)
        y = map_range_abs(self.gamepad.ry, CONFIG.gamepad_deadzone_rstick, 1, 0, 1, True) * -1
        return Vector(x, y)
    
    def _get_move_input(self):
        if self.gamepad:
            return self.lstick
        else:
            return self.input_move.clamp_length(1) * (0.5 if self.window.lctrl_applied else 1)

    move_input:Vector = property(_get_move_input)
    ''' returns movement direction vector (-1, -1) ~ (1, 1) '''
    
    def _get_direction_input(self):
        if self.gamepad:
            if self.rstick.length > 0.5:
                return (self.rstick.unit * CONFIG.screen_size.y / 2 + self.abs_screen_center) * self.render_scale
        else:
            return self.abs_cursor_position
    
    direction_input:Vector = property(_get_direction_input)
    ''' returns relative target point '''
    
    def _get_cursor_position(self) -> Vector:
        # if not self.mouse_input: return Vector()
        return self.mouse_screen_position * self.render_scale
    
    cursor_position:Vector = property(_get_cursor_position)
    ''' returns relative mouse cursor point '''
    
    def _get_abs_cursor_position(self) -> Vector:
        return self.mouse_screen_position + self.abs_screen_center - CONFIG.screen_size / 2
        # return self.mouse_input + self.window.current_camera.position
    
    abs_cursor_position:Vector = property(_get_abs_cursor_position)
    ''' get absolute position in world, pointed by mouse cursor '''


class MObject(object):
    __slots__ = ('id', '_alive', '_lifetime', '_update_tick', '_spawned', 'movable')
    
    def __init__(self, **kwargs) -> None:
        self.id:str = self.get_id()
        """set id by id()"""
        self._alive:bool = True
        """object alive state. if not, should be destroyed"""
        self._lifetime:float = None
        self._update_tick:bool = True
        self._spawned = False
        """tick optimization"""
        self.movable = False
        ''' can move physically '''
        if kwargs:
            for k in kwargs:
                # setattr(self, k, kwargs[k])
                self.__setattr__(k, kwargs[k])
        
    def get_id(self) -> str:
        return str(id(self))
    
    def spawn(self, lifetime:float = None):
        
        if lifetime is not None:
            self._lifetime = lifetime
        
        if self._lifetime:
            CLOCK.timer_start(self.id)
        
        self._spawned = True
        return self
    
    def tick(self, delta_time:float) -> bool:
        """alive, ticking check\n
        if false, tick deactivated"""
        if not (self._spawned and self._update_tick and self._alive): return False
        if self._lifetime:
            if self._lifetime > CLOCK.timer_get(self.id):
                return True
            else:
                return self.destroy()
        else:
            '''additional lifecycle management could be here'''
            return True
    
    def set_update(self, switch = True):
        self._update_tick = switch
    
    def destroy(self) -> bool:
        self._alive = False
        CLOCK.timer_remove(self.id)
        self.on_destroy()
        # del self    # ????? do we need it?
        # SOUND.beep()
        return self.on_destroy()
    
    def delay_destroy(self, dt):
        print(dt)
        return self.destroy()
    
    def on_destroy(self):
        pass
    
    # def __del__(self):
    #     print('good bye')
    
    def set_kwargs(self, kwargs:dict, keyword:str, default:... = None):
        self.__dict__[keyword] = get_from_dict(kwargs, keyword, default)
    
    @property
    def remain_lifetime(self) -> float:
        if self._lifetime:
            return 1 - CLOCK.timer_get(self.id) / self._lifetime
        else: return 1
    
    @property
    def is_alive(self) -> bool:
        return self._alive


class ActorComponent(MObject):
    '''component base class'''
    __slots__ = ('_owner', )
    
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._owner = self
        # spawn = getattr(self, 'spawn', None)
        # if callable(spawn):
        #     print('spawn existence check ', spawn)
        self._spawned = True
        self.on_init()
    
    def on_init(self):
        ''' setup additional parameters '''
        pass
    
    def tick(self, delta_time:float) -> bool:
        return super().tick(delta_time)
    
    def on_register(self):
        pass
    
    def destroy(self) -> bool:
        self._spawned = False
        # self._owner.components.remove(self)
        return super().destroy()
    
    def on_destroy(self):
        pass

    def _get_owner(self):
        return self._owner or self
    
    def _set_owner(self, owner):
        self._owner = owner
    
    owner = property(_get_owner, _set_owner)


class Actor(MObject):
    ''' can have actor components '''
    __slots__ = ('tick_components', )
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.tick_components:list[ActorComponent] = []
    
    def spawn(self, lifetime: float = None):
        self.register_components()
        return super().spawn(lifetime)
    
    def register_components(self):
        
        candidate = (ActorComponent, )
        components:list[ActorComponent] = []    ### type hinting
        
        def check_component(component:Union(*candidate)):
            return isinstance(component, candidate)
        
        if hasattr(self, '__dict__'):    ### for those have only __slots__
            components.extend([c for c in self.__dict__.values() if check_component(c)])
        
        if hasattr(self, '__slots__'):
            components.extend([getattr(self, c) for c in self.__slots__ if check_component(getattr(self, c))])
        
        if components:
            for component in components:
                if hasattr(component, 'owner'): component.owner = self  ### set owner
                if hasattr(component, 'tick'): 
                    if component.tick: self.tick_components.append(component)
                    ''' to disable component tick, put `self.tick = None` into __init__() '''
                if hasattr(component, 'on_register'): component.on_register()
    
    def tick(self, delta_time: float) -> bool:
        if not super().tick(delta_time): return False
        if self.tick_components:
            for ticker in self.tick_components:
                ticker.tick(delta_time)
                # print('character_tick', delta_time)
        return True
    
    def destroy(self) -> bool:
        for component in self.tick_components:
            component.destroy()
        
        self.tick_components = []
        return super().destroy()


class BodyComponent(ActorComponent):
    __slots__ = ('sprite', 
                 '_hidden', 
                 )
    
    def __init__(self, 
                 sprite:Sprite,
                 position:Vector = None,
                 angle:float = None,
                 **kwargs) -> None:
        super().__init__(**kwargs)
        
        self.sprite:Sprite = sprite
        self._hidden:bool = False
        
        if position: self.position = position
        if angle: self.angle = angle
    
    # def on_register(self):
    #     print('body component set',self)
    
    def get_ref(self):
        return self.sprite
    
    # def __del__(self):
        # print('goodbye from body')
    
    def spawn(self, spawn_to:ObjectLayer, position:Vector = None, angle:float = None):
        self.sprite.owner = self.owner
        
        if position is not None: 
            self.position = position
        if angle is not None:
            self.angle = angle
        
        spawn_to.add(self)
        return super().spawn()
    
    def draw(self, *args, **kwargs):
        self.sprite.draw(*args, **kwargs)
    
    def _hide(self, switch:bool = None) -> bool:
        ''' hide sprite and physics if exist and return switch '''
        if switch is None: switch = not self.hidden
        self.visibility = not switch
        return switch
    
    def _get_hidden(self) -> bool:
        return self._hidden
    
    def _set_hidden(self, switch:bool = None):
        ''' hide sprite and physics body '''
        self._hidden = self._hide(switch)
    
    hidden:bool = property(_get_hidden, _set_hidden)
    
    
    def destroy(self) -> bool:
        self.sprite.remove_from_sprite_lists()
        return super().destroy()
    
    def _set_owner(self, owner):
        super()._set_owner(owner)
        self.sprite.owner = self.owner
    
    owner = property(ActorComponent._get_owner, _set_owner)
    
    def _get_visibility(self) -> bool:
        return self.sprite.visible
    
    def _set_visibility(self, switch:bool = None):
        if switch is None: switch = not self.sprite.visible
        self.sprite.visible = switch
    
    visibility:bool = property(_get_visibility, _set_visibility)
    ''' set None to toggle visibility '''
    
    def _get_position(self):
        return self.get_ref().position
    
    def _set_position(self, position):
        self.get_ref().position = position
    
    position:Vector = property(_get_position, _set_position)
    
    def _get_angle(self) -> float:
        return self.get_ref().angle
    
    def _set_angle(self, angle:float = 0.0):
        self.get_ref().angle = angle
    
    angle:float = property(_get_angle, _set_angle)
    
    def _get_veloticy(self) -> Vector:
        return self.get_ref().velocity
    
    def _set_velocity(self, velocity):
        self.get_ref().velocity = velocity
    
    velocity:Vector = property(_get_veloticy, _set_velocity)
    
    @property
    def speed(self) -> float :
        ''' different from physics or sprite 
        
        :physics = per sec
        :sprite = per tick
        '''
        return self.velocity.length
    
    @property
    def forward_vector(self) -> Vector:
        return Vector.directional(self.angle)
    
    @property
    def size(self) -> Vector:
        return Vector(self.sprite.width, self.sprite.height)
    
    @property
    def layers(self) -> list[ObjectLayer]:
        ''' Layers(ObjectLayer list) where this body is '''
        return self.sprite.sprite_lists



class ControllerComponent(ActorComponent):
    #WIP
    """
    액터 컴포넌트로 만들지 않아도 되지 않을까.
    어차피 컨트롤러니까 앱 혹은 ENV에 등록해두고... 즉, 액터의 owner가 되는거지.
    
    입력(조작) 혹은 명령(조건에 따른)에 의해 액터의 의지인양 움직이는 것.
    (리액션은 컨트롤러가 책임지지 않음.)
    
    PlayerController(조작에 의한 직접 행동제어)
    AIController(조건에 의한 자동 행동제어)
    ObjectController(조작에 의한 간접 행동제어)
    
    행동의 주체가 되는 Actor는 '행동'을 가져야 한다.
    '행동'은 이동과 액션, 인터렉션으로 구분된다.
    이동은 MovementHandler를 통하거나 직접 스프라이트를 setpos하는 것.
    액션은 다양.
    
    view의 on_input에 app의 player_controller의 on_input이 함께 실행되어 필요한 것 들을 한다.
    매 업데이트 틱(캐릭터 틱)에 tick이 실행되어 부가적인 작업들을 한다?
    
    
    """
    ''' actor component which control actor.
    get env.inputs, set movement, action
    movement <- body
    action <- actor, body
    
    - handles inputs maybe.
    '''
    
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
    
    def tick(self, delta_time: float) -> bool:
        if not super().tick(delta_time): return False
        return True
    
    def possess(self, actor:Actor):
        # if actor is not valid: return False
        self.owner = actor
    
    def on_key_press(self, key: int, modifiers: int):
        pass
    
    def on_key_release(self, key: int, modifiers: int):
        pass
    
    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int):
        pass
    
    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int):
        pass
    
    def on_mouse_release(self, x: int, y: int, button: int, modifiers: int):
        pass
    
    def on_mouse_drag(self, x: int, y: int, dx: int, dy: int, buttons: int, modifiers: int):
        pass
    
    def on_mouse_scroll(self, x: int, y: int, scroll_x: int, scroll_y: int):
        pass
    
    @property
    def is_alive(self):
        if not self.owner: return False
        return self.owner.is_alive


class App(arcade.Window):
    
    ### class variables : are they needed?
    lshift_applied = False
    lctrl_applied = False
    current_camera:arcade.Camera = None
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        ENV.physics_engine = PhysicsEngine()
    
    def on_show(self):
        # print('window_show')
        ENV.set_screen(self)
        # self.direction_input = Vector()
        # self.get_input_device()
        if ENV.gamepad: self.set_mouse_visible(False)
        ENV.debug_text = DebugTextLayer()
        ENV.debug_text['fps'] = 0
        
    def on_key_press(self, key: int, modifiers: int):
        # ENV.key_inputs.append(key)
        if key in (keys.W, keys.UP): ENV.input_move += vectors.up
        if key in (keys.S, keys.DOWN): ENV.input_move += vectors.down
        if key in (keys.A, keys.LEFT): ENV.input_move += vectors.left
        if key in (keys.D, keys.RIGHT): ENV.input_move += vectors.right
        if key == keys.LSHIFT: self.lshift_applied = True
        if key == keys.LCTRL: self.lctrl_applied = True
        
        if key == keys.F2: CONFIG.debug_draw = not CONFIG.debug_draw
        
        ENV.on_key_press(key, modifiers)
        
    def on_key_release(self, key: int, modifiers: int):
        # ENV.key_inputs.remove(key)
        if key in (keys.W, keys.UP): ENV.input_move -= vectors.up
        if key in (keys.S, keys.DOWN): ENV.input_move -= vectors.down
        if key in (keys.A, keys.LEFT): ENV.input_move -= vectors.left
        if key in (keys.D, keys.RIGHT): ENV.input_move -= vectors.right
        if key == keys.LSHIFT: self.lshift_applied = False
        if key == keys.LCTRL: self.lctrl_applied = False

        ENV.on_key_release(key, modifiers)
        
    def on_update(self, delta_time: float):
        ENV.delta_time = delta_time
        
        CLOCK.fps_current = 1 / delta_time
        ENV.debug_text['fps'] = CLOCK.fps_average

        ENV.debug_text.perf_check('update_physics')
        ENV.physics_engine.step()
        ENV.debug_text.perf_check('update_physics')
        
    def on_draw(self):
        # print('window_draw')
        ENV.debug_text.draw()
        pass
    
    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int):
        ENV.mouse_screen_position = Vector(x, y)
    
    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int):
        if button == arcade.MOUSE_BUTTON_LEFT:
            ENV.last_abs_pos_mouse_lb_pressed = ENV.abs_cursor_position
    
    def on_mouse_release(self, x: int, y: int, button: int, modifiers: int):
        if button == arcade.MOUSE_BUTTON_LEFT:
            ENV.last_abs_pos_mouse_lb_released = ENV.abs_cursor_position

    def run(self):
        arcade.run()
    
    @property
    def render_ratio(self):
        return self.get_framebuffer_size()[0] / self.get_size()[0]
    
    @property
    def cursor_position(self) -> Vector:
        return ENV.mouse_screen_position * ENV.render_scale


class View(arcade.View):
    
    def __init__(self, window: App = None):
        super().__init__(window)
        self.fade_out = 0.0
        self.fade_in = 0.0
        self.fade_alpha = 1

    def draw_tint(self, alpha = 0.0, color = (0, 0, 0)):
        arcade.draw_rectangle_filled(self.window.width / 2, self.window.height / 2,
                                     self.window.width, self.window.height,
                                     (*color, alpha * 255))
    
    def draw_contents(self):
        pass
    
    def on_draw(self):
        self.clear()
        self.draw_contents()
        if self.fade_in > 0 or self.fade_out > 0:
            # self.fade_alpha = finterp_to(self.fade_alpha, )
            self.draw_tint()
    
    def go_next(self, next_screen:arcade.View):
        if self.fade_out:
            pass
        
    def go_after_fade_out(self, next_screen:arcade.View):
        pass
    
    def on_update(self, delta_time: float):
        ENV.delta_time = delta_time


class Sprite(arcade.Sprite):
    
    __slots__ = ('owner',
                 'collide_with_radius',
                 )
    def __init__(self, 
                 filename: str = None, 
                 scale: float = 1, 
                 image_x: float = 0, image_y: float = 0, image_width: float = 0, image_height: float = 0, 
                 center_x: float = 0, center_y: float = 0, 
                 repeat_count_x: int = 1, repeat_count_y: int = 1, 
                 flipped_horizontally: bool = False, flipped_vertically: bool = False, flipped_diagonally: bool = False, 
                 hit_box_algorithm: str = "Simple", hit_box_detail: float = 4.5, 
                 texture: arcade.Texture = None, 
                 angle: float = 0):
        self.owner = None
        super().__init__(filename, scale, image_x, image_y, image_width, image_height, center_x, center_y, repeat_count_x, repeat_count_y, flipped_horizontally, flipped_vertically, flipped_diagonally, hit_box_algorithm, hit_box_detail, texture, angle)
        self.collides_with_radius = False

    def scheduled_remove_from_sprite_lists(self, dt):
        # print('REMOVING!')
        return super().remove_from_sprite_lists()


class SpriteCircle(arcade.SpriteCircle):
    def __init__(self, 
                 radius: int = 16, 
                 color: colors = colors.ALLOY_ORANGE, 
                 soft: bool = False):
        self.owner = None
        super().__init__(radius, color, soft)

    def scheduled_remove_from_sprite_lists(self, dt):
        # print('REMOVING!')
        return super().remove_from_sprite_lists()


class Capsule(Sprite):
    """ LEGACY : WILL BE DEPRECATED """
    
    def __init__(self, radius: int):
        super().__init__()
        
        diameter = radius * 2
        cache_name = arcade.sprite._build_cache_name("circle_texture", diameter, 255, 255, 255, 64, 0)
        texture = None
        
        # texture = make_circle_texture(diameter, color, name=cache_name)
        
        img = PIL.Image.new('RGBA', (diameter, diameter), (0,0,0,0))
        draw = PIL.ImageDraw.Draw(img)
        draw.ellipse((0, 0, diameter - 1, diameter - 1), fill=(255,255,255,64))
        texture = arcade.Texture(cache_name, img, 'Detailed', 1.0)
        
        arcade.texture.load_texture.texture_cache[cache_name] = texture
        
        self.texture = texture
        self._points = self.texture.hit_box_points
        self.collision_radius = radius
        self.collides_with_radius = True
        
    def draw_hit_box(self, color: colors = ..., line_thickness: float = 1):
        return debug_draw_circle(self.position, self.collision_radius, color, line_thickness)


class ObjectLayer(arcade.SpriteList):
    """ extended spritelist with actor, body """
    def __init__(self, 
                 physics_instance:PhysicsEngine = None,
                 use_spatial_hash=None, spatial_hash_cell_size=128, is_static=False, atlas: arcade.TextureAtlas = None, capacity: int = 100, lazy: bool = False, visible: bool = True):
        super().__init__(use_spatial_hash, spatial_hash_cell_size, is_static, atlas, capacity, lazy, visible)
        self.physics_instance = physics_instance
        
    def add(self, obj:Union[Actor, BodyComponent, Sprite, SpriteCircle]):
        sprite:Sprite = None
        body:BodyComponent = None
        if isinstance(obj, Actor):
            sprite = obj.body.sprite
            body = obj.body
        elif isinstance(obj, (BodyComponent, )):
            sprite = obj.sprite
            body = obj
        elif isinstance(obj, (Sprite, SpriteCircle)):
            sprite = obj
        else: raise Exception('ObjectLayer only accept Sprite, Body, Actor')
        
        if sprite:
            self.append(sprite)
        
        if self.physics_instance:
            if body:
                if body.physics:
                    self.physics_instance.add_object(sprite, body.physics.body, body.physics.shape)
                    self.physics_instance.add_to_space(sprite)
                    
    def remove(self, obj:Union[Actor, BodyComponent, Sprite, SpriteCircle]):
        sprite:Sprite = None
        # body:SimpleBody = None
        if isinstance(obj, Actor):
            sprite = obj.body.sprite
            # body = obj.body
        elif isinstance(obj, BodyComponent):
            sprite = obj.sprite
            # body = obj
        elif isinstance(obj, (Sprite, SpriteCircle)):
            sprite = obj
        else: raise Exception('ObjectLayer only accept Sprite, Body, Actor')
        
        ''' 
        Because arcade spritelist remove method automatically remove body from physics,
        we don't need it
        
        if body:
           if body.physics:
               self.physics_instance.remove_sprite(sprite)
        '''
        return super().remove(sprite)
    
    def step(self, delta_time:float = 1/60, sync:bool = True):
        ''' Don't use it usually. For better performance, call directly from physics instance '''
        self.physics_instance.step(delta_time=delta_time, resync_objects=sync)


class Camera(arcade.Camera):
    
    def __init__(self, viewport_width: int = 0, viewport_height: int = 0, window: Optional["arcade.Window"] = None, 
                 max_lag_distance:float = None,
                 ):
        super().__init__(viewport_width, viewport_height, window)
        self.max_lag_distance:float = max_lag_distance
    
    def update(self):
        # last_tick_pos = self.position
        super().update()
        
        if self.max_lag_distance:
            distv = self.position - self.goal_position
            if distv.mag > self.max_lag_distance:
                # print(distv.mag)
                self.position = self.goal_position + distv.limit(self.max_lag_distance)
                # self.position.lerp(self.goal_position + distv.limit(self.max_lag_distance * 0.75), 0.9)


class GLTexture(arcade.Texture):
    pass


class SoundBank:
    def __init__(self, path:str) -> None:
        self.path:str = path
        self.filenames:list = []
        self.sounds:dict[str, arcade.Sound] = {}
        self.mute:bool = False
        self.volume_master:float = 0.5
        print('SOUND initialized')
        self.load()
        
    def load(self, path:str = None):
        sfxpath = path or self.path
        try:
            self.filenames = os.listdir(get_path(sfxpath))
        except FileNotFoundError:
            print(f'no sound file found on "{sfxpath}"')
            return None
        
        if not self.filenames:
            print(f'no sound file found on "{sfxpath}"')
            return None
        
        for filename in self.filenames:
            namespaces = filename.split('.')
            if namespaces[1] in ('wav', 'ogg', 'mp3'):
                self.sounds[namespaces[0]] = arcade.Sound(get_path(sfxpath + filename))
        return self.sounds
    
    def play(self, name:str, volume:float = 0.2, repeat:int = 1) -> float:
        if self.mute: return None
        if name not in self.sounds:
            print(f'no sound file "{name}"')
            return None
        
        sound = self.sounds[name]
        # self.sounds[name].set_volume(volume)
        sound.play(volume)
        return sound.get_length()
    
    def set_mute(self, switch:bool = None):
        if switch is None: switch = not self.mute
        self.mute = switch
        return self.mute
    
    def set_volume_master(self, amount:float):
        self.volume_master = amount
        
    def beep(self):
        self.play('beep', 1.0)


if __name__ != "__main__":
    print("include", __name__, ":", __file__)
    SOUND = SoundBank(SFX_PATH)
    ENV = Environment()
    
    # DEBUG = DebugTextLayer()