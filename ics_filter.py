#!/usr/bin/env python3
"""Filtert einen Uni-ICS-Feed (URL oder lokale Datei).

Behalten werden Termine, deren Notizen (DESCRIPTION) leer sind
oder die Gruppe LP1 enthalten.

Nutzung:
    python3 ics_filter.py "https://uni.example/plan.ics" LP1 meine_gruppe.ics
    python3 ics_filter.py plan.ics LP1 meine_gruppe.ics
"""
import re
import sys
import urllib.request

quelle, gruppe, ausgabe = sys.argv[1], sys.argv[2], sys.argv[3]

# True: auch Termine behalten, deren Notizen KEINE Gruppe (LPx) nennen
BEHALTE_NOTIZEN_OHNE_GRUPPE = True
GRUPPEN_MUSTER = r"\bLP\d+\b"

if quelle.startswith("http"):
    import time
    anfrage = urllib.request.Request(quelle, headers={
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                      "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
        "Accept": "text/calendar,*/*",
    })
    for versuch in range(4):
        try:
            roh = urllib.request.urlopen(anfrage, timeout=30).read()
            break
        except Exception as fehler:
            print(f"Versuch {versuch + 1} fehlgeschlagen: {fehler}")
            if versuch == 3:
                raise
            time.sleep(10)
else:
    roh = open(quelle, "rb").read()
text = roh.decode("utf-8", errors="replace").replace("\r\n", "\n")
text = re.sub(r"\n[ \t]", "", text)  # gefaltete Zeilen zusammenfügen

kopf = text.split("BEGIN:VEVENT")[0]
events = re.findall(r"BEGIN:VEVENT.*?END:VEVENT", text, flags=re.S)


def notizen(ev):
    ev = re.sub(r"BEGIN:VALARM.*?END:VALARM\n?", "", ev, flags=re.S)  # Erinnerungen ignorieren
    m = re.search(r"^DESCRIPTION[^:\n]*:(.*)$", ev, flags=re.M)
    return m.group(1).strip() if m else ""


treffer = []
for ev in events:
    n = notizen(ev)
    if not n or re.search(rf"\b{re.escape(gruppe)}\b", n):
        treffer.append(ev)
    elif BEHALTE_NOTIZEN_OHNE_GRUPPE and not re.search(GRUPPEN_MUSTER, n):
        treffer.append(ev)

with open(ausgabe, "w", encoding="utf-8", newline="") as f:
    f.write(kopf.rstrip().replace("\n", "\r\n") + "\r\n")
    f.write("\r\n".join(e.replace("\n", "\r\n") for e in treffer) + "\r\n")
    f.write("END:VCALENDAR\r\n")

print(f"{len(treffer)} von {len(events)} Terminen behalten.")
