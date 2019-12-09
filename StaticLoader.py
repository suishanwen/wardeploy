import os

STATIC_LOADER = {}
APP = "app"
STATIC = "static"
for file in os.listdir(APP):
    path = f'{APP}/{file}'
    with open(path, 'r', encoding="utf-8") as fp:
        STATIC_LOADER[path] = fp.read()

for file in os.listdir(STATIC):
    path = f'{STATIC}/{file}'
    if path.find(".png") != -1:
        with open(path, 'rb') as fp:
            STATIC_LOADER[path] = fp.read()
    else:
        with open(path, 'r', encoding="utf-8") as fp:
            STATIC_LOADER[path] = fp.read().encode('utf-8')
