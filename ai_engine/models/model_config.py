
MODEL_CONFIG = {
    "project": "SkinTwin",

    "architecture": "SkinTwinUNetSmall",

    "input_channels": 3,
    "num_classes": 2,

    "class_names": {
        0: "background",
        1: "skin"
    },

    "input_size": 128,

    "optimizer": "Adam",
    "learning_rate": 0.001,

    "batch_size": 2,
    "epochs": 30,

    "device": "auto",

    "random_seed": 42
}
