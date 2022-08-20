from lib.foundation import *
from config import *

VERSION = Version()

SPRITE_SCALING_PLAYER = 0.25
PLAYER_MOVE_FORCE = 4000

class PhysicsTestView(View):
    
    def __init__(self, window: Window = None):
        super().__init__(window)
        
        self.wall_layer = ObjectLayer()
        self.debris_layer = ObjectLayer()
        self.player:Player = None
        self.camera:CameraHandler = None
        self.camera_gui = Camera(*CONFIG.screen_size)
        
        self.physics_engine:PhysicsEngine = None
        
    def on_show(self):
        arcade.set_background_color(arcade.csscolor.DARK_SLATE_BLUE)
        
    def setup(self):
        self.physics_engine = PhysicsEngine()
        self.physics_engine.damping = 0.01
        
        self.player = Player(self.physics_engine)
        self.player.spawn(Vector(100, 100))
        self.camera = self.player.camera
        
        self._setup_walls()
        self.physics_engine.add_sprite_list(self.wall_layer, 
                                            friction = 0.0, 
                                            collision_type=collision.wall, 
                                            body_type=physics_types.static)
        
        box = arcade.Sprite(":resources:images/tiles/grassCenter.png", 1.5)
        box.center_x = CONFIG.screen_size.x // 2
        box.center_y = CONFIG.screen_size.y // 2
        self.physics_engine.add_sprite(box, 
                                       mass=10, 
                                       friction = 1.0,
                                       collision_type=collision.debris,
                                       body_type=physics_types.dynamic)
        self.debris_layer.add(box)
        
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
        
        self.physics_engine.add_collision_handler(collision.character, collision.wall, 
                                                  begin_handler=begin_player_hit_wall, 
                                                  pre_handler=pre_player_hit_wall,
                                                  separate_handler=seperate_player_hit_wall,
                                                  post_handler=post_player_hit_wall)
        
    def _setup_walls(self):
        # Set up the walls
        for x in range(0, CONFIG.screen_size.x + 1, 32):
            wall = arcade.Sprite(":resources:images/tiles/grassCenter.png",
                                 SPRITE_SCALING_PLAYER)
            wall.center_x = x
            wall.center_y = 0
            self.wall_layer.add(wall)

            wall = arcade.Sprite(":resources:images/tiles/grassCenter.png",
                                 SPRITE_SCALING_PLAYER)
            wall.center_x = x
            wall.center_y = CONFIG.screen_size.y
            self.wall_layer.add(wall)

        # Set up the walls
        for y in range(32, CONFIG.screen_size.y, 32):
            wall = arcade.Sprite(":resources:images/tiles/grassCenter.png",
                                 SPRITE_SCALING_PLAYER)
            wall.center_x = 0
            wall.center_y = y
            self.wall_layer.add(wall)

            wall = arcade.Sprite(":resources:images/tiles/grassCenter.png",
                                 SPRITE_SCALING_PLAYER)
            wall.center_x = CONFIG.screen_size.x
            wall.center_y = y
            self.wall_layer.add(wall)

    def on_key_press(self, key: int, modifiers: int):
        
        return super().on_key_press(key, modifiers)
    
    def on_key_release(self, key: int, modifiers: int):
        
        if key == arcade.key.ESCAPE: arcade.exit()
        return super().on_key_release(key, modifiers)
    
    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int):
        self.line_of_fire_check(self.player.position, ENV.abs_cursor_position, 1)
        
        
    def line_of_fire_check(self, origin:Vector, end:Vector, thickness:float = 1):
        self.player.body.physics.shape.filter = pymunk.ShapeFilter(categories=0b1)
        sf = pymunk.ShapeFilter(mask = pymunk.ShapeFilter.ALL_MASKS()^0b1)
        query = self.physics_engine.space.segment_query(origin, end, thickness / 2, sf)
        query_first = self.physics_engine.space.segment_query_first(origin, end, thickness / 2, sf)
        if query:
            for sq in query:
                shape = sq.shape
                location = sq.point
                normal = sq.normal
                c1 = SpriteCircle(5, color=(255, 96, 0, 192))
                c1.position = location
                print(location)
                self.debris_layer.add(c1)
                schedule_once(c1.remove_from_sprite_lists, 3)
        if query_first:
            qb:pymunk.Body = query_first.shape.body
            iv = (end - origin).unit * 1000
            qb.apply_impulse_at_world_point(iv, query_first.point)
    
    def on_draw(self):
        ENV.debug_text.perf_check('on_draw')
        self.clear()
        
        self.camera.use()
        self.wall_layer.draw()
        self.debris_layer.draw()
        self.player.draw()
        
        # debug_draw_segment(end = CONFIG.screen_size)
        
        self.camera_gui.use()
        ENV.debug_text.perf_check('on_draw')
        
    def on_update(self, delta_time: float):
        ENV.debug_text.perf_check('on_update')
        
        self.player.tick(delta_time)
        self.physics_engine.step()
        # print(self.player.body.physics.shape.segment_query((0,0), CONFIG.screen_size))
        
        ENV.debug_text.perf_check('on_update')
        
        
def main():
    CLOCK.use_engine_tick = True
    game = Window(*CONFIG.screen_size, 'PHYSICS ENGINE TEST')
    view = PhysicsTestView()
    view.setup()
    game.show_view(view)
    arcade.run()

if __name__ == '__main__':
    main()
    