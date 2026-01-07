import shutil
from pathlib import Path

src = Path("Steiner_GA/GA072-Freiheit Unsterblichkeit Soziales Leben/GA072 (1.) DIE MENSCHENSEELE IM REICHE DES ÜBERSINNLICHEN UND IHR VERHÄLTNIS ZUM LEIB, Basel, 18. Oktober 1917 - Kopie.md")
dst = Path("Steiner_GA/GA072-Freiheit Unsterblichkeit Soziales Leben/GA072 (1.) DIE MENSCHENSEELE IM REICHE DES ÜBERSINNLICHEN UND IHR VERHÄLTNIS ZUM LEIB, Basel, 18. Oktober 1917.md")

shutil.copy(src, dst)
print("Backup wiederhergestellt")

