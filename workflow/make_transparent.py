"""
Weißen Hintergrund aus einem Logo entfernen → transparentes PNG.
Verwendung: python3 make_transparent.py logo.jpg
"""
from PIL import Image
import sys
from pathlib import Path

def make_transparent(eingabe_pfad, schwellwert=230):
    img = Image.open(eingabe_pfad).convert("RGBA")
    daten = img.getdata()

    neu = []
    for r, g, b, a in daten:
        # Helle Pixel (Hintergrund) → transparent
        if r > schwellwert and g > schwellwert and b > schwellwert:
            neu.append((255, 255, 255, 0))
        else:
            neu.append((r, g, b, a))

    img.putdata(neu)
    ausgabe = Path(eingabe_pfad).stem + "_transparent.png"
    img.save(ausgabe, "PNG")
    print(f"✓ Gespeichert: {ausgabe}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Verwendung: python3 make_transparent.py dein_logo.jpg")
    else:
        make_transparent(sys.argv[1])
