import os

class EnvContextManager:
    def __init__(self, **kwargs):
        self.env_vars = kwargs

    def __enter__(self):
        self.old_values = {key: os.environ.get(key, "") for key in self.env_vars.keys()}
        os.environ.update(self.env_vars)

    def __exit__(self, exc_type, exc_value, exc_traceback):
        os.environ.update(self.old_values)