# from lib.foundation import *
from lib.escape import *
from config import *


VERSION = Version()

SPRITE_SCALING_PLAYER = 0.5
PLAYER_MOVE_FORCE = 4000
PLAYER_ATTACK_RANGE = 500
PHYSICS_TEST_DEBRIS_NUM = 200
PHYSICS_TEST_DEBRIS_RADIUS = 9


class PhysicsTestView(View):
    
    def __init__(self, window: App = None):
        super().__init__(window)
        
        self.field_layer = ObjectLayer()
        self.wall_layer = ObjectLayer(ENV.physics_engine)
        self.debris_layer = ObjectLayer(ENV.physics_engine)
        self.character_layer = ObjectLayer(ENV.physics_engine)
        self.fx_layer = ObjectLayer(ENV.physics_engine)
        
        self.test_layer = ObjectLayer(ENV.physics_engine)
        
        self.player:EscapePlayer = None
        self.camera:CameraHandler = None
        self.camera_gui = Camera(*CONFIG.screen_size)
        
        self._tmp = None
        
    def on_show(self):
        arcade.set_background_color(arcade.csscolor.DARK_SLATE_BLUE)
        
    def setup(self):
        start_loading_time = CLOCK.get_perf()
        
        ENV.physics_engine.damping = 0.01
        
        self.player = EscapePlayer()
        self.player.spawn(self.character_layer, Vector(100, 100))
        
        self.player.body.sprite.pymunk.max_velocity = CONFIG.terminal_speed
        # self.player.body.physics.shape.friction = 1.0
        # self.player.body.sprite.pymunk.gravity = (0,980)
        # self.player.body.sprite.pymunk.damping = 0.01
        self.camera = self.player.camera
        
        self._setup_field(self.field_layer)
        
        self._setup_walls_onecue(self.wall_layer)
        
        self._setup_debris_onecue(self.debris_layer)
        
        ### test new method!
        test_simplebody = StaticBody(SpriteCircle(32), 
                                     physics_shape = physics_types.circle,
                                     position=Vector(300,300),
                                     collision_type=collision.none,
                                     elasticity=1.0
                                     )
        # test_simplebody.position = vectors.zero
        test_simpleactor = StaticObject(test_simplebody).spawn(self.test_layer)
        # test_simpleactor.position = vectors.zero
        # test_simpleactor.spawn(self.test_layer, Vector(300,300))
        # test_simpleactor.body.sprite.remove_from_sprite_lists()
        
        ### DynamicObject.spawn test
        box_body = DynamicBody(Sprite(":resources:images/tiles/grassCenter.png", 1.5),
                               mass = 10, friction=1.0,
                               collision_type=collision.debris,
                               physics_shape=physics_types.box,
                               )
        # box = DynamicObject(box_body)
        box = BigBox(box_body)
        box.spawn(self.debris_layer, CONFIG.screen_size / 2)
        ### DynamicObject.spawn test
        
        def begin_player_hit_wall(player, wall, arbiter, space, data):
            print('begin_hit')
            return True
        def pre_player_hit_wall(player, wall, arbiter, space, data):
            print('pre_hit')
            return True
        def post_player_hit_wall(player, wall, arbiter, space, data):
            print('post_hit')
        def seperate_player_hit_wall(player, wall, arbiter, space, data):
            print('seperate_hit')
        
        # ENV.physics_engine.add_collision_handler(collision.character, collision.wall, 
        #                                           begin_handler=begin_player_hit_wall, 
        #                                           pre_handler=pre_player_hit_wall,
        #                                           separate_handler=seperate_player_hit_wall,
        #                                           post_handler=post_player_hit_wall)

        print(f'INITIAL LOADING TIME : {round(CLOCK.perf - start_loading_time, 2)} sec')
        
    def _setup_debris_onecue(self, layer:ObjectLayer):
        ### DynamicBody only test
        for _ in range(PHYSICS_TEST_DEBRIS_NUM):
            debri = DynamicBody(SpriteCircle(PHYSICS_TEST_DEBRIS_RADIUS, (255,255,0,96)),
                                             mass = 0.5, elasticity = 0.2, friction=1.0,
                                             collision_type = collision.debris)
            placed = False
            while not placed:
                debri.position = random.randrange(CONFIG.screen_size.x), random.randrange(CONFIG.screen_size.y)
                if not arcade.check_for_collision_with_lists(debri.sprite, [self.wall_layer, layer]):
                    debri.spawn(layer)
                    placed = True
    
    def _setup_walls_onecue(self, layer:ObjectLayer):
        ### StaticBody only test
        for x in range(0, CONFIG.screen_size.x + 1, 32):
            wall = StaticBody(Sprite(":resources:images/tiles/grassCenter.png", SPRITE_SCALING_PLAYER),
                              Vector(x, 0), 
                              elasticity=0.75,
                              spawn_to = layer)
            wall = StaticBody(Sprite(":resources:images/tiles/grassCenter.png", SPRITE_SCALING_PLAYER),
                              Vector(x, CONFIG.screen_size.y), 
                              elasticity=0.75,
                              spawn_to = layer)
        
        for y in range(32, CONFIG.screen_size.y, 32):
            wall = StaticBody(Sprite(":resources:images/tiles/grassCenter.png", SPRITE_SCALING_PLAYER),
                              Vector(0, y), 
                              elasticity=0.75,
                              spawn_to = layer)
            wall = StaticBody(Sprite(":resources:images/tiles/grassCenter.png", SPRITE_SCALING_PLAYER),
                              Vector(CONFIG.screen_size.x, y), 
                              elasticity=0.75,
                              spawn_to = layer)
        
    def _setup_field(self, layer:ObjectLayer):
        field_size = 6400
        for x in range(-field_size, field_size, 64):
            for y in range(-field_size, field_size, 64):
                ground = Sprite(':resources:images/tiles/brickTextureWhite.png', 0.5)
                ground.position = x, y
                ground.color = (30, 30, 30)
                layer.add(ground)
    
    def on_key_press(self, key: int, modifiers: int):
        # print(modifiers, keys.MOD_OPTION)
        if key == keys.G: 
            self.change_gravity(vectors.zero)
        
        if key == keys.UP and modifiers in (20, keys.MOD_ALT, keys.MOD_OPTION + 512):
            self.change_gravity(vectors.up)
        if key == keys.DOWN and modifiers in (20, keys.MOD_ALT, keys.MOD_OPTION + 512):
            self.change_gravity(vectors.down)
        if key == keys.LEFT and modifiers in (20, keys.MOD_ALT, keys.MOD_OPTION + 512):
            self.change_gravity(vectors.left)
        if key == keys.RIGHT and modifiers in (20, keys.MOD_ALT, keys.MOD_OPTION + 512):
            self.change_gravity(vectors.right)
        
        if key == keys.H: self.player.hidden = None
        
        return super().on_key_press(key, modifiers)
    
    def on_key_release(self, key: int, modifiers: int):
        
        if key == arcade.key.ESCAPE: arcade.exit()
        return super().on_key_release(key, modifiers)
    
    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int):
        ENV.last_mouse_lb_hold_time = CLOCK.perf
        ENV.debug_text.timer_start('mouse_lb_hold')
        
        self.player.test_directional_attack(distance=PLAYER_ATTACK_RANGE)

        if self._tmp: self._tmp.destroy() # works well
    
    def on_mouse_release(self, x: int, y: int, button: int, modifiers: int):
        ENV.last_mouse_lb_hold_time = CLOCK.perf - ENV.last_mouse_lb_hold_time
        ENV.debug_text.timer_end('mouse_lb_hold', 3)
        
        self._tmp = self.player.test_projectile(map_range(ENV.last_mouse_lb_hold_time, 0, 3, 800, 5000, True))
        # delay_run(2, self._tmp.destroy)
        # CLOCK.reserve_exec(2, self._tmp.destroy)
        
        # self.player.test_directional_attack(distance=PLAYER_ATTACK_RANGE)
        # self.line_of_fire_check(self.player.position, self.player.position + self.player.forward_vector * 1000, 5)
    
    def change_gravity(self, direction:Vector) -> None:
        
        if direction == vectors.zero:
            ENV.physics_engine.damping = 0.01
            ENV.physics_engine.gravity = vectors.zero
            return
        
        ENV.physics_engine.gravity = direction * GRAVITY
        ENV.physics_engine.damping = 1.0
        ENV.physics_engine.activate_objects()
        return
        
    def line_of_fire_check(self, origin:Vector, end:Vector, thickness:float = 1, muzzle_speed:float = 500):
        ''' 초고속 발사체(광학병기, 레일건) 체크용. 화학병기 발사체는 발사체를 직접 날려서 충돌체크.
        '''
        self.player.body.physics.shape.filter = pymunk.ShapeFilter(categories=0b1)
        sf = pymunk.ShapeFilter(mask = pymunk.ShapeFilter.ALL_MASKS()^0b1)
        query = ENV.physics_engine.space.segment_query(origin, end, thickness / 2, sf)
        query_first = ENV.physics_engine.space.segment_query_first(origin, end, thickness / 2, sf)
        # if query:
        #     for sq in query:
        #         shape = sq.shape
        #         location = sq.point
        #         normal = sq.normal
        #         c1 = SpriteCircle(5, color=(255, 96, 0, 192))
        #         c1.position = location
        #         self.debris_layer.add(c1)
        #         schedule_once(c1.remove_from_sprite_lists, 3)
        
        if query_first:
            qb:pymunk.Body = query_first.shape.body
            iv = (end - origin).unit * muzzle_speed / 2
            iv -= query_first.normal * muzzle_speed / 2
            qb.apply_impulse_at_world_point(iv, query_first.point)
            add_sprite_timeout(SpriteCircle(5, (255, 64, 0, 128)), query_first.point, self.debris_layer, 3)
    
    def on_draw(self):
        ENV.debug_text.perf_check('on_draw')
        super().on_draw()
        # self.clear()
        
        self.camera.use()
        self.field_layer.draw()
        self.wall_layer.draw()
        self.debris_layer.draw()
        
        self.character_layer.draw()
        self.fx_layer.draw()
        
        self.test_layer.draw()
        debug_draw_segment(self.player.position, self.player.position + self.player.body.velocity, color = colors.AERO_BLUE)
        debug_draw_segment(self.player.position, self.player.position + self.player.forward_vector * PLAYER_ATTACK_RANGE, colors.RED)
        # self.test_layer.__getitem__(0).draw()
        # 
        # debug_draw_segment(end = CONFIG.screen_size)
        
        self.camera_gui.use()
        
        ENV.debug_text.perf_check('on_draw')
    
    def on_update(self, delta_time: float):
        ENV.debug_text.perf_check('update_game')
        super().on_update(delta_time)
        
        self.player.tick(delta_time)
        # print(self.player.body.physics.shape.segment_query((0,0), CONFIG.screen_size))
        
        # ENV.debug_text['distance'] = rowund(self.player.position.length, 1)
        
        if ENV.physics_engine.non_static_objects:
            total = len(ENV.physics_engine.non_static_objects)
            sleeps = list(map(lambda a:a.is_sleeping, ENV.physics_engine.space.bodies)).count(True)
            ENV.debug_text['PHYSICS TOTAL/SLEEP'] = f'{total}/{sleeps}'
        
        # ENV.debug_text.perf_check('update_empty_physics')
        # for pe in self.test_physics_layers:
        #     pe.physics_instance.step(delta_time)
        # ENV.debug_text.perf_check('update_empty_physics')
        ENV.debug_text.show_timer('mouse_lb_hold')
        ENV.debug_text.perf_check('update_game')
        
        
def main():
    CLOCK.use_engine_tick = True
    game = App(*CONFIG.screen_size, 'PHYSICS ENGINE TEST')
    view = PhysicsTestView()
    view.setup()
    game.show_view(view)
    arcade.run()

if __name__ == '__main__':
    main()
    