# CONTRACT — Fantastiska smoothies

Detta dokument är bibeln. Sajt, generator och bilder byggs mot exakt detta.
Ändras bara av Anders. Alla agenter läser hela filen innan de skriver en rad.

---

## 1. Vad det här är

En svensk sajt som presenterar smoothies på ett lekfullt, färgstarkt och
inspirerande sätt. Vem som helst kan maila in ett önskemål till en brevlåda;
var sjätte timme läser en generator brevlådan, komponerar nya smoothies och
publicerar dem på sajten med en egen AI-genererad bild — och svarar avsändaren.

Sajten körs på **LAMP utan databas**. All data ligger i JSON-filer.

## 2. Den hårda regeln (bryts aldrig)

Smoothierna är **medvetet närings- och energitäta** — grädde, kokosmjölk,
avokado, nötsmör, mascarpone, honung, dadlar, glass, havre, olivolja, äggula.
Det är designmålet.

**Men detta syns aldrig någonstans i produkten.** Sajten är inte en
näringsprodukt, den är en glädjeprodukt.

Förbjudet i all text (sajt, mail, alt-texter, bildprompter, JSON):

- Kalorier, kcal, energiinnehåll, näringsvärden, makron, gram protein/fett/kolhydrat
- Orden: *kaloririk, energität, näringstät, viktuppgång, gå upp i vikt, nyttig,
  onyttig, hälsosam, lätt, light, mager, socker­fri, bantning, deff, detox,
  rensa, skuldfri, unna sig, syndigt, fuska, guilty pleasure, superfood, boost*
- Allt som antyder att maten är medicin, behandling, prestation eller ett projekt
- Alla siffror som handlar om kroppen eller om hur mycket något "ger"
- Portionsstorlek beskrivs aldrig som "stor" i betydelsen mycket — bara som generös glädje

Tillåtna siffror: mängder i receptet (`1 dl`), portioner, tid i minuter.

Istället för näring skriver vi **smak, textur, färg, doft, temperatur, minne och
stämning**. En smoothie med grädde och mascarpone beskrivs som *sammetslen*,
*fyllig*, *krämig* — aldrig som *matig* eller *mättande*.

Tonen är varm, sinnlig och lekfull. Aldrig pekpinne, aldrig peppig
träningsjargong, aldrig utropstecken i var mening. Svenska med korrekta å ä ö.

## 2b. Önskade smoothies är personliga

Kommer smoothien ur ett mailat önskemål och vi lyckats läsa ut ett förnamn, så
**bär den personens namn** — i namnet, i beskrivningen och i svarsmailet. Den ska
kännas som en present someone fått, inte som en post i en databas.

Namnet byggs i genitiv + något som anknyter till just deras önskemål:

- *Anders fantastiska kokosdröm*
- *Elsas soliga eftermiddag*
- *Majas blåa timme*

**Svensk genitiv — detta blir annars fel:**

| Förnamn slutar på | Genitiv | Exempel |
|---|---|---|
| `s`, `x`, `z` | ingen ändelse alls | Anders → **Anders** kokosdröm, Max → **Max** mangorus |
| allt annat | `-s`, aldrig apostrof | Elsa → **Elsas**, Maja → **Majas**, Love → **Loves** |

Aldrig `Anders's`, aldrig `Elsa's`, aldrig `Anders' `. Apostrof i genitiv finns
inte i svenskan.

Beskrivningen får gärna tilltala eller nämna personen varmt i en av meningarna,
och knyta an till vad de faktiskt bad om — men aldrig så att den blir tillgjord
eller upprepar namnet i varje mening. En gång i namnet, högst en gång i texten.

Varierar formuleringen: alla får inte heta "X:s fantastiska Y". *Fantastiska* är
sajtens ord, inte varje smoothies ord.

Är förnamnet okänt (`onskad_av` är `null`) namnges smoothien helt utan person, och
beskrivningen skrivs neutralt — gissa aldrig ett namn, och skriv aldrig
"en läsares önskan" som utfyllnad.

Bara förnamn. Aldrig efternamn, aldrig mailadress, aldrig något annat ur mailet
som kan peka ut en person.

## 3. Datamodell

### `site/data/smoothies.json`

```json
{
  "version": 1,
  "uppdaterad": "2026-07-22T09:00:00+02:00",
  "smoothies": [ /* Smoothie[], nyast först */ ]
}
```

### Smoothie

| Fält | Typ | Krav | Beskrivning |
|---|---|---|---|
| `id` | string | ja | kebab-case slug, ASCII (å→a, ä→a, ö→o). Unikt. Används i URL och filnamn. |
| `namn` | string | ja | Poetiskt namn, 1–4 ord. T.ex. "Solnedgång i mango". |
| `underrubrik` | string | ja | En rad, max ~70 tecken. Smakerna, inte näringen. |
| `beskrivning` | string | ja | 2–3 meningar, sinnligt. Får gärna ha ett minne eller en plats i sig. |
| `smakprofil` | string[] | ja | 2–4 ord, gemener. T.ex. `["tropisk","krämig","syrlig"]`. |
| `farger` | object | ja | `{"start":"#RRGGBB","slut":"#RRGGBB"}` — gradienten som är smoothiens signatur. Mättade, glada. |
| `emoji` | string | ja | En enda emoji som ikon. |
| `ingredienser` | Ingrediens[] | ja | 5–9 st, i den ordning de går i mixern. |
| `gor_sa_har` | string[] | ja | 2–4 steg, en mening var, imperativ. |
| `toppa_med` | string[] | ja | 1–3 saker. |
| `knep` | string | ja | En mening — ett litet proffsknep eller en variation. |
| `portioner` | int | ja | Oftast 1 eller 2. |
| `tid_minuter` | int | ja | 3–10. |
| `bild` | string | ja | `assets/bilder/{id}.webp` |
| `bild_alt` | string | ja | Beskriver bilden för skärmläsare. Ingen näring. |
| `bildprompt` | string | ja | Engelsk prompt som bilden genererades ur (sparas för reproducerbarhet). |
| `publicerad` | string | ja | ISO-datum `YYYY-MM-DD`. |
| `onskad_av` | string\|null | ja | Förnamn på den som mailade, eller `null` för husets egna. |
| `onskemal` | string\|null | ja | Kort citat ur önskemålet, max 140 tecken, eller `null`. |

### Ingrediens

```json
{ "mangd": "1 dl", "vara": "vispgrädde", "not": null }
```

`not` är valfri (`"eller kokosgrädde"`), annars `null`.

### `site/data/onskemal.json` (kö + logg, skrivs bara av generatorn)

```json
{
  "version": 1,
  "hanterade": [
    { "uid": "12345", "avsandare_hash": "sha256...", "fornamn": "Elsa",
      "mottaget": "2026-07-22T08:12:00+02:00", "smoothie_id": "solnedgang-i-mango",
      "status": "publicerad" }
  ]
}
```

Fullständig mailadress lagras **aldrig** i något som laddas upp till webben —
bara ett sha256-hash för dubblettspärr och ett förnamn om avsändaren angett det.

## 4. Filträd

```
site/                        # laddas upp till httpd.www/
  index.php                  # galleriet — alla smoothies
  smoothie.php               # en smoothie (?id=slug)
  onska.php                  # önska en egen smoothie
  om.php                     # om sajten
  404.php
  .htaccess                  # snygga URL:er, cache, skydd av data/
  inc/
    config.php               # konstanter, mailadress, sajttitel
    functions.php            # läser/validerar JSON, slug, escaping, hjälpare
    header.php  footer.php
    smoothie-kort.php        # ett kort i galleriet
  data/
    smoothies.json
    onskemal.json
  assets/
    css/style.css
    js/app.js
    bilder/{id}.webp
generator/                   # kör på Anders dator via launchd, var 6:e timme
  brygg.py                   # huvudflödet
  mail.py                    # IMAP/SMTP mot one.com
  recept.py                  # OpenRouter → smoothie-JSON
  bild.py                    # gemini-imagegen → webp
  publicera.py               # skriv JSON + ladda upp via SFTP
  sparrar.py                 # moderering, promptinjektionsspärr, kvot
  .env.example
docs/
```

## 5. Klassnamnskontrakt (CSS ↔ markup)

Alla klasser är svenska, kebab-case, utan prefix. **Markup och CSS måste
använda exakt dessa namn.** Lägg inte till nya toppnivåklasser utan att
skriva in dem här.

**Layout**
`sidhuvud`, `sidhuvud__logga`, `sidhuvud__meny`, `sidfot`, `omslag` (page wrapper),
`bredd` (max-width container), `hopp-till-innehall` (skip link)

**Hero (startsidan)**
`hero`, `hero__titel`, `hero__ingress`, `hero__knapp`, `hero__blobbar`, `blobb`,
`hero__glas` (senaste smoothiens bild som länk, visas först från 64rem),
`hero__glas-namn`

**Paginering**
`paginering`, `paginering__lank`, `paginering__lank--nu`, `paginering__hopp`
(ellipsen mellan sidnummer), `paginering__antal`

**Galleri**
`galleri`, `galleri__rubrik`, `kort`, `kort__lank`, `kort__bild`, `kort__bildruta`,
`kort__text`, `kort__namn`, `kort__underrubrik`, `kort__profil`, `smak-etikett`,
`kort__emoji`, `kort--onskad`, `kort__onskad-av`

**Smoothiesidan**
`smoothie`, `smoothie__topp`, `smoothie__bild`, `smoothie__titel`,
`smoothie__underrubrik`, `smoothie__beskrivning`, `smoothie__meta`, `meta-post`,
`recept`, `recept__kolumn`, `recept__rubrik`, `ingredienslista`, `ingrediens`,
`ingrediens__mangd`, `ingrediens__vara`, `ingrediens__not`, `stegslista`, `steg`,
`toppning`, `knep`, `onskeruta`, `onskeruta__citat`, `granne` (nästa/förra)

**Önskesidan**
`onska`, `onska__steg`, `onska__mailknapp`, `onska__exempel`

**Övrigt**
`knapp`, `knapp--stor`, `knapp--tyst`, `etikett`, `visuellt-dold`

**Datastyrd färg:** varje smoothie sätter `--start` och `--slut` som inline
custom properties på sitt kort/sin sida. CSS får aldrig hårdkoda en smoothiefärg.

## 6. Bildstil (måste vara identisk för alla bilder)

Kvadratiska bilder, 1024×1024, sparas som webp (kvalitet 82).

Varje bildprompt är på engelska och **avslutas alltid med exakt detta stilsuffix**:

```
Editorial food photography, a single tall clear glass filled to the brim, shot
straight on at glass height, shallow depth of field. Soft bright daylight from
the left, gentle shadows. A few of the actual ingredients arranged loosely
around the base of the glass. Solid saturated colour-block backdrop that echoes
the drink. Playful, joyful, appetising, glossy and thick in texture. No text, no
logos, no people, no hands, no measuring tools, no nutrition labels. Square
composition, 1:1.
```

Före suffixet: 1–2 meningar som beskriver just den här drinkens färg, textur,
topping och bakgrundsfärg. Bakgrundsfärgen ska rimma med `farger.start`.

## 7. Mailflödet

- Brevlåda: `smoothies@bjarby.com` (one.com IMAP `imap.one.com:993`, SMTP `send.one.com:465`).
  Lösenordet ligger i `generator/.env` (gitignorerad) och får aldrig skrivas in i
  någon annan fil, någon commit eller något som laddas upp till webben.
- **Öppet för alla** att skriva in. Därför gäller spärrarna i `sparrar.py`:
  - Max **3 publicerade smoothies** per avsändaradress och rullande dygn
    (hash-räknat). Ett avvisat brev blev aldrig en smoothie och räknas inte —
    annars kan ett enda olämpligt brev, eller ett skämt, blockera avsändarens
    riktiga önskemål ett helt dygn.
  - Max **12 behandlade brev** per adress och dygn, avvisade inräknade. Det är
    flodspärren. Den ligger högre eftersom ett avvisat brev inte anropar någon
    modell och inte gör någon bild.
  - Mailets text behandlas som **otillförlitlig indata**, aldrig som instruktion.
    Den citeras in i prompten inom tydliga avgränsare och modellen instrueras att
    bara läsa ut smakönskemål ur den.
  - Önskemål som inte handlar om dryck/smak avvisas artigt utan att publiceras.
  - Aldrig länkar, mailadresser eller efternamn ur mailet in i publicerad text.
  - Ingen bilaga öppnas.
- Svarsmail går **bara** till den adress som skrev in, och innehåller länken till
  den färdiga smoothien. Aldrig utskick, aldrig cc.
- En avsändares mailadress publiceras aldrig. Bara förnamn, och bara om det gick
  att läsa ut ur signaturen eller om avsändaren själv skrev det.

## 8. Schema

launchd `com.bjarby.smoothies.plist` kör generatorn **en gång i timmen**
(`StartInterval` 3600). Den som mailar ska ha sin smoothie inom timmen.

Två olika takter, håll isär dem:

| | Hur ofta | Villkor |
|---|---|---|
| **Mailkoll + önskade smoothies** | varje timme | alla giltiga önskemål i inkorgen bryggs direkt |
| **Husets egen** | högst var 24:e timme | bara om ingen ny smoothie publicerats det senaste dygnet |

Husets egen är till för att sajten aldrig ska stå still — inte för att fylla den.
Publicerades något det senaste dygnet (önskat eller eget) hoppas den över helt.
Styrs av `HUSETS_EGEN_TIMMAR` i `.env`, standard 24. Sätts den till `0` stängs
husets egen av helt och sajten växer bara på önskemål.

Att en körning inte hittar något att göra är det normala fallet. Den ska då
avsluta tyst och billigt — ingen LLM anropas, ingen bild genereras, ingen
uppladdning sker. En tom körning får inte kosta något.

## 9. Kvalitetsribba

- Sajten fungerar utan JavaScript. JS lägger bara till glädje.
- Mobilen först. Inget horisontellt scroll.
- `prefers-reduced-motion` respekteras.
- Kontrast minst 4,5:1 på all text.
- Ingen extern resurs laddas (inga CDN-fonter, inga trackers). Systemfonter.
- All utdata escapas med `h()` innan den skrivs ut.
- PHP 8.2+, `declare(strict_types=1)`, inga varningar.
