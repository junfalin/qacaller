import os
import toml

if not os.path.exists('temp'):
    os.mkdir('temp')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class Cli:
    def __init__(self, file_name):
        if not file_name.endswith('.toml'):
            file_name += ".toml"
        self.toml_file_path = os.path.join(os.path.join(BASE_DIR, 'temp'), file_name)
        self.cfg_temp = self.read_cfg_temp()

    def read_cfg_temp(self):
        with open(os.path.join(BASE_DIR, "cfg_temp.toml"), "r", encoding="utf-8") as fs:
            t_data = toml.load(fs)
        return t_data

    def write(self):
        with open(self.toml_file_path, "w", encoding="utf-8") as fs:
            toml.dump(self.cfg_temp, fs)
