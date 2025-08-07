import threading
import pygame.time
from src.client.client import Client
from src.client.renderer import *
from src.client.screens import Screen, TextLabel
from src.client.world_rendering import draw_cursor, draw_world, draw_world_optimized
from src.shared.combat.bullet import Bullet
from src.shared.npc.npcs import PlayerNPC
from src.shared.textures import *
from src.shared.world import World
import ctypes

# import tracemalloc
# tracemalloc.start()

# import gc
# from collections import Counter
#
# def log_memory_stats():
#     counts = Counter(type(obj).__name__ for obj in gc.get_objects())
#     print(counts.most_common(10))
#     gc.collect()
#     vec = gc.get_objects()
#     print(any(isinstance(obj, Vec2) for obj in vec))  # Should be False if no refs remain
#
#
# import objgraph
#
# def make_vec2_graph():
#     # Find the most common types
#     objgraph.show_most_common_types()
#
#     # Pick one leaked type
#     objgraph.show_backrefs(
#         objgraph.by_type('Vec2')[0],
#         max_depth=3,
#         filename='refs.png'
#     )


try:
    ctypes.windll.user32.SetProcessDPIAware()
except Exception:
    pass

current_file_directory = os.path.dirname(os.path.abspath(__file__))
def get_abs_path(path):
    # return (current_file_directory + "/" + path).replace("\\", "/").replace("//", "/")
    return path

# variables
screenWidth = INITIAL_SCREEN_WIDTH
screenHeight = INITIAL_SCREEN_HEIGHT
groundLevel = INITIAL_GROUND_LEVEL
scale = 1.0

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((INITIAL_SCREEN_WIDTH, INITIAL_SCREEN_HEIGHT), DOUBLEBUF | OPENGL)
icon = pygame.image.load(get_abs_path('assets/icon.png'))
logo = load_texture('assets/logo.png')
backup_bg = load_texture('assets/create_bg.png')
tile_bg = load_texture('assets/textures/bg_tile.png')
font = pygame.font.Font('assets/fonts/elemental.ttf', DEBUG_FONT_SIZE)
pygame.display.set_icon(icon)
pygame.display.set_caption('Farlands')

pygame.mouse.set_visible(False) # Hide cursor here

# Initialize Pygame clock
clock = pygame.time.Clock()


def get_debug_text():
    text = []
    if clock is not None:
        text.append(f"FPS: {clock.get_fps():.2f}")
    if client.server_clock is not None:
        text.append(f"TPS: {client.server_clock.get_fps():.2f}")
    player = client.player
    if player is not None:
        text.extend([
            f"pos (world): [x: {player.position.x:.0f} y: {player.position.y:.0f}]",
            f"pos (map): [x: {player.position.x/TILE_SIZE:.0f} y: {player.position.y/TILE_SIZE:.0f}]",
            f"vel: [x: {player.get_velocity().x:} y: {player.get_velocity().y:}]",
        ])
    return text

# Enable blending to handle transparency
glEnable(GL_BLEND)
glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
glBlendColor(1.0, 1.0, 1.0, 1.0)
glEnable(GL_TEXTURE_2D)
glDisable(GL_MULTISAMPLE)


client = Client(font)

# !!!!!
# threading
# !!!!!

def game_logic_thread(flags, client: Client):
    client.server_clock = pygame.time.Clock()

    while flags[0]:
        server_dt = client.server_clock.tick(TPS) / 1000.0  # Конвертуємо час у секунди
        # print(server_dt)

        mouse_clicked = False
        client.mouse_pos.x, client.mouse_pos.y = pygame.mouse.get_pos()
        m_l, m_m, m_r = pygame.mouse.get_pressed()
        screen_size = Vec2(client.screenWidth, client.screenHeight)

        client.focused_objects = []
        spawn_pos = client.mouse_pos - client.camera.get_offset()
        p = spawn_pos / TILE_SIZE / client.camera.get_scale()

        if client.world is not None:
            tile_available, side_hit, _ = client.world.map_manager.trace_ray(
                client.player.position / TILE_SIZE,
                (p - client.player.position / TILE_SIZE).normalized())

            if tile_available is not None:
                client.focused_objects.append(tile_available)

        else: tile_available, side_hit = None, None




        if not client.is_initialized:
            continue
        if client.input_flags["scroll_d"] != 0:
            client.player.inventory.move_slot_pointer(-client.input_flags["scroll_d"])
            client.input_flags["scroll_d"] = 0
            client.play_sound("fx", "click")

        if client.input_flags["mouse_clicked"]:
            if client.world is not None:
                pos = (client.mouse_pos - client.camera.get_offset()) / client.camera.get_scale()
                shake_screen = client.player.use_item_in_hand(client.world, client.camera, client.textures, (m_l, m_m, m_r), pos, tile_available, side_hit)
                if shake_screen:
                    client.camera.shake(0.2, 5)

            mouse_clicked = True
            client.input_flags["mouse_clicked"] = False

        keys = pygame.key.get_pressed()

        if keys[client.keybinds['move_left']]:
            client.player.move_left(server_dt)
        else: client.player.is_traveling_left = False

        if keys[client.keybinds['move_right']]:
            client.player.move_right(server_dt)
        else: client.player.is_traveling_right = False

        if keys[client.keybinds['jump']]:
            client.player.jump(server_dt)

        # if keys[client.keybinds['crouch']]:
        #     client.player.crouch(True)
        # else:
        #     client.player.crouch(False)

        # if keys[keybinds['sprint']]:
        #     player.sprint()

        if client.input_flags["key_pressed"]:
            if keys[K_p]:
                client.player.set_text_bubble("wow")
                if client.world is not None:
                    pos = client.player.position
                    client.world.spawn(
                        PlayerNPC(client.world, pos.x, pos.y, 12, 29,
                                    client.textures["entities"]['player'][0], 50),
                        pos.x/TILE_SIZE)

            if keys[K_F3]:
                pass
                # memory profiling
                # snapshot = tracemalloc.take_snapshot()
                # top_stats = snapshot.statistics('lineno')
                #
                # print("[ Топ 10 джерел витрат памʼяті ]")
                # for stat in top_stats[:10]:
                #     print(stat)

                # log_memory_stats()
                # make_vec2_graph()

            client.input_flags["key_pressed"] = False

        if client.world is None:

            # main menu

            play_button = client.screens["main_menu"].buttons[0]
            play = play_button.is_pressed(mouse_clicked, screen_size, client.mouse_pos, client.camera.get_scale())

            if keys[pygame.K_RETURN] or play:
                client.is_loading = True
                client.world = World()
                client.world.create_map(4, client)
                client.is_loading = False

            continue

        if client.player is None and client.world is not None:
            pass

        if not client.player in client.world.environment.bodies and client.world.environment.time_running > 1:
            # player is missing, either dead or not initialized yet
            if client.player.is_alive:
                client.world.spawn(client.player, 0)

        client.update(server_dt)
        client.play_sound("music", "background")
        client.play_sound("ambience", "forest")

        for layer in sorted(client.background_layers, key=lambda l: l.layer):
            layer.scroll(client.camera.get_offset().x, screen_size.x, server_dt)

        pass


start_time = pygame.time.get_ticks()
initialized_time = pygame.time.get_ticks()
world_start_time = pygame.time.get_ticks()
play_button_hover_time = pygame.time.get_ticks()
logo_animation_time = 500
player_adding_interval = 1500

last_toggle_time = 0

running = True
server_running = True
server_flags = [server_running]

server_thread = threading.Thread(target=game_logic_thread, args=(server_flags, client,), daemon=True)
server_thread.start()


while server_flags[0] or running:
    dt = clock.tick() / 1000.0  # Конвертуємо час у секунди
    # print(clock.get_fps())
    if not server_flags[0]: running = False

    now = pygame.time.get_ticks()

    for event in pygame.event.get():
        if event.type == QUIT:
            server_flags[0] = False
            pass

        elif event.type == VIDEORESIZE and now - last_toggle_time > TOGGLE_COOLDOWN_MS:
            client.setup_screen(*event.size)

        elif event.type == pygame.KEYDOWN:
            client.input_flags["key_pressed"] = True
            if event.key == client.keybinds['fullscreen']:
                client.preferences['fullscreen'] = not client.preferences['fullscreen']
                client.setup_screen(client.screenWidth, client.screenHeight)
                last_toggle_time = now  # Record when we toggled fullscreen
            elif event.key == client.keybinds['debug']:
                client.is_debugging = not client.is_debugging

        elif event.type == pygame.MOUSEBUTTONDOWN:
            client.input_flags["mouse_clicked"] = True

        elif event.type == pygame.MOUSEWHEEL:
            client.input_flags["scroll_d"] = event.y

    keys = pygame.key.get_pressed()

    width, height = pygame.display.get_window_size()
    if (width != client.screenWidth) or (height != client.screenHeight):
        if width is not None and height is not None:
            client.setup_screen(width, height)

    # Render game here

    screen_size = Vec2(client.screenWidth, client.screenHeight)

    glBindVertexArray(client.renderer.quad_vao)

    if not client.is_initialized:
        start_time = pygame.time.get_ticks()
        time_animation_goes = 0
        while time_animation_goes < logo_animation_time:
            glClear(GL_COLOR_BUFFER_BIT)
            t = parametric_blend(time_animation_goes/logo_animation_time)
            client.renderer.draw_quad(logo[0],
                  create_transformation_matrix(
                      screen_size / 2,
                      Vec2(logo[1], logo[2])*(t*0.1+0.8)), transparency=1-t)
            pygame.display.flip()
            time_animation_goes = pygame.time.get_ticks() - start_time


        client.initialize()

        client.screens["debug"] = Screen(None, [
            TextLabel(16,16, Vec2(), client.renderer.default_font, "")
        ], [])

        client.play_sound("fx", "start")

        start_time = pygame.time.get_ticks()
        time_animation_goes = 0
        while time_animation_goes < logo_animation_time:
            glClear(GL_COLOR_BUFFER_BIT)
            t = parametric_blend(time_animation_goes/logo_animation_time)
            client.renderer.draw_quad(logo[0],
                  create_transformation_matrix(
                      screen_size / 2,
                      Vec2(logo[1], logo[2])*((1-t)*0.1+0.8)), transparency=t)
            pygame.display.flip()
            time_animation_goes = pygame.time.get_ticks() - start_time

        glClear(GL_COLOR_BUFFER_BIT)

        continue

    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    if client.world is None:
        client.screens["main_menu"].draw(client.renderer, client.camera, client.mouse_pos)
        draw_cursor(client, CursorType.DEFAULT)
        pygame.display.flip()
        continue

    if client.is_loading:
        client.screens["main_menu_loading"].draw(client.renderer, client.camera, client.mouse_pos)
        pygame.display.flip()
        continue

    client.debug_text = get_debug_text()

    draw_world(client, clock, dt)
    draw_cursor(client, CursorType.CROSSHAIR)

    pygame.display.flip()

pygame.quit()