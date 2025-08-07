import pygame

from src.client.renderer import *
from src.shared.combat.bullet import Projectile
from src.shared.npc.npcs import PlayerNPC
from src.shared.physics.objects import *
from src.shared.utilites import *


def draw_cursor(client, cursor_type=CursorType.DEFAULT):
    texture_id = "cursor"
    of = Vec2(*pygame.mouse.get_pos())

    if cursor_type == CursorType.CROSSHAIR:
        texture_id = "crosshair"
        of -= Vec2(0.5, 0.5)

    c_texture = client.textures["ui"][texture_id]
    client.renderer.draw_quad(c_texture[0], create_transformation_matrix(offset=of, size=Vec2(c_texture[1], c_texture[2])))


def draw_world(client, clock, dt):

    screen_size = Vec2(client.screenWidth, client.screenHeight)

    followed_body = client.player
    #
    # glUseProgram(default_shader)
    #
    #
    # Draw background layers
    i = 0
    for layer in sorted(client.background_layers, key=lambda l: l.layer):
        glUniform4f(client.renderer.get_current_uniform_locations()["fogColor"], 0.51, 0.42, 0.59,
                    0 if i == 1 else 0.1 + 0.4 * (1 - i / len(client.background_layers)))
        wave_angle = 0
        if layer.waving:
            wave_angle = math.sin(pygame.time.get_ticks() / (1000 + i * 200) + i * 20) * 2
        client.renderer.draw_image_cover(layer.texture,
                                         Vec2(layer.width, layer.height), screen_size, client.camera.scale,
                                         0 if layer.is_immovable else layer.offset, wave_angle)
        # draw_image_cover(client.renderer.default_shader_uniforms, quad_vao, client.background_layers[0].texture, Vec2(layer.width, layer.height), screen_size, client.camera.scale, 0, 0.85)
        i += 1
    world_offset = client.camera.get_offset() / client.camera.get_scale()
    start = (world_offset * -1) / TILE_SIZE
    end = (screen_size - world_offset) / TILE_SIZE
    cx_start, cy_start, _, _ = client.world.map_manager.get_local_coords(start.x, start.y)
    cx_end, cy_end, _, _ = client.world.map_manager.get_local_coords(end.x, end.y)
    # print(start, end)
    client.camera.follow(followed_body, client.mouse_pos, dt)
    followed_body_pos = followed_body.position.copy()
    for layer in range(-1, 2):
        if layer == -1:
            glUniform4f(client.renderer.get_current_uniform_locations()["fogColor"], 0, 0, 0, 0.25)

        if layer == 0:
            glUniform4f(client.renderer.get_current_uniform_locations()["fogColor"], 0, 0, 0, 0)

        glBindVertexArray(client.renderer.non_centered_vao)

        for x in range(cx_start, cx_end):
            for y in range(cy_start, cy_end):

                if (x, y) in client.world.map_manager.render_meshes[layer]:
                    for tile_type, meshes in client.world.map_manager.render_meshes[layer][(x, y)].items():

                        if tile_type in client.textures["tiles_irregular"]:
                            for body in meshes:

                                start = Vec2i.from_vec2(body.position / TILE_SIZE)
                                end = Vec2i.from_vec2((body.position + body.size) / TILE_SIZE)
                                for tx in range(start.x, end.x):
                                    for ty in range(start.y, end.y):
                                        p = Vec2(tx, ty) * TILE_SIZE
                                        texture = client.textures["tiles_irregular"][tile_type]
                                        render_start = p - Vec2((texture[1] - TILE_SIZE) / 2, texture[2] - TILE_SIZE)
                                        client.renderer.draw_quad(texture[0],
                                                                  create_transformation_matrix(render_start,
                                                                                               Vec2(texture[1],
                                                                                                    texture[2]),
                                                                                               client.camera.get_offset(),
                                                                                               client.camera.get_scale()))

                        else:
                            for body in meshes:
                                # if client.world.environment.check_collision(body, client.camera.renderBounds):
                                client.renderer.draw_quad(client.textures["tiles"][tile_type][0],
                                                          create_transformation_matrix(body.position, body.size,
                                                                                       client.camera.get_offset(),
                                                                                       client.camera.get_scale()),
                                                          Vec4(0,0, body.size.x / TILE_SIZE, body.size.y / TILE_SIZE))
                else:
                    client.world.map_manager.mark_chunk_dirty(x, y)

        if layer == 0:

            def in_bounds(elem):
                pos = elem.position
                return abs(followed_body_pos.x - pos.x) < screen_size.x * 0.55 \
                    or abs(followed_body_pos.y - pos.y) < screen_size.y * 0.55

            for body in filter(in_bounds, client.world.environment.bodies):

                pos = body.position
                if body == followed_body:
                    pos = followed_body_pos

                draw_outlined = False
                outline_color = [1.0, 1.0, 1.0, 1.0]
                outline_thickness = 2
                scale = client.camera.get_scale()
                offset = client.camera.get_offset()
                texture = body.texture
                uv = body.get_uv()
                size = body.size
                transparency = 0
                wave_frequency = 250

                if isinstance(body, Particle) or issubclass(type(body), Particle):
                    transparency = body.get_transparency()
                    if isinstance(body, TileBreakParticle):
                        texture = client.textures["tiles"][body.tile_type][0]

                elif isinstance(body, ItemStackEntity):
                    texture = client.textures["tiles"][body.stack.item.tile_type][0]
                    offset.y -= int((1 + math.sin(
                        pygame.time.get_ticks() / wave_frequency + pos.x + pos.y + texture * 10)) * TILE_SIZE * 0.25 + 0.25)
                    draw_outlined = True

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
                    frame_uv = Vec4(
                        int(body.animation_frame) * texture_size.x / current_texture_size.x, 0,
                        texture_size.x / current_texture_size.x, 1
                    )
                    uv.transform(frame_uv)

                    texture = client.textures["entities"][body.entity_type][texture_number][0]
                    size = texture_size
                    pos += Vec2((body.size.x - texture_size.x) / 2, body.size.y - texture_size.y)
                    if body.is_stunted:
                        draw_outlined = True
                        outline_color = [1.0, 0.2, 0.1, 1.0]

                if isinstance(body, Projectile) or issubclass(type(body), Projectile):
                    draw_outlined = True

                if texture is not None:
                    if draw_outlined:
                        client.renderer.use_shader("outline")
                        glUniform1f(client.renderer.get_current_uniform_locations()["outlineThickness"],
                                    (1 / scale) * outline_thickness)
                        glUniform4f(client.renderer.get_current_uniform_locations()["outlineColor"], *outline_color)
                        client.renderer.draw_quad(texture,
                                                  create_transformation_matrix(pos, size, offset, scale), uv, transparency=transparency)
                        client.renderer.use_shader("default")
                    else:
                        client.renderer.draw_quad(texture,
                                                  create_transformation_matrix(pos, size, offset, scale), uv, transparency=transparency)

                # text_bubble = body.get_text_bubble()
                # if text_bubble is not None:
                #     text_surface = client.default_font.render(text_bubble, True, (255, 255, 255, 255))
                #     texture_id, text_width, text_height = surface_to_texture(text_surface)
                #     size = Vec2(text_width, text_height)
                #     # start = Vec2(x, y) if centered else Vec2(x, y) + size / 2
                #     client.renderer.draw_quad(client.renderer.default_shader_uniforms, texture_id, matrices["normal"],
                #                               create_transformation_matrix(pos * scale, size,
                #                                                            offset - Vec2(
                #                                                                (size.x - body.size.x) / 2,
                #                                                                size.y + DEBUG_FONT_SIZE)))

                # draw item in hand

                if isinstance(body, LivingEntity) or issubclass(type(body), LivingEntity):
                    stack = body.inventory.get_current()
                    if stack is not None:
                        t = client.textures["tiles"][stack.item.tile_type]
                        size = Vec2(t[1], t[2])
                        if stack.item.tile_type in client.textures["tiles_irregular"]:
                            size = Vec2(t[1], t[2]) / (max(t[1], t[2]) / TILE_SIZE)

                        rotation = (
                                    followed_body.position * client.camera.get_scale() + client.camera.get_offset() - client.mouse_pos).get_rotation_deg()
                        flip = False
                        if rotation < -90 or rotation > 90:
                            rotation += 180
                            flip = True
                        client.renderer.draw_quad(t[0],
                                                  create_transformation_matrix(
                                                      pos + Vec2(body.size.x * 0.5 if flip else body.size.x * 0.8, body.size.y*0.8) - size*0.5, size,
                                                      offset, scale,
                                                      rotation=rotation, flip_x=flip, origin=Vec2(0.5, 0.5)))

                # draw nps targets

                if isinstance(body, PlayerNPC) and client.is_debugging:
                    poss = []
                    if body.brain.target_pos is not None: poss += [body.brain.target_pos * TILE_SIZE]
                    if body.brain.action is not None: poss += [
                        Vec2(body.brain.action.jumps[f] * TILE_SIZE, body.position.y) for f in
                        range(len(body.brain.action.jumps))]
                    t = client.textures["ui"]["crosshair"]
                    for pos in poss:
                        client.renderer.draw_quad(t[0],
                                                  create_transformation_matrix(
                                                      pos, Vec2(4, 4),
                                                      offset, scale,
                                                      origin=Vec2(0.5, 0.5)))

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
    client.renderer.use_shader("outline")
    glUniform1f(client.renderer.get_current_uniform_locations()["centered"], False)
    glUniform1f(client.renderer.get_current_uniform_locations()["outlineThickness"], 1 / client.camera.get_scale())
    glUniform4f(client.renderer.get_current_uniform_locations()["outlineColor"], 1, 1, 1, 1)
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
                else:
                    texture = client.textures["tiles"][obj.tile_type][0]
            if texture is not None:
                client.renderer.draw_quad(texture,
                                          create_transformation_matrix(pos, size, client.camera.get_offset(),
                                                                       client.camera.get_scale()), transparency=0.5)
    client.renderer.use_shader("default")
    glBindVertexArray(client.renderer.quad_vao)
    s = math.ceil(client.camera.get_scale() * 0.5)
    if client.is_debugging:
        # client.renderer.draw_debug_info(None, client.default_font, clock, client.server_clock,
        #                                 client.player)

        client.screens["debug"].images[0].set_text("\r\n".join(client.debug_text))
        client.screens["debug"].draw(client.renderer, client.camera, client.mouse_pos, centered=False)

        debug_map_size = screen_size / 6
        debug_map_chunk_size = Vec2(1, 1) * TILE_SIZE
        gap = TILE_SIZE
        debug_map_offset = Vec2(screen_size.x - debug_map_size.x / 2 - gap, debug_map_size.y / 2 + gap)
        poss = list(client.world.environment.map_manager.dirty_chunks)

        for chunk_pos in poss:
            t = client.textures["tiles"]["dirt"]
            client.renderer.draw_quad(t[0],
                                      create_transformation_matrix(Vec2(*chunk_pos), Vec2(1, 1), debug_map_offset,
                                                                   debug_map_chunk_size.x))
        p = pos_world_to_map(client.player.position)
        cx, cy, lx, ly = client.world.map_manager.get_local_coords(p.x, p.y)
        sim_range = 3

        poss = [Vec2(x, y)
                for y in range(cy - sim_range, cy + sim_range)
                for x in range(cx - sim_range, cx + sim_range)]

        for chunk_pos in poss:
            t = client.textures["tiles"]["stone"] if chunk_pos == Vec2(cx, cy) \
                else client.textures["tiles"]["grass_dirt"]
            client.renderer.draw_quad(t[0],
                                      create_transformation_matrix(chunk_pos, Vec2(1, 1), debug_map_offset,
                                                                   debug_map_chunk_size.x))

    else:
        gap = UI_GAP
        i_t = client.textures["ui"]["inventory"]
        top = (i_t[2] / 2 + gap) * s
        inv_of = Vec2(screen_size.x / 2, top)
        client.renderer.draw_quad(i_t[0], create_transformation_matrix(Vec2(), Vec2(i_t[1], i_t[2]), inv_of, s))
        of = Vec2(
            (screen_size.x
             - (client.textures["ui"]["inventory_slot_focused"][1]) * s * (client.player.inventory.size - 1)
             - gap * s * (client.player.inventory.size - 1)) / 2,
            top
        )

        for x in range(client.player.inventory.size):
            stack = client.player.inventory.items[x]
            focused = x == client.player.inventory.slot
            texture = client.textures["ui"]["inventory_slot_focused" if focused else "inventory_slot"]
            slot_size = Vec2(texture[1], texture[2])

            pos = Vec2((slot_size.x + gap) * x, 0)
            client.renderer.draw_quad(texture[0],
                                      create_transformation_matrix(pos, slot_size, of, s), transparency= 0 if focused else 0.2)
            if stack is not None:
                t = client.textures["tiles"][stack.item.tile_type]
                size = Vec2(t[1], t[2]) / (max(t[1], t[2]) / TILE_SIZE)
                client.renderer.draw_quad(t[0],
                                          create_transformation_matrix(pos, size, of, s))
                # client.renderer.draw_text(client.renderer.default_shader_uniforms, pos.x * s + of.x + 1,
                #                           pos.y * s + of.y + 1, str(stack.count), client.default_font, (0, 0, 0, 0))
                # client.renderer.draw_text(client.renderer.default_shader_uniforms, pos.x * s + of.x, pos.y * s + of.y,
                #                           str(stack.count), client.default_font, (255, 255, 255, 255))

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

    # Delete any remaining large temps
    del screen_size, followed_body, world_offset, start, end, cx_start, cy_start, cx_end, cy_end, followed_body_pos



def draw_world_optimized(client, clock, dt):
    screen_size = Vec2(client.screenWidth, client.screenHeight)
    followed_body = client.player

    # Update camera follow logic
    client.camera.follow(followed_body, client.mouse_pos, dt)


    # Cache scale and offset once per frame
    cam_scale = client.camera.get_scale()
    cam_offset = client.camera.get_offset()

    # Cache player position once per frame (copy to avoid mutation issues)
    followed_body_pos = followed_body.position.copy()

    # Cache current time once per frame (for wave calculations)
    current_time = pygame.time.get_ticks()

    # Background layers rendering (cached fog alpha calc)
    total_layers = len(client.background_layers)
    for i, layer in enumerate(sorted(client.background_layers, key=lambda l: l.layer)):
        fog_alpha = 0 if i == 1 else 0.1 + 0.4 * (1 - i / total_layers)
        glUniform4f(client.renderer.get_current_uniform_locations()["fogColor"], 0.51, 0.42, 0.59, fog_alpha)

        wave_angle = 0
        if layer.waving:
            wave_angle = math.sin(current_time / (1000 + i * 200) + i * 20) * 2

        client.renderer.draw_image_cover(
            layer.texture,
            Vec2(layer.width, layer.height),
            screen_size,
            cam_scale,
            0 if layer.is_immovable else layer.offset,
            wave_angle
        )

    # Calculate camera world offsets and tile range once per frame
    world_offset = cam_offset / cam_scale
    start = (world_offset * -1) / TILE_SIZE
    end = (screen_size - world_offset) / TILE_SIZE

    cx_start, cy_start, _, _ = client.world.map_manager.get_local_coords(start.x, start.y)
    cx_end, cy_end, _, _ = client.world.map_manager.get_local_coords(end.x, end.y)


    # Iterate over layers (-1, 0, 1)
    for layer in range(-1, 2):
        # Set fog color per layer only once
        if layer == -1:
            glUniform4f(client.renderer.get_current_uniform_locations()["fogColor"], 0, 0, 0, 0.25)
        elif layer == 0:
            glUniform4f(client.renderer.get_current_uniform_locations()["fogColor"], 0, 0, 0, 0)

        glBindVertexArray(client.renderer.non_centered_vao)

        # Cache common texture lookup dicts outside inner loops
        tiles_irregular = client.textures["tiles_irregular"]
        tiles_regular = client.textures["tiles"]

        render_meshes_layer = client.world.map_manager.render_meshes[layer]

        # Loop over chunks visible on screen
        for x in range(cx_start, cx_end):
            for y in range(cy_start, cy_end):
                chunk_pos = (x, y)
                if chunk_pos in render_meshes_layer:
                    for tile_type, meshes in render_meshes_layer[chunk_pos].items():
                        if tile_type in tiles_irregular:
                            texture = tiles_irregular[tile_type]
                            tex_id, tex_w, tex_h = texture
                            half_tex_x = (tex_w - TILE_SIZE) / 2
                            for body in meshes:
                                start_tile = Vec2i.from_vec2(body.position / TILE_SIZE)
                                end_tile = Vec2i.from_vec2((body.position + body.size) / TILE_SIZE)
                                for tx in range(start_tile.x, end_tile.x):
                                    for ty in range(start_tile.y, end_tile.y):
                                        pos = Vec2(tx, ty) * TILE_SIZE
                                        render_start = pos - Vec2(half_tex_x, tex_h - TILE_SIZE)
                                        model_matrix = create_transformation_matrix(render_start, Vec2(tex_w, tex_h),
                                                                                    cam_offset, cam_scale)
                                        client.renderer.draw_quad(tex_id, model_matrix)
                        else:
                            tex_id = tiles_regular[tile_type][0]
                            for body in meshes:
                                # Precompute model matrix for body only once per body (avoids nested calls)
                                pos_matrix = create_transformation_matrix(body.position, body.size, cam_offset,
                                                                          cam_scale)
                                size_matrix = Vec4(0,0, body.size.x / TILE_SIZE, body.size.y / TILE_SIZE)
                                client.renderer.draw_quad(tex_id, pos_matrix, size_matrix)
                else:
                    client.world.map_manager.mark_chunk_dirty(x, y)

        # Layer 0 special: draw entities and particles, etc.
        if layer == 0:
            def in_bounds(elem):
                pos = elem.position
                dx = abs(followed_body_pos.x - pos.x)
                dy = abs(followed_body_pos.y - pos.y)
                return dx < screen_size.x * 0.55 or dy < screen_size.y * 0.55

            # Cache camera scale and offset once for this loop
            scale = cam_scale
            offset = cam_offset

            for body in filter(in_bounds, client.world.environment.bodies):
                pos = body.position if body != followed_body else followed_body_pos

                draw_outlined = False
                outline_color = [1.0, 1.0, 1.0, 1.0]
                outline_thickness = 2
                transparency = 0
                texture = body.texture
                uv = body.get_uv()
                size = body.size

                # Entity-specific logic
                if isinstance(body, Particle) or issubclass(type(body), Particle):
                    transparency = body.get_transparency()
                    if isinstance(body, TileBreakParticle):
                        texture = tiles_regular[body.tile_type][0]

                elif isinstance(body, ItemStackEntity):
                    texture = tiles_regular[body.stack.item.tile_type][0]
                    offset_y = int(
                        (1 + math.sin(current_time / 250 + pos.x + pos.y + texture * 10)) * TILE_SIZE * 0.25 + 0.25)
                    offset = Vec2(offset.x, offset.y - offset_y)
                    draw_outlined = True

                elif isinstance(body, LivingEntity) or issubclass(type(body), LivingEntity):
                    texture_number = body.state.value
                    textures_for_entity = client.textures["entities"][body.entity_type]
                    if texture_number >= len(textures_for_entity):
                        texture_number = 0

                    base_texture_size = Vec2(textures_for_entity[0][1], textures_for_entity[0][2])
                    current_texture_size = Vec2(textures_for_entity[texture_number][1],
                                                textures_for_entity[texture_number][2])
                    body.texture_size = base_texture_size
                    body.animation_frames = max(1, int(current_texture_size.x / base_texture_size.x))

                    frame_uv = create_transformation_matrix(
                        Vec2(int(body.animation_frame) * base_texture_size.x / current_texture_size.x, 0),
                        Vec2(base_texture_size.x / current_texture_size.x, 1)
                    )
                    uv = np.matmul(uv, frame_uv)
                    texture = textures_for_entity[texture_number][0]
                    size = base_texture_size
                    pos += Vec2((body.size.x - base_texture_size.x) / 2, body.size.y - base_texture_size.y)

                    if body.is_stunted:
                        draw_outlined = True
                        outline_color = [1.0, 0.2, 0.1, 1.0]

                if isinstance(body, Projectile) or issubclass(type(body), Projectile):
                    draw_outlined = True

                if texture is not None:
                    if draw_outlined:
                        client.renderer.use_shader("outline")
                        glUniform1f(client.renderer.get_current_uniform_locations()["outlineThickness"],
                                    (1 / scale) * outline_thickness)
                        glUniform4f(client.renderer.get_current_uniform_locations()["outlineColor"], *outline_color)
                        model_matrix = create_transformation_matrix(pos, size, offset, scale)
                        client.renderer.draw_quad(texture, model_matrix,
                                                  transparency=transparency)
                        client.renderer.use_shader("default")
                    else:
                        model_matrix = create_transformation_matrix(pos, size, offset, scale)
                        client.renderer.draw_quad(texture, model_matrix,
                                                  transparency=transparency)

                # Draw text bubble
                # text_bubble = body.get_text_bubble()
                # if text_bubble:
                #     text_surface = client.default_font.render(text_bubble, True, (255, 255, 255, 255))
                #     texture_id, text_width, text_height = surface_to_texture(text_surface)
                #     size = Vec2(text_width, text_height)
                #     model_matrix = create_transformation_matrix(pos * scale, size,
                #                                                 offset - Vec2((size.x - body.size.x) / 2,
                #                                                               size.y + DEBUG_FONT_SIZE))
                #     client.renderer.draw_quad(client.renderer.default_shader_uniforms, texture_id, matrices["normal"],
                #                               model_matrix)

                # Draw item in hand (LivingEntity only)
                if isinstance(body, LivingEntity) or issubclass(type(body), LivingEntity):
                    stack = body.inventory.get_current()
                    if stack:
                        t = tiles_regular[stack.item.tile_type]
                        size = Vec2(t[1], t[2]) / (
                            max(t[1], t[2]) / TILE_SIZE if stack.item.tile_type in tiles_irregular else 1)
                        rotation = (followed_body.position * scale + offset - client.mouse_pos).get_rotation_deg()
                        flip = False
                        if rotation < -90 or rotation > 90:
                            rotation += 180
                            flip = True
                        pos_hand = pos + Vec2(0, -size.y * 0.7)
                        model_matrix = create_transformation_matrix(pos_hand, size, offset, scale)
                        uv_hand = matrices["normal"]
                        if flip:
                            uv_hand = np.matmul(uv_hand, create_transformation_matrix(Vec2(1, 0), Vec2(-1, 1)))
                        client.renderer.draw_quad(t[0], model_matrix)

