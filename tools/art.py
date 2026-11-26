from pathlib import Path
from PIL import Image
base=Path(__file__).resolve().parents[1]
dest=base/'app'/'pictures';dest.mkdir(exist_ok=True)
turtle=Image.open(base/'art/turtle.png').convert('RGBA')
sheep=Image.open(base/'art/sheep.png').convert('RGBA')
for k in (1,2):
    base_layer=Image.new('RGBA',(160*k,160*k))
    stamp=turtle.copy();stamp.thumbnail((103*k,80*k),Image.Resampling.LANCZOS)
    base_layer.alpha_composite(stamp,((base_layer.width-stamp.width)//2,(base_layer.height-stamp.height)//2))
    for a in range(0,360,10):
        img=base_layer.rotate(a,resample=Image.Resampling.BICUBIC).resize((80*k,80*k),Image.Resampling.LANCZOS)
        img.save(dest/f'turtle_{k}_{a}.png')
    im=sheep.copy();im.thumbnail((74*k,60*k),Image.Resampling.LANCZOS);im.save(dest/f'sheep_{k}.png')
small=turtle.copy();small.thumbnail((44,38),Image.Resampling.LANCZOS);small.save(dest/'brand.png')
ic=Image.new('RGBA',(256,256),'#E6F3DD');si=turtle.copy();si.thumbnail((220,210),Image.Resampling.LANCZOS);ic.alpha_composite(si,((256-si.width)//2,(256-si.height)//2));ic.save(dest/'studio.ico',sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)])
