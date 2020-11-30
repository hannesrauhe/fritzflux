from fritzflux import FritzFlux,DefaultFFConfig
import sys, json
from pathlib import Path,PurePath

config_dir = PurePath(Path.joinpath(Path.home(), ".fritzflux"))
config_path = Path.joinpath(config_dir, "fritzflux.conf")

def create_config(config_dict={}, extend=False):
    if not Path(config_path).exists() or extend:
        if not Path(config_dir).is_dir():
            Path(config_dir).mkdir()
        config_file = open(str(config_path), 'w')
        json.dump({**DefaultFFConfig,**config_dict}, config_file, indent=2)
        print("Created config file at %s. Please set values and restart."%config_path)
        sys.exit(0)

def read_config():
    create_config()
    config = {}
    with open(str(config_path), 'r') as config_file:
        config = json.load(config_file)

    keys_not_in_config = DefaultFFConfig.keys()-config.keys()
    if len(keys_not_in_config)>0:
        print("Please set following keys in config: ", keys_not_in_config)
        create_config(config, True)
    return config

if __name__ == '__main__':
    ffc = read_config()
    ff=FritzFlux(ffc)
    ff.push()
