from core import models

activities = {
    "sleep": {
        "icon": "babybuddy/img/crib.svg",
        "color": "purple",
        "title": "Sleep",
        "model": models.Sleep,
    },
    "changes": {
        "icon": "babybuddy/img/diaper.svg",
        "color": "yellow",
        "title": "Diaper",
        "model": models.DiaperChange,
        "create_url": "mobile:changes-add",
    },
    "bottle": {
        "icon": "babybuddy/img/feeding.svg",
        "color": "green",
        "title": "Feeding",
        "model": models.Feeding,
    },
    "nursing": {
        "icon": "babybuddy/img/nursing.svg",
        "color": "green",
        "title": "Nursing",
        "model": models.Feeding,
    },
    "tummy": {
        "icon": "babybuddy/img/tummy.svg",
        "color": "purple",
        "title": "Tummy Time",
        "model": models.TummyTime,
    },
    "pumping": {
        "icon": "babybuddy/img/feeding.svg",
        "color": "green",
        "title": "Pumping",
        "model": models.Pumping,
    },
}
