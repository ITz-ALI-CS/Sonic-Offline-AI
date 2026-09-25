from PIL import Image, ImageDraw

size = 256
img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

draw.ellipse([8, 8, size-8, size-8], fill=(15, 17, 23, 255), outline=(0, 212, 255, 255), width=6)

bolt = [
    (150, 40), (95, 130), (130, 130),
    (100, 216), (165, 118), (128, 118)
]
draw.polygon(bolt, fill=(0, 212, 255, 255))

img.save("icon.ico", sizes=[(256,256),(128,128),(64,64),(32,32),(16,16)])
print("icon.ico created!")