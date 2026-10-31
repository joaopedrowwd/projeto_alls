from PIL import Image, ImageChops

ENTRADA = "site/app/static/img/logo.png"
SAIDA = "site/app/static/img/logo.png"

img = Image.open(ENTRADA).convert("RGBA")

# Considera "vazio" o que é transparente OU branco puro
fundo = Image.new("RGBA", img.size, (255, 255, 255, 255))
diff = ImageChops.difference(img, fundo)
alpha = img.getchannel("A").point(lambda a: 255 if a > 10 else 0)
caixa = ImageChops.lighter(diff.convert("L").point(lambda p: 255 if p > 10 else 0), alpha).getbbox()

if caixa:
    img = img.crop(caixa)
    print("Cortado para", img.size)
else:
    print("Nada para cortar")

img.save(SAIDA)