class Config:
    VIEW_LIST = [
        {"name": "Abdomen", "wl": 60, "ww": 400},
        {"name": "Angio", "wl": 300, "ww": 600},
        {"name": "Bone", "wl": 300, "ww": 1500},
        {"name": "Brain", "wl": 40, "ww": 80},
        {"name": "Chest", "wl": 40, "ww": 400},
        {"name": "Lungs", "wl": -400, "ww": 1500},
    ]
    DEFAULT_VIEW = 5

    REGISTER_ACTIVE = True
    SECRET_KEY = open(".secret_key", "rb").read()
    MAX_ADDITIONAL_SLICE_PER_DAY = 300
    MAX_PATIENT_PER_DAY = 600
