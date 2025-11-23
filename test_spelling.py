#!/usr/bin/env python3
"""Test ob Rechtschreibkorrekturen funktionieren"""

from rechtschreibregeln import korrigiere_rechtschreibung

test = "daß muß Bewußtsein wußte"
result = korrigiere_rechtschreibung(test)
print(f"Test: {test}")
print(f"Ergebnis: {result}")
print(f"Erwartet: dass muss Bewusstsein wusste")
print(f"Korrekt: {result == 'dass muss Bewusstsein wusste'}")

