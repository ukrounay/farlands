import re
import subprocess
import sys

from src.client.renderer import *
from src.client.screens import *
from src.shared.physics.objects import *
from src.shared.sounds import load_sounds_from_json
from src.shared.textures import *


class Client:
    player: Player | None

    def __init__(self, default_font):
        self.default_font = default_font
        self.screens = {}
        self.input_flags = {
            "scroll_d": 0,
            "mouse_clicked": False,
        }
        self.focused_objects = []
        self.mouse_pos = Vec2()
        self.server_clock = None
        self.ortho_projection_matrix = None
        self.screenHeight = None
        self.screenWidth = None
        self.screen = None
        self.keybinds = None
        self.world = None
        self.player = None
        self.camera = Camera()
        self.sceneHeight = None
        self.sceneWidth = None
        self.background_layers = None
        self.bg_source = None
        self.biome_name = None
        self.sounds = None
        self.currently_playing = {}
        self.textures = None
        self.tilemap = None
        self.is_debugging = False
        self.is_initialized = False
        self.is_loading = False
        self.loaded = 0
        self.renderer = Renderer(self.default_font)
        self.preferences = {
            "fullscreen": False
        }

    def get_loaded(self):
        return self.loaded


    def initialize(self):
        self.is_loading = True
        self.load_resources()
        self.is_loading = False
        self.is_initialized = True

    def load_resources(self):
        # Load data from the JSON file
        self.textures, texture_dict = load_textures_from_json('assets/textures.json')

        self.player = Player(0, 0,12, 29,
                             self.textures["entities"]['player'][0], 50)


        self.screens["main_menu"] = Screen(
            Image(0,0, Vec2(),
                self.textures["ui"]["main_menu_bg"][1],
                self.textures["ui"]["main_menu_bg"][2],
                self.textures["ui"]["main_menu_bg"][0]
            ),
            [
                Image(0.5, 0.35, Vec2(),
                    self.textures["ui"]["main_menu_title"][1],
                    self.textures["ui"]["main_menu_title"][2],
                    self.textures["ui"]["main_menu_title"][0]
                ),
            ],
            [
                Button(0.5, 50.6, Vec2(),
                    self.textures["ui"]["main_menu_play"][1],
                    self.textures["ui"]["main_menu_play"][2],
                    self.textures["ui"]["main_menu_play"][0],
                    ButtonForm.SQ45
                ),
            ])

        self.screens["main_menu_loading"] = Screen(
            Image(0,0, Vec2(),
                self.textures["ui"]["main_menu_bg"][1],
                self.textures["ui"]["main_menu_bg"][2],
                self.textures["ui"]["main_menu_bg"][0]
            ),
            [
                Image(0.5, 0.35, Vec2(),
                    self.textures["ui"]["main_menu_title"][1],
                    self.textures["ui"]["main_menu_title"][2],
                    self.textures["ui"]["main_menu_title"][0]
                ),
                ProgressBar(0.5, 0.7, Vec2(),
                            self.textures["ui"]["loadbar_bg"][1],
                            self.textures["ui"]["loadbar_bg"][2],
                            self.textures["ui"]["loadbar_bg"][0],
                            self.textures["ui"]["loadbar_fg"][0],
                            self.get_loaded,1,
                            percents=True)

            ],
            [])

        s_t = self.textures["ui"]["stats_ui"]
        s_t_h = self.textures["ui"]["stats_ui_progress_bar"]
        pos = Vec2(int(s_t[1]/2 + UI_GAP), int(s_t[2]/2 + UI_GAP))

        self.screens["main_menu_ui"] = Screen(
            None,
            [
                ProgressBar(pos.x, pos.y, Vec2(),
                            s_t[1], s_t[2], s_t[0], s_t_h[0],
                            self.player.get_health, self.player.max_health)
            ],
            [])

        # self.tilemap = Tilemap(texture_dict)
        self.sounds = load_sounds_from_json('assets/sounds.json')

        # self.biome_name = random.choice(list(textures['background'].keys()))
        # self.biome_name = "star_meadow"
        # self.biome_name = "farlands_plato"
        self.biome_name = "laria_valley"

        self.bg_source = self.textures['background'][self.biome_name]

        biome_background_music = self.sounds["background_music"][self.biome_name]

        bg_speeds = []
        bg_immovability = []
        bg_waving = []
        if self.biome_name == "laria_valley":
            for i in range(0, len(self.bg_source), 1, ):
                bg_speeds.append(0.02*(1 - 1 / (i + 1)) if (i==3 or i==6) else 0)
                bg_immovability.append(i==1 or i==2)
                bg_waving.append(i==5 or i==7)

        self.background_layers = [BackgroundLayer(
                self.bg_source[i], speed = 0.1 * (1 - 1 / (i + 1)),
                layer = i - len(self.bg_source),
                movement_speed = bg_speeds[i],
                is_immovable=bg_immovability[i],
                waving = bg_waving[i]
            ) for i in range(len(self.bg_source))]

        self.sceneWidth = self.background_layers[0].width
        self.sceneHeight = self.background_layers[0].height


        self.setup_screen(INITIAL_SCREEN_WIDTH, INITIAL_SCREEN_HEIGHT)





        # Create map manager
        # self.world.map_manager.update_chunk(0, 0)



        # Load keybinds from JSON file
        def load_keybinds(json_file):
            json_file = get_abs_path(json_file)

            with open(json_file) as f:
                keybind_map = json.load(f)

            # Convert key names in the JSON file to Pygame key constants
            keybinds = {}
            for action, key_name in keybind_map.items():
                keybinds[action] = getattr(pygame, key_name)

            return keybinds

        # Load keybinds from the JSON file
        self.keybinds = load_keybinds('data/default_keybinds.json')


        pass

    def create_ortho_projection_matrix(self):
        """
        Creates a 4x4 orthographic projection matrix for 2D rendering
        matching screen coordinates (0,0) top-left to (width,height) bottom-right.
        """
        matrix = np.identity(4, dtype=np.float32)

        # # Left, Right, Bottom, Top, Near, Far
        # left = 0.0
        # right = self.screenWidth
        # bottom = self.screenHeight
        # top = 0.0
        # near = -1.0
        # far = 1.0
        #
        # matrix[0, 0] = 2.0 / (right - left)
        # matrix[1, 1] = 2.0 / (top - bottom)
        # matrix[2, 2] = -2.0 / (far - near)
        #
        # matrix[0, 3] = -(right + left) / (right - left)
        # matrix[1, 3] = -(top + bottom) / (top - bottom)
        # matrix[2, 3] = -(far + near) / (far - near)



        # simple implementation

        # matrix[0, 0] = 2.0 / self.screenWidth
        # matrix[1, 1] = -2.0 / self.screenHeight  # Flip Y
        # matrix[0, 3] = -1.0
        # matrix[1, 3] = 1.0

        # return matrix

        # third implementation

        w = self.screenWidth
        h = self.screenHeight
        z_near = -1.0
        z_far = 1.0

        proj = np.identity(4, dtype=np.float32)
        proj[0, 0] = 2.0 / w
        proj[1, 1] = -2.0 / h  # Flip Y so (0,0) is top-left
        proj[2, 2] = -2.0 / (z_far - z_near)
        proj[0, 3] = -1.0
        proj[1, 3] = 1.0
        proj[2, 3] = -(z_far + z_near) / (z_far - z_near)

        return proj

    # def move_window(self, x, y):
    #     info = pygame.display.get_wm_info()
    #     if sys.platform == "win32":
    #         import ctypes
    #         hwnd = info['window']
    #         ctypes.windll.user32.SetWindowPos(hwnd, None, x, y, 0, 0, 0x0001)
    #     elif sys.platform.startswith("linux"):
    #         import subprocess
    #         subprocess.run(["xdotool", "windowmove", str(info['window']), str(x), str(y)])
    #     elif sys.platform == "darwin":
    #         print("⚠️ macOS: direct window positioning is not supported via SDL")

    def get_monitor_resolution_windows(self):
        user32 = ctypes.windll.user32
        user32.SetProcessDPIAware()  # Optional: avoid DPI scaling
        width = user32.GetSystemMetrics(0)
        height = user32.GetSystemMetrics(1)
        return width, height


    def get_monitor_resolution_linux(self):
        try:
            output = subprocess.check_output("xrandr | grep '*' | head -n 1", shell=True)
            resolution = re.search(r'(\d+)x(\d+)', output.decode())
            if resolution:
                return int(resolution.group(1)), int(resolution.group(2))
        except Exception:
            pass
        return 800, 600  # fallback

    def get_monitor_resolution(self):
        if sys.platform == "win32":
            return self.get_monitor_resolution_windows()
        elif sys.platform.startswith("linux"):
            return self.get_monitor_resolution_linux()
        else:
            return 800, 600  # fallback/default

    # Function to set up OpenGL with the current screen size
    def setup_screen(self, w, h):
        width, height = w, h

        # display_info = pygame.display.Info()
        # desktop_size = (display_info.current_w, display_info.current_h)



        if self.preferences['fullscreen']:
            self.screen = pygame.display.set_mode((0,0), DOUBLEBUF | OPENGL | FULLSCREEN)
            # self.move_window(0,0)
            width, height = self.get_monitor_resolution()
        else:
            self.screen = pygame.display.set_mode((w, h), DOUBLEBUF | OPENGL | RESIZABLE)


        # pygame.display.update()

        pygame.display.flip()  # Let SDL/OS process display mode change
        pygame.event.pump()  # Force processing window events

        # width, height = self.screen.get_size()
        # info = pygame.display.Info()
        # width = info.current_w
        # height = info.current_h
        # viewport = glGetIntegerv(GL_VIEWPORT)
        # x, y, width, height = viewport  # x, y are usually 0, 0

        # ratio = width / height
        # if self.sceneWidth is not None and self.sceneHeight is not None:
        #     self.camera.scale = int(width / self.sceneWidth if ratio < 1 else height / self.sceneHeight)
        # else: self.camera.scale = 1
        scale = 1
        if self.sceneWidth is not None and self.sceneHeight is not None:
            scale = math.ceil(max(width / self.sceneWidth, height / self.sceneHeight))
        self.camera.scale = max(scale, 1)  # Ensure never zero

        # Set viewport to window dimensions
        glViewport(0, 0, width, height)

        # Update screen dimensions
        self.screenWidth = width
        self.screenHeight = height
        self.camera.update_bounds(width, height)

        self.ortho_projection_matrix = self.create_ortho_projection_matrix()

        # Update screen size uniform in shaders
        glUseProgram(self.renderer.outline_shader)
        glUniform2f(self.renderer.outline_shader_uniforms["screenSize"], width, height)
        glUniformMatrix4fv(self.renderer.outline_shader_uniforms["projectionMatrix"],
                           1, GL_TRUE, self.ortho_projection_matrix)

        glUseProgram(self.renderer.default_shader)
        glUniform2f(self.renderer.default_shader_uniforms["screenSize"], width, height)
        glUniformMatrix4fv(self.renderer.default_shader_uniforms["projectionMatrix"],
                           1, GL_TRUE, self.ortho_projection_matrix)

        # Enable blending for texture transparency
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)


        glDisable(GL_MULTISAMPLE)

    def update(self, dt):
        cx, cy, lx, ly = self.world.map_manager.get_local_coords(self.player.position.x / TILE_SIZE, self.player.position.y / TILE_SIZE)
        # sim_range = math.ceil(max(screenWidth, screenHeight)/2/TILE_SIZE/self.map_manager.chunk_size) + 1
        self.world.environment.update(dt, cx, cy, 3, self.camera)

    def play_sound(self, category, name, variation=0, force_play=False, maxtime=0, fade=0):
        # Determine which sound we're about to play
        sound = self.sounds[category][name][variation % len(self.sounds[category][name])]

        # Check if it's a long/background sound (like 'music')
        if category == "music":
            # Only play if nothing's playing already
            if force_play:
                if self.currently_playing["music"]:
                    self.currently_playing["music"].stop()
                # Then play new music

            if not self.currently_playing.get("music") or not self.currently_playing["music"].get_busy():
                channel = sound.play(-1)  # loop music
                self.currently_playing["music"] = channel
        else:
            # Play short SFX without restrictions
            sound.play(maxtime=maxtime, fade_ms=fade)




    # ui