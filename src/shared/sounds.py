# Load sound paths from JSON
import json
import os

import pygame


def load_sounds_from_json(json_file):

    with open(json_file) as f:
        sound_map = json.load(f)

    sounds = {}
    for key, value in sound_map.items():
        if isinstance(value, dict):
            sounds[key] = {}
            for sub_key, sub_value in value.items():
                if isinstance(sub_value, list):
                    sounds[key][sub_key] = []
                    for entry in sub_value:
                        sounds[key][sub_key].append(pygame.mixer.Sound((os.path.join('assets/sounds', entry))))
                        print(f"Loaded sound: assets/sounds/{entry}")
                else:
                    sounds[key][sub_key] = pygame.mixer.Sound(os.path.join('assets/sounds', sub_value))
                    print(f"Loaded sound: assets/sounds/{sub_value}")

        else:
            sounds[key] = pygame.mixer.Sound(os.path.join('assets/sounds', value))
            print(f"Loaded sound: assets/sounds/{value}")

    return sounds


