import math
import threading

import pygame.time

from src.client.client import Client
# modules
from src.client.renderer import *
from src.client.screens import ProgressBar
from src.shared.physics.objects import *


from src.shared.textures import *
from src.shared.world import World

import ctypes
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
screen = pygame.display.set_mode((INITIAL_SCREEN_WIDTH, INITIAL_SCREEN_HEIGHT), DOUBLEBUF | OPENGL | RESIZABLE)
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

def game_logic_thread(running, client: Client):
    client.server_clock = pygame.time.Clock()

    while running:
        server_dt = client.server_clock.tick(TPS) / 1000.0  # Конвертуємо час у секунди
        # print(server_dt)

        mouse_clicked = False
        client.mouse_pos.x, client.mouse_pos.y = pygame.mouse.get_pos()
        m_l, m_m, m_r = pygame.mouse.get_pressed()
        screen_size = Vec2(client.screenWidth, client.screenHeight)

        if not client.is_initialized:
            continue
        if client.input_flags["scroll_d"] != 0:
            client.player.inventory.move_slot_pointer(-client.input_flags["scroll_d"])
            client.input_flags["scroll_d"] = 0

        if client.input_flags["mouse_clicked"]:
            client.player.set_text_bubble("wow")
            if client.world is not None:
                client.camera.shake(0.2, 5)
                pos = (client.camera.get_offset() + screen_size - client.mouse_pos)/TILE_SIZE
                client.world.environment.add_body(PlayerNPC(pos.x, pos.y,12, 29,
                             client.textures["entities"]['player'][0], 50))
            # client.player.damage(1)
            mouse_clicked = True
            client.input_flags["mouse_clicked"] = False

        keys = pygame.key.get_pressed()

        if keys[client.keybinds['move_left']]:
            client.player.move_left(server_dt)
        else: client.player.is_traveling_left = False

            # start_velocity = client.player.get_velocity()
            # if start_velocity.x * dt > client.player.movement_speed*-0.001:
            #     client.player.position.x += client.player.movement_speed*-0.001+start_velocity.x * dt

        if keys[client.keybinds['move_right']]:
            client.player.move_right(server_dt)
        else: client.player.is_traveling_right = False
            # start_velocity = client.player.get_velocity()
            # if start_velocity.x * dt < client.player.movement_speed*0.001:
            #     client.player.position.x += client.player.movement_speed*0.001-start_velocity.x * dt


        if keys[client.keybinds['jump']]:
            client.player.jump(server_dt)

        # if keys[client.keybinds['crouch']]:
        #     if client.player.get_velocity().y < client.player.movement_speed:
        #         client.player.move(Vec2(0, client.player.movement_speed / (dt * dt)))

        #     player.crouch(True)
        # else:
        #     player.crouch(False)

        # if keys[keybinds['sprint']]:
        #     player.sprint()




        ### crushes the game:
        # if keys[client.keybinds['fullscreen']]:
        #     pygame.display.toggle_fullscreen()

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
            # player is missing, either dead or not onotoalized yet
            if client.player.is_alive:
                client.world.environment.add_body(client.player)

        spawn_pos = client.mouse_pos - client.camera.get_offset()
        p = spawn_pos / TILE_SIZE / client.camera.get_scale()
        world_mouse_pos = Vec2i(math.floor(p.x), math.floor(p.y))

        client.focused_objects = []

        # tile_available = client.world.map_manager.get_first_non_none_tile(, world_mouse_pos)
        tile_available, side_hit, _ = client.world.map_manager.trace_ray(client.player.position/TILE_SIZE, (p - client.player.position/TILE_SIZE).normalized(), )
        tile_pointing = client.world.map_manager.get_tile(world_mouse_pos.x, world_mouse_pos.y)
        if tile_available is not None:
            if mouse_clicked and m_r:
                stack = client.player.inventory.get_current()
                if not (stack is None or stack.item is None or stack.item.tile_type is None):
                    append_pos = tile_available.tile_pos
                    match side_hit:
                        case "top": append_pos += Vec2(0,1)
                        case "left": append_pos += Vec2(1, 0)
                        case "bottom": append_pos += Vec2(0, -1)
                        case "right": append_pos += Vec2(-1, 0)
                    print(side_hit)
                    if client.world.map_manager.get_tile(append_pos.x, append_pos.y) is None:
                        client.world.map_manager.set_tile(append_pos.x, append_pos.y, stack.item.tile_type)
                        client.player.inventory.use()
                        client.focused_objects.append(client.world.map_manager.get_tile(append_pos.x, append_pos.y))
                    else: print("oksdjvdjskkjFVJPFJJPVDFPJVPDF DSJKOVJSF")
            elif mouse_clicked and m_l:
                client.world.map_manager.delete_tile(tile_available.tile_pos)
            else:
                client.focused_objects.append(tile_available)


        client.update(server_dt)
        # if not pygame.mixer.music.get_busy():
        #     play_sound(random.choice(biome_background_music))

        for layer in sorted(client.background_layers, key=lambda l: l.layer):
            layer.scroll(client.camera.get_offset().x, screen_size.x, server_dt)

        pass


start_time = pygame.time.get_ticks()
initialized_time = pygame.time.get_ticks()
world_start_time = pygame.time.get_ticks()
play_button_hover_time = pygame.time.get_ticks()
# play_button_scale =
logo_animation_time = 500
player_adding_interval = 1500


last_toggle_time = 0
TOGGLE_COOLDOWN_MS = 300  # ms to block VIDEORESIZE after fullscreen toggle

# start_sound = pygame.mixer.Sound("assets/sounds/fx/start.wav")

running = True
server_running = True

threading.Thread(target=game_logic_thread, args=(server_running, client,), daemon=True).start()


def draw_cursor():
    client.renderer.draw_quad(client.renderer.default_shader_uniforms, client.textures["ui"]["crosshair"][0],
              matrices["normal"],
              create_transformation_matrix(offset=Vec2(*pygame.mouse.get_pos()) - Vec2(0.5, 0.5),
                                           size=Vec2(client.textures["ui"]["crosshair"][1],
                                                     client.textures["ui"]["crosshair"][2])))


# # Create framebuffer
# fbo = glGenFramebuffers(1)
# glBindFramebuffer(GL_FRAMEBUFFER, fbo)
#
# # Color texture attachment
# texture_color_buffer = glGenTextures(1)
# glBindTexture(GL_TEXTURE_2D, texture_color_buffer)
# glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, screenWidth, screenHeight, 0, GL_RGB, GL_UNSIGNED_BYTE, None)
# glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
# glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
# glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, texture_color_buffer, 0)
#
# # Depth-stencil renderbuffer
# rbo = glGenRenderbuffers(1)
# glBindRenderbuffer(GL_RENDERBUFFER, rbo)
# glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH24_STENCIL8, screenWidth, screenHeight)
# glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_STENCIL_ATTACHMENT, GL_RENDERBUFFER, rbo)
#
# # Check completeness
# if glCheckFramebufferStatus(GL_FRAMEBUFFER) != GL_FRAMEBUFFER_COMPLETE:
#     print("ERROR::FRAMEBUFFER:: Framebuffer is not complete!")
#
# glBindFramebuffer(GL_FRAMEBUFFER, 0)



# 1. Generate texture
fbo_texture = glGenTextures(1)
glBindTexture(GL_TEXTURE_2D, fbo_texture)
glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, screenWidth, screenHeight, 0, GL_RGB, GL_UNSIGNED_BYTE, None)

# 2. Set texture filtering
glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

# 3. Create and bind FBO
fbo = glGenFramebuffers(1)
glBindFramebuffer(GL_FRAMEBUFFER, fbo)

# 4. Attach texture to FBO's color buffer
glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, fbo_texture, 0)

# 6. Check if framebuffer is complete
if glCheckFramebufferStatus(GL_FRAMEBUFFER) != GL_FRAMEBUFFER_COMPLETE:
    print("ERROR: Framebuffer is not complete")
else:
    print("Framebuffer complete, texture is bound.")

glBindFramebuffer(GL_FRAMEBUFFER, 0)


while server_running or running:
    dt = clock.tick() / 1000.0  # Конвертуємо час у секунди
    # print(clock.get_fps())
    if not server_running: running = False

    now = pygame.time.get_ticks()

    for event in pygame.event.get():
        if event.type == QUIT:
            server_running = False

        elif event.type == VIDEORESIZE and now - last_toggle_time > TOGGLE_COOLDOWN_MS:
            # Handle window resize
            width, height = event.size
            client.setup_screen(width, height)

        elif event.type == pygame.KEYDOWN:
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

    # Clear the screen
    # glClear(GL_COLOR_BUFFER_BIT)

    if not client.is_initialized:

        glClear(GL_COLOR_BUFFER_BIT)

        for a in range(logo_animation_time):
            glClear(GL_COLOR_BUFFER_BIT)
            t = parametric_blend(a/logo_animation_time)
            client.renderer.draw_quad(client.renderer.default_shader_uniforms, logo[0], matrices["normal"],
                  create_transformation_matrix(
                      screen_size / 2,
                      Vec2(logo[1], logo[2])*(t*0.1+0.8)), 1-t)
            pygame.display.flip()
            while pygame.time.get_ticks() < start_time + a: pass

        client.initialize()

        client.play_sound("fx", "start")

        for a in range(logo_animation_time):
            glClear(GL_COLOR_BUFFER_BIT)
            t = parametric_blend(a/logo_animation_time)
            client.renderer.draw_quad(client.renderer.default_shader_uniforms, logo[0], matrices["normal"],
                  create_transformation_matrix(
                      screen_size / 2,
                      Vec2(logo[1], logo[2])*((1-t)*0.1+0.8)), t)
            pygame.display.flip()
            while pygame.time.get_ticks() < start_time + a: pass

        glClear(GL_COLOR_BUFFER_BIT)

        continue

    # glBindFramebuffer(GL_FRAMEBUFFER, fbo)
    # glViewport(0, 0, client.screenWidth, client.screenHeight)  # Optional, but good practice
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    # don't draw if not focused
    # not working so not needed
    # if not pygame.display.get_active(): continue

    if client.world is None:
        client.screens["main_menu"].draw(client.renderer, client.camera, client.mouse_pos)
        draw_cursor()
        pygame.display.flip()
        continue

    if client.is_loading:
        client.screens["main_menu_loading"].draw(client.renderer, client.camera, client.mouse_pos)

        # client.renderer.draw_image_cover(client.renderer.default_shader_uniforms, backup_bg[0], Vec2(backup_bg[1], backup_bg[2]), screen_size, client.camera.scale)
        # client.renderer.draw_quad(client.renderer.default_shader_uniforms, client.textures["ui"]["main_menu_title"][0], matrices["normal"],
        #           create_transformation_matrix(
        #               offset=Vec2(screen_size.x/2, screen_size.y*0.35),
        #               size=Vec2(
        #                   client.textures["ui"]["main_menu_title"][1],
        #                   client.textures["ui"]["main_menu_title"][2]
        #               ),
        #               scale=client.camera.get_scale()
        #           ))
        #
        #
        # client.renderer.draw_quad(client.renderer.default_shader_uniforms, client.textures["ui"]["loadbar_bg"][0], matrices["normal"],
        #           create_transformation_matrix(
        #               position=Vec2(0, client.textures["ui"]["main_menu_title"][2]),
        #               offset=Vec2(screen_size.x/2, screen_size.y*0.7),
        #               size=Vec2(
        #                   client.textures["ui"]["loadbar_bg"][1],
        #                   client.textures["ui"]["loadbar_bg"][2]
        #               ),
        #               scale=client.camera.get_scale()
        #           ))
        # progress = min(1, max(0, client.loaded))
        # crop_matrix = create_transformation_matrix(size=Vec2(progress, 1))
        #
        # client.renderer.draw_quad(client.renderer.default_shader_uniforms, client.textures["ui"]["loadbar_fg"][0], crop_matrix,
        #           create_transformation_matrix(
        #               position=Vec2(client.textures["ui"]["loadbar_bg"][1]*(progress-1)*0.5, client.textures["ui"]["main_menu_title"][2]),
        #               offset=Vec2(screen_size.x/2 , screen_size.y*0.7),
        #               size=Vec2(
        #                   client.textures["ui"]["loadbar_bg"][1]*progress,
        #                   client.textures["ui"]["loadbar_bg"][2]
        #               ),
        #               scale=client.camera.get_scale()
        #           ))
        # text = f"{math.ceil(progress*100)}%"
        # text_top = client.camera.get_scale()*(client.textures["ui"]["main_menu_title"][2])
        # text_shadow_top = client.camera.get_scale()*(client.textures["ui"]["main_menu_title"][2] + 1)
        #
        # client.renderer.draw_text(client.renderer.default_shader_uniforms, screen_size.x/2+client.camera.get_scale(), screen_size.y*0.7 + text_shadow_top,
        #           text, font,
        #           (0,0,0,0),
        #           centered=True)
        # client.renderer.draw_text(client.renderer.default_shader_uniforms, screen_size.x/2, screen_size.y*0.7 + text_top,
        #           text, font,
        #           (255,255,255,255),
        #           centered=True)


        draw_cursor()
        pygame.display.flip()
        continue

    followed_body = client.player
    #
    # glUseProgram(default_shader)
    #
    #
    # Draw background layers
    i=0
    for layer in sorted(client.background_layers, key=lambda l: l.layer):
        glUniform4f(client.renderer.default_shader_uniforms["fogColor"], 0.51, 0.42, 0.59, 0 if i==1 else 0.1+0.4*(1-i/len(client.background_layers)))
        wave_angle = 0
        if layer.waving:
            wave_angle = math.sin(pygame.time.get_ticks() / (1000 + i*200) + i*20) * 2
        client.renderer.draw_image_cover(client.renderer.default_shader_uniforms, layer.texture, Vec2(layer.width, layer.height), screen_size, client.camera.scale, 0 if layer.is_immovable else layer.offset, wave_angle)
        # draw_image_cover(client.renderer.default_shader_uniforms, quad_vao, client.background_layers[0].texture, Vec2(layer.width, layer.height), screen_size, client.camera.scale, 0, 0.85)
        i+=1



    world_offset = client.camera.get_offset() / client.camera.get_scale()
    start = (world_offset * -1) / TILE_SIZE
    end = (screen_size - world_offset) / TILE_SIZE

    cx_start, cy_start, _, _ = client.world.map_manager.get_local_coords(start.x, start.y)
    cx_end, cy_end, _, _ = client.world.map_manager.get_local_coords(end.x, end.y)

     # print(start, end)

    client.camera.follow(followed_body, client.mouse_pos, dt)
    followed_body_pos = followed_body.position.copy()

    for layer in range(-1, 2):
        if layer==-1:
            glUniform4f(client.renderer.default_shader_uniforms["fogColor"], 0,0,0,0.25)

        if layer==0:
            glUniform4f(client.renderer.default_shader_uniforms["fogColor"], 0,0,0,0)

        glBindVertexArray(client.renderer.non_centered_vao)

        for x in range(cx_start, cx_end):
            for y in range(cy_start, cy_end):

                if (x, y) in client.world.map_manager.render_meshes[layer]:
                    for tile_type, meshes in client.world.map_manager.render_meshes[layer][(x, y)].items():

                        if tile_type in client.textures["tiles_irregular"]:
                            for body in meshes:

                                start = Vec2i.from_vec2(body.position/TILE_SIZE)
                                end = Vec2i.from_vec2((body.position + body.size)/TILE_SIZE)
                                for tx in range(start.x, end.x):
                                    for ty in range(start.y, end.y):
                                        p = Vec2(tx, ty)*TILE_SIZE
                                        texture = client.textures["tiles_irregular"][tile_type]
                                        render_start = p - Vec2((texture[1] - TILE_SIZE) / 2, texture[2] - TILE_SIZE)
                                        client.renderer.draw_quad(client.renderer.default_shader_uniforms, texture[0], matrices["normal"],
                                                  create_transformation_matrix(render_start, Vec2(texture[1], texture[2]), client.camera.get_offset(),
                                                                               client.camera.get_scale()))

                        else:
                            for body in meshes:
                                # if client.world.environment.check_collision(body, client.camera.renderBounds):
                                client.renderer.draw_quad(client.renderer.default_shader_uniforms, client.textures["tiles"][tile_type][0],
                                        create_transformation_matrix(size=body.size/TILE_SIZE),
                                          create_transformation_matrix(body.position, body.size, client.camera.get_offset(),
                                                                       client.camera.get_scale()))
                else:
                    client.world.map_manager.mark_chunk_dirty(x, y)

        if layer == 0:
            for body in client.world.environment.bodies:
                pos = body.position
                if body == followed_body:
                    pos = followed_body_pos
                elif pos.distance_to(followed_body_pos) > max(screen_size.x, screen_size.y)/2:
                    continue

                scale = client.camera.get_scale()
                offset = client.camera.get_offset()
                texture = body.texture
                outline_color = [1.0, 1.0, 1.0, 0.5]
                uv = body.get_uv()
                size = body.size
                transparency = 0

                if isinstance(body, Particle) or issubclass(type(body), Particle):
                    transparency = body.get_transparency()
                    if isinstance(body, TileBreakParticle):
                        texture = client.textures["tiles"][body.tile_type][0]

                elif isinstance(body, ItemStackEntity):
                    texture = client.textures["tiles"][body.stack.item.tile_type][0]
                    outline_color = [0.0, 0.8, 0.4, 0.8]

                elif isinstance(body, LivingEntity) or issubclass(type(body), LivingEntity):
                    texture_number = body.state.value
                    if body.state.value > len(client.textures["entities"][body.entity_type]):
                        texture_number = 0
                    texture_size = Vec2(client.textures["entities"][body.entity_type][0][1],
                                        client.textures["entities"][body.entity_type][0][2])
                    body.texture_size = texture_size
                    current_texture_size = Vec2(client.textures["entities"][body.entity_type][texture_number][1],
                                        client.textures["entities"][body.entity_type][texture_number][2])
                    body.animation_frames = max(1, int(current_texture_size.x / texture_size.x))
                    frame_uv = create_transformation_matrix(
                        Vec2(int(body.animation_frame) * texture_size.x / current_texture_size.x, 0),
                        Vec2(texture_size.x / current_texture_size.x,1)
                    )
                    uv = np.matmul(uv, frame_uv)
                    texture = client.textures["entities"][body.entity_type][texture_number][0]
                    size = texture_size
                    pos += Vec2((body.size.x - texture_size.x)/2, body.size.y - texture_size.y)


                if texture is not None:
                    # glUseProgram(client.renderer.outline_shader)
                    # glUniform1f(client.renderer.outline_shader_uniforms["outlineThickness"], 1/scale)
                    # glUniform4f(client.renderer.outline_shader_uniforms["outlineColor"], *outline_color)
                    # draw_quad(client.renderer.outline_shader_uniforms, non_centered_vao, texture, uv,
                    #                   create_transformation_matrix(pos, size, offset, scale))
                    # glUseProgram(client.renderer.default_shader)
                    client.renderer.draw_quad(client.renderer.default_shader_uniforms, texture, uv,
                                      create_transformation_matrix(pos, size, offset, scale), transparency)


                text_bubble = body.get_text_bubble()
                if text_bubble is not None:

                    text_surface = font.render(text_bubble, True, (255,255,255,255))
                    texture_id, text_width, text_height = surface_to_texture(text_surface)
                    size = Vec2(text_width, text_height)
                    # start = Vec2(x, y) if centered else Vec2(x, y) + size / 2
                    client.renderer.draw_quad(client.renderer.default_shader_uniforms, texture_id, matrices["normal"],
                              create_transformation_matrix(pos*scale, size,
                                                           client.camera.get_offset() - Vec2((size.x-body.size.x)/2, size.y + DEBUG_FONT_SIZE)))


                # draw item in hand

                if isinstance(body, LivingEntity) or issubclass(type(body), LivingEntity):
                    stack = body.inventory.get_current()
                    if stack is not None:
                        t = client.textures["tiles"][stack.item.tile_type]
                        size = Vec2(t[1], t[2]) / (max(t[1], t[2]) / TILE_SIZE)
                        rotation = (followed_body.position - client.mouse_pos).get_rotation_deg()
                        client.renderer.draw_quad(client.renderer.default_shader_uniforms, t[0], matrices["normal"],
                                                  create_transformation_matrix(pos, size, of, s))

                # draw_text(client.renderer.default_shader_uniforms, quad_vao,
                #           pos.x,
                #           pos.y,
                #           "ifbfdiovnfdobjnbojnbo", font, (255, 255, 255, 255))


        # for x in range(cx_start, cy_start):
        #     for y in range(cx_end, cx_end):
        #         for obj in client.map_manager.collision_map[x, y]:
        #             print(obj)
        #             pass



    # focused bodies outline render
    glUseProgram(client.renderer.outline_shader)
    glUniform1f(client.renderer.outline_shader_uniforms["centered"], False)
    glUniform1f(client.renderer.outline_shader_uniforms["outlineThickness"], 1 / client.camera.get_scale())
    glUniform4f(client.renderer.outline_shader_uniforms["outlineColor"], 1, 1, 1, 1)

    for obj in client.focused_objects:
        if obj is not None:
            texture = obj.texture
            pos = obj.position
            size = obj.size
            if isinstance(obj, Tile):
                if obj.tile_type in client.textures["tiles_irregular"]:
                    t = client.textures["tiles_irregular"][obj.tile_type]
                    texture = t[0]
                    pos = obj.position - Vec2((t[1] - TILE_SIZE) / 2, t[2] - TILE_SIZE)
                    size = Vec2(t[1], t[2])
                else: texture = client.textures["tiles"][obj.tile_type][0]
            if texture is not None:
                client.renderer.draw_quad(client.renderer.outline_shader_uniforms, texture, obj.get_uv(),
                          create_transformation_matrix(pos, size, client.camera.get_offset(), client.camera.get_scale()))

    glUseProgram(client.renderer.default_shader)

    glBindVertexArray(client.renderer.quad_vao)

    s = math.ceil(client.camera.get_scale() * 0.5)

    if client.is_debugging:
        client.renderer.draw_debug_info(client.renderer.default_shader_uniforms, font, clock, client.server_clock, client.player)

    else:
        gap = UI_GAP
        i_t = client.textures["ui"]["inventory"]
        top = (i_t[2]/2+gap)*s
        inv_of = Vec2(screen_size.x / 2, top)
        client.renderer.draw_quad(client.renderer.default_shader_uniforms, i_t[0], matrices["normal"],
                  create_transformation_matrix(Vec2(), Vec2(i_t[1], i_t[2]), inv_of, s))
        of = Vec2(
            (screen_size.x
             - (client.textures["ui"]["inventory_slot_focused"][1]) * s * (client.player.inventory.size-1)
             - gap * s * (client.player.inventory.size-1)) / 2,
            top
        )

        for x in range(client.player.inventory.size):
            stack = client.player.inventory.items[x]
            focused = x==client.player.inventory.slot
            texture = client.textures["ui"]["inventory_slot_focused" if focused else "inventory_slot"]
            slot_size = Vec2(texture[1],texture[2])

            pos = Vec2((slot_size.x + gap) * x, 0)
            client.renderer.draw_quad(client.renderer.default_shader_uniforms, texture[0], matrices["normal"],
                      create_transformation_matrix(pos, slot_size, of, s), 0 if focused else 0.2)
            if stack is not None:
                t = client.textures["tiles"][stack.item.tile_type]
                size = Vec2(t[1], t[2]) / (max(t[1], t[2]) / TILE_SIZE)
                client.renderer.draw_quad(client.renderer.default_shader_uniforms, t[0], matrices["normal"],
                          create_transformation_matrix(pos, size, of, s))
                client.renderer.draw_text(client.renderer.default_shader_uniforms, pos.x*s + of.x + 1, pos.y*s + of.y + 1, str(stack.count), font, (0, 0, 0, 0))
                client.renderer.draw_text(client.renderer.default_shader_uniforms, pos.x*s + of.x, pos.y*s + of.y, str(stack.count), font, (255, 255, 255, 255))

        # draw ui

        client.screens["main_menu_ui"].draw(client.renderer, client.camera, client.mouse_pos, True, s)

        # health = client.player.health
        # health_coef = client.player.health / client.player.max_health
        # progress = min(1, max(0, health_coef))
        # of = Vec2(s_t[2] + gap, (s_t[2] - DEBUG_FONT_SIZE)/2)
        # crop_matrix = create_transformation_matrix(size=Vec2(progress, 1))
        # client.renderer.draw_quad(client.renderer.default_shader_uniforms, s_t[0], matrices["normal"],
        #           create_transformation_matrix(pos, Vec2(s_t[1], s_t[2]), Vec2(), s))
        # client.renderer.draw_quad(client.renderer.default_shader_uniforms, s_t_h[0], crop_matrix,
        #           create_transformation_matrix(pos, Vec2(s_t_h[1]*progress, s_t_h[2]), Vec2(s_t_h[1] * s * (0.5 * progress - 0.5),0), s))
        # client.renderer.draw_text(client.renderer.default_shader_uniforms, (of.x + 1) * s, (of.y + 1) * s,
        #                           str(health), font, (100, 100, 100, 100))
        # client.renderer.draw_text(client.renderer.default_shader_uniforms, of.x * s, of.y * s,
        #                           str(health), font, (255, 51, 0, 255))
        # pb.draw(client.renderer, screen_size, s, centered=True)

    if not client.player.is_alive:
        # death menu

        # death_message = "Not quite there."
        # client.renderer.draw_text(client.renderer.default_shader_uniforms, screen_size.x/2+1, screen_size.y/2+1,
        #                           death_message, font, (0,0,0,0), screen_size.x/DEBUG_FONT_SIZE)
        # client.renderer.draw_text(client.renderer.default_shader_uniforms, screen_size.x/2, screen_size.y/2,
        #                           death_message, font, (255, 255, 255, 255), screen_size.x/DEBUG_FONT_SIZE)

        pass


    draw_cursor()




    # post-processing

    # glBindFramebuffer(GL_FRAMEBUFFER, 0)
    # glClear(GL_COLOR_BUFFER_BIT)
    #
    # # glUseProgram(client.renderer.postprocess_shader)
    #
    # glActiveTexture(GL_TEXTURE0)
    # glBindTexture(GL_TEXTURE_2D, fbo_texture)
    # location = glGetUniformLocation(client.renderer.default_shader, "ourTexture")
    # glUniform1i(location, 0)
    #
    #
    # # Set UV transformation uniform
    # uv_matrix = np.array(uv_transform, dtype=np.float32)
    # glUniformMatrix4fv(u_loc["uvTransform"], 1, GL_FALSE, uv_matrix)
    #
    # # Set model matrix uniform
    # glUniformMatrix4fv(u_loc["modelMatrix"], 1, GL_FALSE, model_matrix)
    #
    # # Draw the quad
    # glDrawArrays(GL_TRIANGLE_STRIP, 0, 4)


    # draw_quad(client.renderer.default_shader_uniforms, quad_vao, texture_color_buffer, matrices["normal"],
    #           create_transformation_matrix(size=screen_size))
    # glUseProgram(client.renderer.default_shader)

    # Update display
    pygame.display.flip()

pygame.quit()