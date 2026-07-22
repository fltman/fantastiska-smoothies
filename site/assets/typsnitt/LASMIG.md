# Typsnitt

Sajten laddar inga typsnitt från tredje part. De två filerna här är
självhostade, så att inget anrop går till Google när någon besöker sidan.

| Typsnitt | Används till | Licens |
|---|---|---|
| **Fredoka** | rubriker | SIL Open Font License 1.1 — `OFL-Fredoka.txt` |
| **Nunito** | brödtext | SIL Open Font License 1.1 — `OFL-Nunito.txt` |

Båda är variabla (Fredoka vikt 300–700, Nunito 400–800), delade i `latin` och
`latin-ext` med `unicode-range`, så att en svensk besökare bara hämtar den
första. Laddas med `font-display: swap`: texten ritas direkt i systemfonten och
byts när filen landat, så sidan aldrig står tom och väntar.

OFL kräver att licensen följer med filerna. Ta inte bort `OFL-*.txt`.
