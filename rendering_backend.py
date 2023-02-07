import pygame

class backend_switch():
    def get_backend_ref(self):
        return pygame_backend()

class pygame_backend():

    def __new__(cls):
        if not hasattr(cls, 'instance'):
          cls.instance = super(pygame_backend, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        self._api = pygame

    def api(self):
        return self._api

