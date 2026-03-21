import fitz
import sys

path = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA_pdf\ga068a.pdf"
doc = fitz.open(path)
print(f"Seiten: {doc.page_count}")

for pi in [0, 1, doc.page_count // 2]:
    p = doc[pi]
    imgs = p.get_images(full=True)
    text = p.get_text()
    print(f"\n--- Seite {pi+1} ---")
    print(f"Bilder: {len(imgs)}, Text: {len(text)} Zeichen")
    for img in imgs[:3]:
        xref = img[0]
        info = doc.extract_image(xref)
        ext = info["ext"]
        w = info["width"]
        h = info["height"]
        size_kb = len(info["image"]) // 1024
        print(f"  Bild xref={xref}: {w}x{h} {ext} {size_kb}KB")
    if text.strip():
        print(f"  Text: {text[:150].strip()}")
    else:
        print("  (kein Text)")

doc.close()
