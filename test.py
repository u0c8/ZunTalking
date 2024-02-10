from psd_tools import PSDImage

path = "image\\zundamon__.psd"
psd = PSDImage.open(path)
# psd.compose().save('example.png')

visible_parts = [
    "v1.ずんだもん/まゆ/ちょい眉",
    "v1.ずんだもん/目/にこ～",
    "v1.ずんだもん/口/笑顔の口",
    "v1.ずんだもん/ほっぺ・顔色/通常",
    # "v1.ずんだもん/触覚/通常触覚",
    # "v1.ずんだもん/腕/通常下げ腕",
    # ""
]

def convert_layer(part, psd : PSDImage):
    correct_part : str = part[3:]
    parts = correct_part.split("/")
    for layer in psd:
        if layer.name in parts:
            for layer2 in layer:
                print(layer2)
    return parts

def visible_layer(group, parts):
    for layer in psd:
        if layer.name in parts:
            # これがグループかレイヤーか

# for layer in psd:
#     print(layer.name)
convert_layer(visible_parts[0], psd)