class Config:
    REGISTER_ACTIVE = True
    DATA_PATH = "path to the root directory of data"
    VIEW_LIST = [
        {"name": "Abdomen", "wl": 60, "ww": 400},
        {"name": "Angio", "wl": 300, "ww": 600},
        {"name": "Bone", "wl": 300, "ww": 1500},
        {"name": "Brain", "wl": 40, "ww": 80},
        {"name": "Chest", "wl": 40, "ww": 400},
        {"name": "Lungs", "wl": -400, "ww": 1500},
    ]
    DEFAULT_VIEW = 5
    SECRET_KEY = open(".secret_key").read()
    MAX_ADDITIONAL_PER_DAY = 24*10*10
