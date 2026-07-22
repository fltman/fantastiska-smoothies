# ART DIRECTION — Fantastiska smoothies

Visuell spec. Underordnad `CONTRACT.md` — vid konflikt vinner kontraktet alltid.
Klassnamnen här är exakt de i CONTRACT §5. Inga nya toppnivåklasser har uppfunnits.

**Känslan:** ett fruktstånd i solen. Varmt papper, generösa mjuka former, tyst
neutral scen — och så exploderar smoothiernas egna färger ur den. Vuxen lekfullhet:
stora självsäkra rubriker, inga clipart, inga utropstecken, ingen konfettiglädje som
skriker. Sajten ska göra någon sugen på tre sekunder.

**Grundprincip som styr allt annat:**
> Scenen är neutral och varm. Allt som är färgstarkt kommer från datan.
> CSS hårdkodar aldrig en smoothiefärg (CONTRACT §5). Enda undantaget är de neutrala
> reservvärdena för `--start`/`--slut`, som är scenens egna grå — inte fruktfärger.

---

## 0. Snabbreferens för agenterna

| Jag bygger | Läs |
|---|---|
| `assets/css/style.css` | Hela dokumentet. §1–§9 är normativa. |
| `index.php` | §5.1 hero, §5.2 galleri, §10.1–10.2 markup |
| `smoothie.php` | §5.3, §10.3 markup |
| `onska.php` / `om.php` / `404.php` | §5.5, §10.4 markup |
| `inc/smoothie-kort.php` | §5.2, §10.2, §1.4 (så sätts `--start`/`--slut`) |
| `inc/header.php` / `footer.php` | §5.4, §10.1 |

**Fyra saker att aldrig göra:**
1. Aldrig text ovanpå en mättad smoothiegradient. Text ligger på `--papper`, `--yta`
   eller en pastelltoning (§1.4). Då är kontrasten deterministisk.
2. Aldrig ett startläge med `opacity: 0` som bara en animation tar bort. Sajten ska
   fungera utan JS och under `prefers-reduced-motion`.
3. Aldrig en extern resurs. Inga fonter, ikoner, bilder eller script utifrån.
4. Aldrig en fast pixelhöjd på något som innehåller text.

---

## 1. Färgsystem

### 1.1 Scenen — ljust läge

Varmt, lite gräddvitt papper. Bläcket är brunsvart, aldrig rent `#000`.

```css
:root {
  color-scheme: light dark;

  --papper:      #FFF9F2;  /* sidbakgrund, varmt off-white */
  --yta:         #FFFFFF;  /* kort, receptkolumner, upphöjda ytor */
  --yta-hog:     #FFFFFF;  /* hovrad/aktiv yta (ljust läge: samma vita) */
  --blck:        #241A16;  /* all brödtext och alla rubriker */
  --dis:         #6B5A52;  /* sekundär text: meta, datum, noter */
  --ram:         #E7DACC;  /* dekorativa linjer, avdelare */
  --ram-stark:   #9C8779;  /* kontrollgränser (knapp, fält) — klarar 3:1 */
  --skugga:      28 16 10; /* rgb-komponenter för skuggor, varm brun */
  --slojja:      255 249 242; /* = --papper som rgb, för toningar mot kanten */
}
```

### 1.2 Scenen — mörkt läge

Samma varma temperatur, nedsläckt. Inte blå natt — ett mörkt trärum.

```css
@media (prefers-color-scheme: dark) {
  :root {
    --papper:    #17110F;
    --yta:       #221A17;
    --yta-hog:   #2C221E;
    --blck:      #FBF3EC;
    --dis:       #B7A69C;
    --ram:       #3A2D28;
    --ram-stark: #7A6C64;
    --skugga:    0 0 0;
    --slojja:    23 17 15;
  }
}
```

### 1.3 Kontroll — uträknade värden (WCAG, sRGB-relativ luminans)

Kravet i CONTRACT §9 är 4,5:1 på all text. Icke-textgränser mäts mot 3:1.

**Ljust läge**

| Kombination | Kontrast | Krav | Status |
|---|---|---|---|
| `--blck` på `--papper` | **16,27:1** | 4,5 | ✔ |
| `--blck` på `--yta` | **17,01:1** | 4,5 | ✔ |
| `--dis` på `--papper` | **6,26:1** | 4,5 | ✔ |
| `--dis` på `--yta` | **6,54:1** | 4,5 | ✔ |
| `--papper` på `--blck` (fylld knapp) | **16,27:1** | 4,5 | ✔ |
| `--ram-stark` på `--papper` (kontrollgräns) | **3,26:1** | 3,0 | ✔ |
| `--ram-stark` på `--yta` | **3,41:1** | 3,0 | ✔ |
| Fokusring (`--blck`) mot `--papper` | **16,27:1** | 3,0 | ✔ |

**Mörkt läge**

| Kombination | Kontrast | Krav | Status |
|---|---|---|---|
| `--blck` på `--papper` | **17,03:1** | 4,5 | ✔ |
| `--blck` på `--yta` | **15,58:1** | 4,5 | ✔ |
| `--blck` på `--yta-hog` | **14,12:1** | 4,5 | ✔ |
| `--dis` på `--papper` | **7,96:1** | 4,5 | ✔ |
| `--dis` på `--yta` | **7,29:1** | 4,5 | ✔ |
| `--papper` på `--blck` (fylld knapp) | **17,03:1** | 4,5 | ✔ |
| `--ram-stark` på `--papper` | **3,70:1** | 3,0 | ✔ |
| `--ram-stark` på `--yta` | **3,38:1** | 3,0 | ✔ |
| Fokusring (`--blck`) mot `--yta` | **15,58:1** | 3,0 | ✔ |

`--ram` (1,3:1) är rent dekorativ och bär aldrig information ensam. Alla
kontrollgränser använder `--ram-stark` eller `--blck`.

### 1.4 Smoothiens egna färger

Varje smoothie sätter `--start` och `--slut` inline på sitt yttersta element.
PHP-sidan gör detta — CSS får bara läsa dem.

```php
<?php $s = h_farg($sm['farger']['start']); $e = h_farg($sm['farger']['slut']); ?>
<article class="kort" style="--start:<?= $s ?>;--slut:<?= $e ?>">
```

`h_farg()` i `functions.php` måste validera mot `/^#[0-9A-Fa-f]{6}$/` och annars
returnera tom sträng (inga inline-värden alls) — då slår CSS-reserven in nedan.
Det är både en säkerhets- och en visuell spärr.

CSS deklarerar neutrala reservvärden på samma element. Inline-stilen vinner alltid
när den finns, så detta syns bara om datan saknas eller är trasig:

```css
/* Reserv = scenens egna neutraler, aldrig en påhittad fruktfärg. */
.kort, .smoothie, .hero__blobbar {
  --start: #E7DACC;
  --slut:  #9C8779;
}
```

**Härledda toningar.** Text får aldrig ligga på råa `--start`/`--slut`. När en yta
behöver smaka smoothie bakom text används pastellen:

```css
.kort, .smoothie {
  --pastell: color-mix(in oklab, var(--start) 14%, var(--yta));
  --pastell-slut: color-mix(in oklab, var(--slut) 14%, var(--yta));
}
@media (prefers-color-scheme: dark) {
  .kort, .smoothie {
    --pastell: color-mix(in oklab, var(--start) 22%, var(--yta));
    --pastell-slut: color-mix(in oklab, var(--slut) 22%, var(--yta));
  }
}
```

Kontrollräkning av pastellen i värsta fall (sRGB-approximation, konservativ — oklab
ger ljusare resultat i ljust läge och mörkare i mörkt läge, alltså mer marginal):

| Läge | Extremfärg som `--start` | Resulterande yta | `--blck` på den |
|---|---|---|---|
| Ljust | `#000000` (svartast tänkbara) | `#DBD6D0` | **11,78:1** ✔ |
| Ljust | `#FFE066` (klargul) | `#FFF6DE` | **15,79:1** ✔ |
| Ljust | `#2B1B6B` (mörkblå) | `#E1DADF` | **12,39:1** ✔ |
| Mörkt | `#FFFFFF` (ljusast tänkbara) | `#534C4A` | **7,65:1** ✔ |
| Mörkt | `#7CF7C0` (mintgrön) | `#364B3C` | **8,59:1** ✔ |
| Mörkt | `#FF3B00` (signalorange) | `#532112` | **12,00:1** ✔ |

Alltså: **`--blck` är alltid säker på en pastellyta, oavsett vilken färg datan ger.**

> **Regel:** på pastellytor används endast `--blck` som textfärg. `--dis` sjunker till
> 3,58:1 i mörkt läge mot ljusa pasteller och är därför förbjuden där.

Reserv för webbläsare utan `color-mix` (deklarera alltid den enkla raden först):

```css
.smak-etikett { background: var(--yta); background: var(--pastell); }
```

---

## 2. Typografi

### 2.1 Stackar — bara systemfonter

Rubriker använder `ui-rounded`, vilket ger SF Pro Rounded på macOS/iOS. Det är
sajtens största gratisvinst: mjuka, glada bokstavsformer utan en enda nedladdad byte.
Windows och Android faller till Segoe UI Variable Display respektive Roboto, som är
tighta och självsäkra i stora grader.

```css
:root {
  --typ-rubrik: ui-rounded, "SF Pro Rounded", -apple-system, BlinkMacSystemFont,
                "Segoe UI Variable Display", "Segoe UI", Roboto, "Helvetica Neue",
                Arial, sans-serif;
  --typ-brod:   system-ui, -apple-system, BlinkMacSystemFont,
                "Segoe UI Variable Text", "Segoe UI", Roboto, "Helvetica Neue",
                Arial, sans-serif;
  --typ-siffra: ui-monospace, SFMono-Regular, "SF Mono", "Cascadia Mono",
                "Segoe UI Mono", "Roboto Mono", Menlo, Consolas, monospace;
}
```

`--typ-siffra` används enbart till `ingrediens__mangd`, så att `1 dl` och `1½ msk`
radar upp sig i kolumn.

### 2.2 Skala — steg −1 till 6

Flytande via `clamp()`. Referensfönster: 360 px → 1440 px.

```css
:root {
  --steg--1: clamp(0.8125rem, 0.79rem + 0.11vw, 0.875rem);  /* 13 → 14 px */
  --steg-0:  clamp(1rem,      0.97rem + 0.14vw, 1.0625rem); /* 16 → 17 px */
  --steg-1:  clamp(1.125rem,  1.07rem + 0.25vw, 1.25rem);   /* 18 → 20 px */
  --steg-2:  clamp(1.3125rem, 1.20rem + 0.50vw, 1.5rem);    /* 21 → 24 px */
  --steg-3:  clamp(1.5rem,    1.28rem + 1.00vw, 2.125rem);  /* 24 → 34 px */
  --steg-4:  clamp(1.875rem,  1.47rem + 1.80vw, 3rem);      /* 30 → 48 px */
  --steg-5:  clamp(2.375rem,  1.66rem + 3.18vw, 4.25rem);   /* 38 → 68 px */
  --steg-6:  clamp(3rem,      1.65rem + 6.00vw, 6rem);      /* 48 → 96 px */

  --rad-tat:   1.02;  /* steg 5–6 */
  --rad-rubrik:1.12;  /* steg 2–4 */
  --rad-brod:  1.6;   /* steg 0–1 */
  --sparr-tat: -0.03em;
  --sparr-etikett: 0.08em;
}
```

Kontroll vid 360 px: `--steg-6` ≈ 49 px. "Fantastiska" på en rad ryms i 328 px
innehållsbredd med `--sparr-tat`. Hero-titeln får ändå `text-wrap: balance` och
`overflow-wrap: break-word` som skydd.

### 2.3 Roller

| Roll | Storlek | Familj | Vikt | Radavstånd | Sparrning |
|---|---|---|---|---|---|
| `hero__titel` | `--steg-6` | rubrik | 800 | `--rad-tat` | `--sparr-tat` |
| `smoothie__titel` | `--steg-5` | rubrik | 800 | `--rad-tat` | `--sparr-tat` |
| `galleri__rubrik`, `h2` | `--steg-4` | rubrik | 700 | `--rad-rubrik` | −0.02em |
| `kort__namn`, `recept__rubrik` | `--steg-2` | rubrik | 700 | `--rad-rubrik` | −0.015em |
| `hero__ingress`, `smoothie__underrubrik` | `--steg-1` | bröd | 400 | 1.45 | 0 |
| Brödtext, `steg`, `beskrivning` | `--steg-0` | bröd | 400 | `--rad-brod` | 0 |
| `kort__underrubrik` | `--steg-0` | bröd | 400 | 1.45 | 0 |
| `smak-etikett`, `etikett`, `meta-post` | `--steg--1` | bröd | 600 | 1.2 | `--sparr-etikett`, versaler |
| `ingrediens__mangd` | `--steg-0` | siffra | 500 | `--rad-brod` | 0 |
| `ingrediens__not`, `kort__onskad-av` | `--steg--1` | bröd | 400 kursiv | 1.4 | 0 |

Radlängd: `--matt-brod: 62ch` för löpande text, `--matt-rubrik: 16ch` för `--steg-5`
och `--steg-6`, `--matt-ingress: 46ch`.

```css
body { font: 400 var(--steg-0)/var(--rad-brod) var(--typ-brod);
       color: var(--blck); background: var(--papper);
       -webkit-text-size-adjust: 100%; text-rendering: optimizeLegibility; }
h1, h2, h3, .hero__titel, .smoothie__titel, .kort__namn, .recept__rubrik,
.galleri__rubrik { font-family: var(--typ-rubrik); text-wrap: balance; }
p, li { text-wrap: pretty; }
.ingrediens__mangd { font-family: var(--typ-siffra);
                     font-variant-numeric: tabular-nums; }
```

---

## 3. Rumslighet

### 3.1 Mellanrum

```css
:root {
  --rum-0: 0.25rem;  --rum-1: 0.5rem;   --rum-2: 0.75rem;  --rum-3: 1rem;
  --rum-4: 1.5rem;   --rum-5: 2rem;     --rum-6: 3rem;     --rum-7: 4.5rem;
  --rum-8: 6.5rem;
  --kant: clamp(1rem, 4vw, 2.5rem);   /* sidmarginal, 16 px vid 360 px */
  --sektion: clamp(3rem, 7vw, 6rem);  /* lodrätt mellan sektioner */
}
```

### 3.2 Radier — generösa och mjuka

```css
:root {
  --radie-0: 0.5rem;    /* etiketter, små ytor */
  --radie-1: 0.875rem;  /* fält, små knappar */
  --radie-2: 1.25rem;   /* knappar, önskeruta */
  --radie-3: 1.75rem;   /* kort, receptkolumner */
  --radie-4: 2.5rem;    /* bildrutor, hero-panel, smoothie__bild */
  --radie-rund: 999px;  /* piller: smak-etikett, hero__knapp */
}
```

Regel: ju större yta, desto större radie. En bildruta får aldrig mindre radie än
kortet den ligger i.

### 3.3 Skuggor

Varm brun skugga, aldrig grå. Två lager: en tät kontaktskugga plus en vid mjuk.

```css
:root {
  --lyft-0: 0 1px 2px rgb(var(--skugga) / 0.06);
  --lyft-1: 0 1px 2px rgb(var(--skugga) / 0.07),
            0 4px 12px -4px rgb(var(--skugga) / 0.10);
  --lyft-2: 0 2px 4px rgb(var(--skugga) / 0.08),
            0 12px 28px -8px rgb(var(--skugga) / 0.14);
  --lyft-3: 0 4px 8px rgb(var(--skugga) / 0.10),
            0 28px 56px -16px rgb(var(--skugga) / 0.20);
}
@media (prefers-color-scheme: dark) {
  :root {
    --lyft-0: 0 1px 2px rgb(0 0 0 / 0.35);
    --lyft-1: 0 1px 2px rgb(0 0 0 / 0.40), 0 4px 12px -4px rgb(0 0 0 / 0.45);
    --lyft-2: 0 2px 4px rgb(0 0 0 / 0.45), 0 12px 28px -8px rgb(0 0 0 / 0.55);
    --lyft-3: 0 4px 8px rgb(0 0 0 / 0.50), 0 28px 56px -16px rgb(0 0 0 / 0.65);
  }
}
```

I mörkt läge får varje upphöjd yta dessutom en hårfin ljus ovankant så att den lyfter
från bakgrunden: `box-shadow: var(--lyft-2), inset 0 1px 0 rgb(255 255 255 / 0.05);`

Färgad glöd (bara på hovrat kort, §5.2): `0 18px 40px -18px var(--start)`.

---

## 4. Rutnät och behållare

```css
.omslag { min-height: 100dvh; display: flex; flex-direction: column;
          overflow-x: clip; position: relative; }
.omslag > main { flex: 1; }
.bredd  { width: min(100% - var(--kant) * 2, var(--max, 76rem)); margin-inline: auto; }
.bredd--text { --max: 46rem; }
```

`overflow-x: clip` på `.omslag` är obligatoriskt — blobbarna sticker ut med flit och
CONTRACT §9 förbjuder horisontell scroll.

> `bredd--text` är den enda klass i detta dokument som inte står ordagrant i
> CONTRACT §5. Det är en modifierare av `bredd`, ingen ny toppnivåklass, och följer
> samma mönster som `knapp--stor` och `kort--onskad`. Den smalnar behållaren till
> läsbredd på textsidor. Inga andra tillägg finns eller får läggas till.

**Brytpunkter (bara tre, alltid `min-width`, alltid rem):**

| Namn | Värde | Vad som händer |
|---|---|---|
| liten | `40rem` (640 px) | galleriet → 2 kolumner; sidhuvudets meny på samma rad |
| mellan | `52rem` (832 px) | receptet → 2 kolumner; hero får luftigare mått |
| stor | `64rem` (1024 px) | galleriet → 3 kolumner; smoothietoppen → bild bredvid text |

---

## 5. Layout per yta

### 5.1 Hero (startsidan)

Full bredd, hög luft, ingen bild — blobbarna och typografin bär den.
Höjd: `min-block-size: clamp(24rem, 62vh, 34rem)`, aldrig `100vh`.

```css
.hero { position: relative; isolation: isolate;
        padding-block: var(--rum-7) var(--rum-8);
        display: grid; align-content: center; gap: var(--rum-4); }
.hero__titel   { font-size: var(--steg-6); font-weight: 800;
                 line-height: var(--rad-tat); letter-spacing: var(--sparr-tat);
                 max-inline-size: var(--matt-rubrik); margin: 0; }
.hero__ingress { font-size: var(--steg-1); color: var(--dis);
                 max-inline-size: var(--matt-ingress); margin: 0; }
.hero__knapp   { justify-self: start; }
```

Under titeln ligger det rinnande gradientstrecket (§6.3). Det är ett `::after` på
`.hero__titel` — ingen extra klass behövs.

`hero__knapp` är den enda primära handlingen på startsidan och leder till `onska.php`.
Text: "Önska en egen smoothie".

### 5.2 Galleri

```css
.galleri { display: grid; gap: var(--rum-5) var(--rum-4);
           grid-template-columns: 1fr; padding-block: var(--sektion); }
.galleri__rubrik { grid-column: 1 / -1; font-size: var(--steg-4);
                   margin: 0 0 var(--rum-1); }
@media (min-width: 40rem) { .galleri { grid-template-columns: repeat(2, minmax(0,1fr)); } }
@media (min-width: 64rem) { .galleri { grid-template-columns: repeat(3, minmax(0,1fr));
                                       gap: var(--rum-6) var(--rum-5); } }
```

**Kortet.** Ytan är `--yta`, aldrig gradienten. Gradienten syns i tre kontrollerade
doser: bandet överst, ljusgården bakom bilden och etiketternas pasteller.

```css
.kort { position: relative; background: var(--yta);
        border: 1px solid var(--ram); border-radius: var(--radie-3);
        box-shadow: var(--lyft-1); overflow: hidden;
        transition: transform var(--rorelse-mjuk) var(--lugn),
                    box-shadow var(--rorelse-mjuk) var(--lugn); }
.kort::before {                       /* gradientbandet, 6 px överst */
  content: ""; position: absolute; inset-block-start: 0; inset-inline: 0;
  block-size: 6px; background: linear-gradient(90deg, var(--start), var(--slut));
  z-index: 2; }
.kort__lank { display: grid; gap: var(--rum-3); color: inherit;
              text-decoration: none; padding-block-end: var(--rum-4); }
.kort__lank::after { content: ""; position: absolute; inset: 0; } /* hela kortet klickbart */
.kort__bildruta { position: relative; aspect-ratio: 1; overflow: hidden;
                  border-radius: var(--radie-3) var(--radie-3) var(--radie-4) var(--radie-4);
                  background: linear-gradient(150deg, var(--start), var(--slut)); }
.kort__bild { inline-size: 100%; block-size: 100%; object-fit: cover; display: block;
              transition: transform var(--rorelse-lang) var(--lugn); }
.kort__emoji { position: absolute; inset-block-end: var(--rum-2);
               inset-inline-end: var(--rum-2); font-size: var(--steg-3);
               line-height: 1; filter: drop-shadow(0 2px 6px rgb(0 0 0 / .35)); }
.kort__text  { display: grid; gap: var(--rum-1);
               padding-inline: var(--rum-4); }
.kort__namn  { font-size: var(--steg-2); margin: 0; }
.kort__underrubrik { color: var(--dis); margin: 0; }
.kort__profil { display: flex; flex-wrap: wrap; gap: var(--rum-1);
                list-style: none; margin: var(--rum-1) 0 0; padding: 0; }
.smak-etikett { font-size: var(--steg--1); font-weight: 600; text-transform: lowercase;
                letter-spacing: 0.01em; padding: 0.3em 0.75em;
                border-radius: var(--radie-rund);
                background: var(--yta); background: var(--pastell);
                color: var(--blck);
                border: 1px solid color-mix(in oklab, var(--start) 30%, transparent); }
.kort--onskad { border-color: var(--ram-stark); }
.kort__onskad-av { font-size: var(--steg--1); font-style: italic; color: var(--dis);
                   padding-inline: var(--rum-4); margin: 0; }
```

`kort--onskad` sätts när `onskad_av !== null`. Den skillnaden ska kännas som en liten
stolthet, inte som en varning: starkare ram plus raden `Önskad av Elsa` sist i kortet.

Bilden får `loading="lazy"` (utom de tre första korten som får `loading="eager"`),
`decoding="async"`, `width="1024" height="1024"`.

### 5.3 Smoothiesidan

**Toppen.** Mobilt: bild först, sedan text. Från 64rem: bild till vänster (klibbig),
text till höger.

```css
.smoothie__topp { display: grid; gap: var(--rum-5);
                  padding-block: var(--rum-6) var(--rum-7); }
@media (min-width: 64rem) {
  .smoothie__topp { grid-template-columns: minmax(0, 1fr) minmax(0, 1.05fr);
                    gap: var(--rum-7); align-items: start; }
  .smoothie__bild { position: sticky; inset-block-start: var(--rum-5); }
}
.smoothie__bild { inline-size: 100%; aspect-ratio: 1; object-fit: cover;
                  border-radius: var(--radie-4); box-shadow: var(--lyft-3);
                  background: linear-gradient(150deg, var(--start), var(--slut)); }
.smoothie__titel { font-size: var(--steg-5); margin: 0 0 var(--rum-2); }
.smoothie__underrubrik { font-size: var(--steg-1); color: var(--dis);
                         max-inline-size: var(--matt-ingress); margin: 0 0 var(--rum-4); }
.smoothie__beskrivning { max-inline-size: var(--matt-brod); font-size: var(--steg-1); }
.smoothie__meta { display: flex; flex-wrap: wrap; gap: var(--rum-1) var(--rum-2);
                  list-style: none; padding: 0; margin: var(--rum-4) 0 0; }
.meta-post { font-size: var(--steg--1); font-weight: 600; text-transform: uppercase;
             letter-spacing: var(--sparr-etikett); color: var(--blck);
             background: var(--yta); background: var(--pastell);
             padding: 0.45em 0.85em; border-radius: var(--radie-rund); }
```

`smoothie__meta` innehåller bara tillåtna siffror (CONTRACT §2): portioner, tid i
minuter, publiceringsdatum. Aldrig något annat mätvärde.

**Receptet — två spalter.** Vänster: ingredienser. Höger: gör så här, toppa med, knep.

```css
.recept { display: grid; gap: var(--rum-5);
          padding-block: var(--sektion);
          border-block-start: 1px solid var(--ram); }
@media (min-width: 52rem) {
  .recept { grid-template-columns: minmax(0, 0.95fr) minmax(0, 1.15fr);
            gap: var(--rum-7); align-items: start; }
}
.recept__kolumn { background: var(--yta); border: 1px solid var(--ram);
                  border-radius: var(--radie-3); padding: var(--rum-5);
                  box-shadow: var(--lyft-1); }
.recept__rubrik { font-size: var(--steg-2); margin: 0 0 var(--rum-3); }
.recept__rubrik + * { margin-block-start: 0; }

.ingredienslista { list-style: none; margin: 0; padding: 0; }
.ingrediens { display: grid; grid-template-columns: 5.5rem 1fr; gap: var(--rum-2);
              padding-block: var(--rum-2);
              border-block-end: 1px dashed var(--ram); }
.ingrediens:last-child { border-block-end: 0; }
.ingrediens__mangd { color: var(--dis); }
.ingrediens__vara  { font-weight: 500; }
.ingrediens__not   { grid-column: 2; font-size: var(--steg--1); font-style: italic;
                     color: var(--dis); }

.stegslista { list-style: none; counter-reset: steg; margin: 0; padding: 0;
              display: grid; gap: var(--rum-3); }
.steg { counter-increment: steg; display: grid;
        grid-template-columns: 2.25rem 1fr; gap: var(--rum-3); align-items: start; }
.steg::before { content: counter(steg); grid-row: 1 / 3;
                inline-size: 2.25rem; block-size: 2.25rem; display: grid;
                place-items: center; border-radius: var(--radie-rund);
                font-family: var(--typ-rubrik); font-weight: 700;
                font-size: var(--steg--1); color: var(--blck);
                background: var(--yta); background: var(--pastell);
                border: 1px solid color-mix(in oklab, var(--start) 35%, transparent); }

.toppning { list-style: none; margin: var(--rum-4) 0 0; padding: 0;
            display: flex; flex-wrap: wrap; gap: var(--rum-1); }
.toppning li { font-size: var(--steg-0); padding: 0.35em 0.8em;
               border: 1px solid var(--ram-stark); border-radius: var(--radie-rund); }
.knep { margin-block-start: var(--rum-4); padding: var(--rum-4);
        border-radius: var(--radie-2); border: 1px solid var(--ram);
        background: var(--yta); background: var(--pastell-slut);
        color: var(--blck); font-size: var(--steg-0); }
.knep::before { content: "Knep"; display: block; font-size: var(--steg--1);
                font-weight: 600; text-transform: uppercase;
                letter-spacing: var(--sparr-etikett); color: var(--blck);
                opacity: .7; margin-block-end: var(--rum-0); }
```

Ingrediensmängdernas kolumn är `5.5rem` — rymmer `1 ½ msk` utan brytning. Under
30rem viewport (§9.3) blir `.ingrediens` en kolumn med mängden ovanför varan.

**Önskerutan** visas bara när `onskad_av !== null`:

```css
.onskeruta { margin-block: var(--rum-5); padding: var(--rum-5);
             border-radius: var(--radie-3);
             border: 1px solid color-mix(in oklab, var(--start) 35%, var(--ram));
             background: var(--yta); background: var(--pastell); color: var(--blck); }
.onskeruta__citat { font-family: var(--typ-rubrik); font-size: var(--steg-2);
                    line-height: 1.25; margin: 0 0 var(--rum-2);
                    text-wrap: balance; }
.onskeruta__citat::before { content: "”"; }
.onskeruta__citat::after  { content: "”"; }
```

**Grannar** (förra/nästa smoothie), två länkkort i botten:

```css
.granne { display: grid; gap: var(--rum-3); padding-block: var(--sektion) 0;
          border-block-start: 1px solid var(--ram); }
@media (min-width: 40rem) { .granne { grid-template-columns: 1fr 1fr; } }
.granne a { display: grid; gap: var(--rum-0); padding: var(--rum-4);
            border-radius: var(--radie-2); border: 1px solid var(--ram);
            background: var(--yta); color: inherit; text-decoration: none;
            min-block-size: 44px; }
.granne a:last-child { text-align: end; }
```

### 5.4 Sidhuvud och sidfot

Sidhuvudet är lågt, klibbigt och nästan osynligt — innehållet ska äga skärmen.

```css
.hopp-till-innehall { position: absolute; inset-block-start: -100%;
                      inset-inline-start: var(--rum-3); z-index: 100;
                      padding: var(--rum-2) var(--rum-4);
                      background: var(--blck); color: var(--papper);
                      border-radius: 0 0 var(--radie-2) var(--radie-2); }
.hopp-till-innehall:focus { inset-block-start: 0; }

.sidhuvud { position: sticky; inset-block-start: 0; z-index: 30;
            background: rgb(var(--slojja) / 0.82);
            -webkit-backdrop-filter: blur(12px) saturate(1.4);
            backdrop-filter: blur(12px) saturate(1.4);
            border-block-end: 1px solid var(--ram); }
@supports not (backdrop-filter: blur(1px)) { .sidhuvud { background: var(--papper); } }
.sidhuvud > .bredd { display: flex; align-items: center;
                     justify-content: space-between; gap: var(--rum-3);
                     min-block-size: 3.5rem; }
.sidhuvud__logga { font-family: var(--typ-rubrik); font-weight: 800;
                   font-size: var(--steg-1); letter-spacing: -0.02em;
                   color: var(--blck); text-decoration: none;
                   display: inline-flex; align-items: center; gap: var(--rum-1);
                   min-block-size: 44px; }
.sidhuvud__meny { display: flex; gap: var(--rum-0); list-style: none;
                  margin: 0; padding: 0; }
.sidhuvud__meny a { display: inline-flex; align-items: center;
                    min-block-size: 44px; padding-inline: var(--rum-2);
                    border-radius: var(--radie-1); color: var(--dis);
                    text-decoration: none; font-weight: 500; }
.sidhuvud__meny a:hover { color: var(--blck); background: var(--ram); }
.sidhuvud__meny a[aria-current="page"] { color: var(--blck); font-weight: 600; }
```

Loggan är ordmärket "Fantastiska smoothies" — på under 30rem bara "Fantastiska"
plus resten i ett `<span class="visuellt-dold">`? **Nej.** Loggan förkortas aldrig i
markup; den krymper med `--steg-0` under 26rem. Text får inte försvinna för synhjälpmedel.

Menyn har högst tre poster (Smoothies, Önska, Om). Ingen hamburgare behövs — tre
44 px-mål ryms på 360 px.

```css
.sidfot { margin-block-start: var(--sektion);
          border-block-start: 1px solid var(--ram);
          padding-block: var(--rum-6) var(--rum-7);
          color: var(--dis); font-size: var(--steg--1);
          position: relative; }
.sidfot::before { /* prickkonfetti, §6.4 */ }
```

Sidfoten innehåller: en rad om vad sajten är, länk till `onska.php`, mailadressen
som `mailto:`, och tidpunkten datan uppdaterades. Inga sociala ikoner.

### 5.5 Önskesidan och innehållssidor

```css
.onska { padding-block: var(--sektion); }
.onska > * { max-inline-size: var(--matt-brod); }
.onska__steg { list-style: none; counter-reset: onskesteg; margin: var(--rum-5) 0;
               padding: 0; display: grid; gap: var(--rum-4); }
.onska__steg > li { counter-increment: onskesteg;
                    display: grid; grid-template-columns: 2.75rem 1fr;
                    gap: var(--rum-3); align-items: start; }
.onska__steg > li::before { content: counter(onskesteg);
                            inline-size: 2.75rem; block-size: 2.75rem;
                            display: grid; place-items: center;
                            border-radius: var(--radie-rund);
                            background: var(--blck); color: var(--papper);
                            font-family: var(--typ-rubrik); font-weight: 700; }
.onska__mailknapp { /* ärver .knapp .knapp--stor */ margin-block: var(--rum-5); }
.onska__exempel { padding: var(--rum-5); border-radius: var(--radie-3);
                  border: 1px dashed var(--ram-stark); background: var(--yta);
                  font-style: italic; }
```

`onska__mailknapp` är en `<a href="mailto:…">` med `.knapp .knapp--stor
.onska__mailknapp`. Mailadressen skrivs också ut som synlig text bredvid, för den
som inte har en mailklient kopplad.

### 5.6 Knappar och etiketter

```css
.knapp { display: inline-flex; align-items: center; justify-content: center;
         gap: var(--rum-1); min-block-size: 2.75rem;   /* 44 px */
         padding: 0.75rem 1.5rem; border-radius: var(--radie-rund);
         border: 1px solid transparent; background: var(--blck);
         color: var(--papper); font: 600 var(--steg-0)/1.2 var(--typ-brod);
         text-decoration: none; cursor: pointer; box-shadow: var(--lyft-1);
         transition: transform var(--rorelse-snabb) var(--studs),
                     box-shadow var(--rorelse-snabb) var(--lugn); }
.knapp:hover  { transform: translateY(-2px); box-shadow: var(--lyft-2); }
.knapp:active { transform: translateY(0); box-shadow: var(--lyft-0); }
.knapp--stor  { font-size: var(--steg-1); padding: 1rem 2rem; min-block-size: 3.25rem; }
.knapp--tyst  { background: transparent; color: var(--blck);
                border-color: var(--ram-stark); box-shadow: none; }
.knapp--tyst:hover { background: var(--yta); box-shadow: var(--lyft-1); }

.etikett { display: inline-block; font-size: var(--steg--1); font-weight: 600;
           text-transform: uppercase; letter-spacing: var(--sparr-etikett);
           color: var(--dis); }

.visuellt-dold { position: absolute !important; inline-size: 1px; block-size: 1px;
                 padding: 0; margin: -1px; overflow: hidden;
                 clip-path: inset(50%); white-space: nowrap; border: 0; }
```

---

## 6. Signaturgrepp (exakt fyra)

Dessa fyra, och inga fler, är det som gör sajten till just den här sajten.

### 6.1 Blobbhavet — hero__blobbar / blobb

Tre stora mjuka färgmoln som driver långsamt bakom hero-texten. Färgerna kommer från
de tre nyaste smoothiernas `--start`/`--slut` — sajtens bakgrund byts alltså av sig
själv varje gång generatorn kör. Det är greppet som binder ihop data och känsla.

PHP (`index.php`) skickar in färgerna:

```php
<div class="hero__blobbar" aria-hidden="true">
  <?php foreach (array_slice($smoothies, 0, 3) as $b): ?>
    <span class="blobb" style="--start:<?= h_farg($b['farger']['start']) ?>;
                               --slut:<?= h_farg($b['farger']['slut']) ?>"></span>
  <?php endforeach; ?>
</div>
```

```css
.hero__blobbar { position: absolute; inset: -10% -20% auto; block-size: 130%;
                 z-index: -1; overflow: hidden; pointer-events: none;
                 filter: blur(60px) saturate(1.15); opacity: 0.55;
                 -webkit-mask-image: radial-gradient(120% 100% at 50% 30%,
                                     #000 40%, transparent 78%);
                 mask-image: radial-gradient(120% 100% at 50% 30%,
                             #000 40%, transparent 78%); }
@media (prefers-color-scheme: dark) { .hero__blobbar { opacity: 0.38; } }

.blobb { position: absolute; inline-size: 46vmax; aspect-ratio: 1;
         border-radius: 46% 54% 38% 62% / 58% 42% 60% 40%;
         background: radial-gradient(circle at 35% 35%, var(--start), var(--slut) 72%);
         will-change: transform;
         animation: driva var(--tid, 64s) var(--mjukt-fram-tillbaka) infinite alternate; }
.blobb:nth-child(1) { inset-block-start: -14%; inset-inline-start: -8%;  --tid: 58s; }
.blobb:nth-child(2) { inset-block-start:  18%; inset-inline-start: 52%;  --tid: 71s;
                      animation-delay: -18s; }
.blobb:nth-child(3) { inset-block-start:  46%; inset-inline-start: 16%;  --tid: 86s;
                      animation-delay: -37s; inline-size: 34vmax; }

@keyframes driva {
  from { transform: translate3d(0, 0, 0) scale(1)    rotate(0deg); }
  to   { transform: translate3d(6vw, -4vh, 0) scale(1.14) rotate(24deg); }
}
```

`filter: blur()` på behållaren i stället för på varje blobb halverar antalet lager
kompositorn måste hantera. `.hero { isolation: isolate }` gör att `z-index: -1` stannar
bakom hero-texten men framför sidbakgrunden.

### 6.2 Kortlyftet — kort / kort__bildruta / kort__bild

Kortet lyfter, tiltar en halv grad och tänder en glöd i smoothiens egen färg. Bilden
zoomar sakta inuti sin ruta. Tilten är avsiktligt liten: 0,5° läses som liv, 2° som
leksak.

```css
@media (hover: hover) and (pointer: fine) {
  .kort:hover, .kort:focus-within {
    transform: translateY(-6px) rotate(-0.5deg) scale(1.012);
    box-shadow: var(--lyft-3), 0 18px 40px -18px var(--start);
    border-color: color-mix(in oklab, var(--start) 40%, var(--ram));
  }
  .kort:nth-child(even):hover,
  .kort:nth-child(even):focus-within { rotate: 0.5deg; } /* varannan åt andra hållet */
  .kort:hover .kort__bild,
  .kort:focus-within .kort__bild { transform: scale(1.05); }
  .kort:active { transform: translateY(-2px) scale(1.004); }
}
```

Kravet `pointer: fine` gör att inget hoppar till på pekskärm, där `:hover` fastnar.
`:focus-within` gör att tangentbordsanvändare får exakt samma glädje.

### 6.3 Det rinnande strecket — hero__titel / smoothie__titel

En bred gradientremsa under rubriken, med `background-size: 300%` och en långsam
förskjutning av `background-position`. Färgerna rinner sakta fram och tillbaka som
mixerns virvel. **Texten ligger aldrig i gradienten**, bara ovanför den — därför är
kontrasten oförändrad 16,27:1.

```css
.hero__titel::after,
.smoothie__titel::after {
  content: ""; display: block; block-size: 0.5rem;
  inline-size: min(12rem, 42%); margin-block-start: var(--rum-3);
  border-radius: var(--radie-rund);
  background: linear-gradient(90deg, var(--start), var(--slut),
                              var(--start), var(--slut));
  background-size: 300% 100%;
  animation: rinna 14s var(--mjukt-fram-tillbaka) infinite alternate; }
@keyframes rinna { from { background-position: 0% 50%; }
                   to   { background-position: 100% 50%; } }
```

På startsidan ärver `.hero__titel` färgerna från `.hero__blobbar`s första barn —
enklast genom att `index.php` sätter `--start`/`--slut` även på `.hero`-elementet med
den nyaste smoothiens färger. Samma remsa återkommer på `galleri__rubrik` (utan
animation, 4 rem bred) som en tyst rim.

### 6.4 Prickkonfettin — sidfot, onska, 404

En glesa prickraster i bläckfärg, maskad så att den tonar bort. Ger papperskänsla
utan en enda bildfil. Aldrig bakom brödtext med full täckning — max 6 % opacitet.

```css
.sidfot::before, .onska::before {
  content: ""; position: absolute; inset: 0; z-index: -1; pointer-events: none;
  background-image: radial-gradient(circle at center,
                    color-mix(in oklab, var(--blck) 55%, transparent) 1.5px,
                    transparent 1.6px);
  background-size: 22px 22px;
  opacity: 0.10;
  -webkit-mask-image: linear-gradient(180deg, transparent, #000 60%);
  mask-image: linear-gradient(180deg, transparent, #000 60%); }
@media (prefers-color-scheme: dark) { .sidfot::before, .onska::before { opacity: 0.14; } }
```

`.sidfot` och `.onska` behöver `position: relative; isolation: isolate;`.

> **Inget femte grepp.** Ingen parallax, ingen scrollanimation, inga svävande frukter,
> ingen mus-följande markör. Fyra räcker och gör helheten sammanhållen.

---

## 7. Rörelse

### 7.1 Tokens

```css
:root {
  --rorelse-snabb: 140ms;  /* knapptryck, färgbyte */
  --rorelse-mjuk:  260ms;  /* kortlyft, fokusring */
  --rorelse-lang:  520ms;  /* bildzoom */
  --lugn:  cubic-bezier(0.2, 0.7, 0.3, 1);      /* standard in/ut */
  --studs: cubic-bezier(0.34, 1.4, 0.5, 1);     /* knappar, lekfullt */
  --mjukt-fram-tillbaka: cubic-bezier(0.45, 0.05, 0.55, 0.95); /* loopar */
}
```

### 7.2 Vad som får röra sig

| Vad | Egenskap | Tid | Easing |
|---|---|---|---|
| `.blobb` | `transform` | 58 / 71 / 86 s, `alternate` | `--mjukt-fram-tillbaka` |
| Rubrikstreck | `background-position` | 14 s, `alternate` | `--mjukt-fram-tillbaka` |
| `.kort` hover | `transform`, `box-shadow`, `border-color` | 260 ms | `--lugn` |
| `.kort__bild` hover | `transform` | 520 ms | `--lugn` |
| `.knapp` hover/active | `transform`, `box-shadow` | 140 ms | `--studs` |
| Länkar, meny | `color`, `background-color` | 140 ms | `--lugn` |
| Fokusring | `outline-offset` | 140 ms | `--lugn` |

Bara `transform`, `opacity`, `box-shadow`, `background-position` och färg animeras —
aldrig `width`, `height`, `top` eller `margin`. Inga `@scroll-timeline`, ingen
`IntersectionObserver`-inflygning.

### 7.3 Avstängning

Ett enda block, sist i filen, som stänger av allt:

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important; }

  .blobb { animation: none !important;
           transform: none !important; }            /* står stilla i utgångsläget */
  .hero__titel::after, .smoothie__titel::after {
           animation: none !important;
           background-position: 0% 50% !important; }
  .kort:hover, .kort:focus-within,
  .kort:nth-child(even):hover, .kort:nth-child(even):focus-within {
           transform: none !important; rotate: 0 !important; }
  .kort:hover .kort__bild, .kort:focus-within .kort__bild {
           transform: none !important; }
  .knapp:hover, .knapp:active { transform: none !important; }
}
```

Hovertillstånd försvinner inte — de blir bara statiska: kortet behåller sin glöd och
starkare ram, knappen sin djupare skugga. Återkopplingen finns kvar, rörelsen inte.

JS (`assets/js/app.js`) får aldrig animera något utan att först fråga:

```js
const stilla = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
```

---

## 8. Fokus, tryckytor och tangentbord

### 8.1 Fokusmarkering

En enda markering i hela sajten, i bläckfärg, med en ljus ytterring så att den syns
även ovanpå en mättad bildruta.

```css
:where(a, button, input, textarea, select, summary, [tabindex]):focus-visible {
  outline: 3px solid var(--blck);
  outline-offset: 3px;
  border-radius: var(--radie-1);
  box-shadow: 0 0 0 6px var(--papper); }
.kort__lank:focus-visible { outline-offset: 5px; border-radius: var(--radie-3); }
.knapp:focus-visible { border-radius: var(--radie-rund); }
:focus:not(:focus-visible) { outline: none; }
```

Kontrast ring/bakgrund: 16,27:1 ljust, 17,03:1 mörkt — långt över kravet 3:1.
Ringen är alltid minst 3 px och alltid utanför elementet, aldrig en inåtgående glow.

`.kort__lank::after` täcker hela kortet, så tangentbordsfokus på kortlänken markerar
hela kortet. Kortet får därför **inte** `overflow: hidden` som klipper ringen —
lösning: `.kort { overflow: clip; overflow-clip-margin: 8px; }` så att bandet och
bildzoomen fortfarande klipps men fokusringen syns.

### 8.2 Tryckytor

Minst **44 × 44 px** för allt klickbart. Gäller: `.knapp`, `.sidhuvud__meny a`,
`.sidhuvud__logga`, `.granne a`, `.onska__mailknapp`, alla länkar i `.sidfot`.

```css
.sidfot a { display: inline-flex; align-items: center; min-block-size: 44px;
            padding-inline-end: var(--rum-1); }
```

Vertikalt avstånd mellan två intilliggande mål: minst `--rum-1` (8 px).
Inline-länkar i löpande text är undantagna (WCAG 2.5.8), men får understrykning med
`text-underline-offset: 0.18em; text-decoration-thickness: from-font;`.

### 8.3 Länkstil i brödtext

```css
main a:not(.knapp):not(.kort__lank):not(.granne a) {
  color: var(--blck); text-decoration: underline;
  text-decoration-color: var(--ram-stark); text-underline-offset: 0.18em;
  text-decoration-thickness: 2px; }
main a:hover { text-decoration-color: var(--blck); }
```

Färg bär aldrig information ensam — understrykningen gör länken identifierbar.

---

## 9. Små skärmar

### 9.1 Galleriet på 360 px

- `--kant` = 16 px → innehållsbredd 328 px.
- En kolumn. Kortet blir 328 px brett, bildrutan 328 × 328 px.
- `kort__namn` ≈ 21 px, `kort__underrubrik` 16 px/1,45 — cirka två rader.
- `kort__profil`: 2–4 etiketter à ~76 px bryter till högst två rader.
- Radavstånd mellan kort: `--rum-5` (32 px). Det syns tydligt att korten är enheter.
- Ingen hovereffekt (blockeras av `pointer: fine`), men `:active` ger en 2 px
  nedtryckning så att tapet känns.
- Totalhöjd per kort ≈ 328 + 150 ≈ 478 px. Man ser ett helt kort plus toppen av nästa
  — det är precis vad som ska få någon att fortsätta rulla.

### 9.2 Hero på 360 px

`hero__titel` ≈ 49 px över tre rader, `hero__ingress` 18 px över tre rader, knappen
52 px hög. Sammanlagt ryms hela heron plus första kortets ovankant i 640 px höjd.

### 9.3 Under 30 rem (480 px)

```css
@media (max-width: 30rem) {
  .ingrediens { grid-template-columns: 1fr; gap: var(--rum-0); }
  .ingrediens__not { grid-column: 1; }
  .recept__kolumn { padding: var(--rum-4); }
  .smoothie__meta { gap: var(--rum-1); }
}
@media (max-width: 26rem) {
  .sidhuvud__logga { font-size: var(--steg-0); }
  .sidhuvud__meny a { padding-inline: var(--rum-1); }
}
```

### 9.4 Överskridningsskydd

```css
img, svg, video { max-inline-size: 100%; block-size: auto; }
.hero__titel, .smoothie__titel, .kort__namn { overflow-wrap: break-word; hyphens: auto; }
html { -webkit-text-size-adjust: 100%; }
```

Testviewporter innan något kallas klart: **360**, 390, 414, 768, 1024, 1440 px — i
både ljust och mörkt läge, och en gång med `prefers-reduced-motion: reduce`.

---

## 10. Markupskelett (normativt för PHP-agenterna)

Klassnamnen nedan är exakt CONTRACT §5. Elementvalen är del av specen: rätt semantik
är en del av designen. All utdata går genom `h()`.

### 10.1 Ram (header.php / footer.php)

```html
<body>
  <div class="omslag">
    <a class="hopp-till-innehall" href="#innehall">Hoppa till innehållet</a>
    <header class="sidhuvud">
      <div class="bredd">
        <a class="sidhuvud__logga" href="/">🥤 Fantastiska smoothies</a>
        <nav aria-label="Huvudmeny">
          <ul class="sidhuvud__meny">
            <li><a href="/">Smoothies</a></li>
            <li><a href="/onska">Önska</a></li>
            <li><a href="/om">Om</a></li>
          </ul>
        </nav>
      </div>
    </header>
    <main id="innehall">
      <!-- sidans innehåll -->
    </main>
    <footer class="sidfot">
      <div class="bredd"> … </div>
    </footer>
  </div>
</body>
```

### 10.2 Kort (inc/smoothie-kort.php)

```html
<article class="kort kort--onskad" style="--start:#F5A623;--slut:#E0417B">
  <a class="kort__lank" href="/smoothie/solnedgang-i-mango">
    <div class="kort__bildruta">
      <img class="kort__bild" src="assets/bilder/solnedgang-i-mango.webp"
           alt="…" width="1024" height="1024" loading="lazy" decoding="async">
      <span class="kort__emoji" aria-hidden="true">🥭</span>
    </div>
    <div class="kort__text">
      <h3 class="kort__namn">Solnedgång i mango</h3>
      <p class="kort__underrubrik">…</p>
      <ul class="kort__profil">
        <li class="smak-etikett">tropisk</li>
        <li class="smak-etikett">krämig</li>
      </ul>
    </div>
  </a>
  <p class="kort__onskad-av">Önskad av Elsa</p>
</article>
```

`kort--onskad` och `kort__onskad-av` skrivs bara ut när `onskad_av !== null`.
`kort__onskad-av` ligger **utanför** `kort__lank` men innanför `kort`.

### 10.3 Smoothiesidan (smoothie.php)

```html
<article class="smoothie bredd" style="--start:…;--slut:…">
  <div class="smoothie__topp">
    <img class="smoothie__bild" src="…" alt="…" width="1024" height="1024">
    <div>
      <h1 class="smoothie__titel">…</h1>
      <p class="smoothie__underrubrik">…</p>
      <div class="smoothie__beskrivning"><p>…</p></div>
      <ul class="smoothie__meta">
        <li class="meta-post">2 portioner</li>
        <li class="meta-post">5 minuter</li>
        <li class="meta-post">22 juli 2026</li>
      </ul>
      <!-- onskeruta här om onskad_av !== null -->
    </div>
  </div>

  <div class="recept">
    <section class="recept__kolumn">
      <h2 class="recept__rubrik">Det här behövs</h2>
      <ul class="ingredienslista">
        <li class="ingrediens">
          <span class="ingrediens__mangd">1 dl</span>
          <span class="ingrediens__vara">vispgrädde</span>
          <span class="ingrediens__not">eller kokosgrädde</span>
        </li>
      </ul>
    </section>
    <section class="recept__kolumn">
      <h2 class="recept__rubrik">Gör så här</h2>
      <ol class="stegslista">
        <li class="steg">…</li>
      </ol>
      <h3 class="recept__rubrik">Toppa med</h3>
      <ul class="toppning"><li>…</li></ul>
      <p class="knep">…</p>
    </section>
  </div>

  <nav class="granne" aria-label="Fler smoothies">
    <a href="…"><span class="etikett">Förra</span> Namn</a>
    <a href="…"><span class="etikett">Nästa</span> Namn</a>
  </nav>
</article>
```

`ingrediens__not` utelämnas helt när `not === null` (inget tomt element).

### 10.4 Önskesidan (onska.php)

```html
<section class="onska bredd bredd--text">
  <h1>Önska en egen smoothie</h1>
  <p>…</p>
  <ol class="onska__steg">
    <li>…</li>
  </ol>
  <a class="knapp knapp--stor onska__mailknapp" href="mailto:smoothies@bjarby.com">
    Skriv till smoothies@bjarby.com</a>
  <div class="onska__exempel">…</div>
</section>
```

---

## 11. CSS-filens ordning

`assets/css/style.css` skrivs i exakt den här ordningen. En fil, inga importer.

1. Reset (`box-sizing`, marginaler, `img`-defaults, `:target` scroll-margin)
2. `:root` — färg, typ, rum, radie, skugga, rörelse
3. `@media (prefers-color-scheme: dark)` — bara omdefinierade färgvariabler
4. Bas (`html`, `body`, rubriker, `p`, listor, länkar)
5. Hjälpare (`bredd`, `visuellt-dold`, `hopp-till-innehall`, `etikett`, `knapp*`)
6. Layout (`omslag`, `sidhuvud`, `sidfot`)
7. Hero + blobbar
8. Galleri + kort
9. Smoothiesidan
10. Önskesidan
11. Fokus
12. Små skärmar (`max-width`-block)
13. `@media print`
14. `@media (prefers-reduced-motion: reduce)` — **absolut sist**

Riktmärke: under 16 kB oförkortad. Blir den större har någon lagt till ett femte grepp.

### 11.1 Utskrift

Receptet ska kunna skrivas ut och tejpas på kylskåpet.

```css
@media print {
  .sidhuvud, .sidfot, .granne, .hero__blobbar, .onska__exempel { display: none; }
  .kort, .recept__kolumn { box-shadow: none; border: 1px solid #999; }
  .recept { grid-template-columns: 1fr 1fr; }
  body { background: #fff; color: #000; }
  a[href^="http"]::after { content: " (" attr(href) ")"; font-size: 0.8em; }
}
```

---

## 12. Ordval i gränssnittet

Designen bär samma regel som texten (CONTRACT §2). Fasta strängar i markup:

| Yta | Text |
|---|---|
| Hero-knapp | Önska en egen smoothie |
| Galleri-rubrik | Alla smoothies · Nyast först |
| Receptkolumn 1 | Det här behövs |
| Receptkolumn 2 | Gör så här |
| Toppning | Toppa med |
| Knep | Knep |
| Grannar | Förra / Nästa |
| Kort med önskemål | Önskad av *Förnamn* |
| Meta | *n* portioner · *n* minuter · *datum* |
| Skiplänk | Hoppa till innehållet |
| 404 | Den smoothien finns inte. Men de här finns. |

Aldrig i något gränssnittselement: näringsord, siffror om kroppen, "nyttig", "boost",
"unna dig", "guilt free". Aldrig en ikon som föreställer en våg, ett hjärta med puls,
ett mål eller en bock i en ruta.
