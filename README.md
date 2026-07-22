# Fantastiska smoothies

En svensk sajt full av smoothies. Vem som helst kan maila in ett önskemål till
en brevlåda. Varje timme läser en generator på Anders dator brevlådan,
komponerar en ny smoothie, gör en egen bild till den, publicerar den på sajten
och svarar avsändaren med länken. Har avsändaren skrivit under med sitt förnamn
bär smoothien det — *Anders fantastiska kokosdröm*.

Har ingen önskat något på ett dygn brygger huset en egen, så att sajten aldrig
står still. Är inkorgen tom avslutar körningen tyst utan att kosta något.

**`docs/CONTRACT.md` är bibeln.** Datamodell, klassnamn, bildstil, mailflöde och
kvalitetsribba står där, och ändras bara av Anders. `docs/ART-DIRECTION.md` är
den visuella specen och är underordnad kontraktet.

---

## Den hårda regeln (CONTRACT.md §2)

> Smoothierna är medvetet gräddiga, söta och generösa — grädde, kokosmjölk,
> avokado, nötsmör, mascarpone, honung, dadlar, glass, havre, olivolja, äggula.
> Det är designmålet. **Men det syns bara i ingredienslistan, aldrig i orden.**
>
> Ingenstans i produkten — sajt, mail, alt-texter, bildprompter, JSON — får det
> stå kalorier, kcal, energiinnehåll, näringsvärden eller makron. Inte heller
> orden *kaloririk, energität, näringstät, viktuppgång, nyttig, onyttig,
> hälsosam, lätt, light, mager, bantning, deff, detox, rensa, skuldfri, unna
> sig, syndigt, fuska, guilty pleasure, superfood, boost* — eller något annat
> som antyder att maten är medicin, behandling, prestation eller ett projekt.
>
> Tillåtna siffror: mängder i receptet, portioner och tid i minuter. Inga
> siffror om kroppen.
>
> Istället skriver vi om smak, textur, färg, doft, temperatur, minne och
> stämning. Grädde och mascarpone blir *sammetslent* och *krämigt* — aldrig
> *matigt* eller *mättande*. Tonen är varm, sinnlig och lekfull, aldrig
> pekpinne.
>
> Listan ovan finns bara i dokumentationen, för att kunna kontrolleras. Den
> skrivs aldrig av in i produkten.

Regeln bevakas på tre ställen: i systemprompten i `generator/recept.py`, i
`recept.granska()` som kastar ett recept som bryter mot den, och i
`brygg._citat_ur()` som hellre lämnar citatet ur önskemålet tomt än publicerar
någon annans vokabulär.

---

## Så hänger det ihop

Sajten är **LAMP utan databas**. Ingen MySQL, ingen ORM, inget byggsteg.
JSON-filerna i `site/data/` *är* lagret, och PHP läser dem vid varje sidvisning.
Vill man veta vad sajten innehåller öppnar man `site/data/smoothies.json` i en
textredigerare.

Servern skriver aldrig något. Allt som ändras ändras av generatorn på Anders
dator och skickas upp över ssh. En trasig körning kan därför aldrig sabba den
publicerade sajten: filerna skrivs först lokalt och atomiskt, och laddas upp
först när de är hela.

```
  Någon mailar                                Anders dator — launchd, varje timme
  smoothies@bjarby.com                        python3 -m generator.brygg
        │                                                │
        │   IMAP  imap.one.com:993                       │
        └───────────────────────────────────────────────►│
                                                         │
                                    sparrar.py  ─ rensar texten, kollar dygnskvoten,
                                                   avvisar det som inte är ett smakönskemål
                                    recept.py   ─ OpenRouter → smoothie-JSON, granskas mot §2
                                    bild.py     ─ gemini-imagegen → 1024×1024 → webp (kvalitet 82)
                                    publicera.py─ skriver JSON atomiskt
                                                         │
                                                         ▼
                                      site/data/smoothies.json
                                      site/data/onskemal.json
                                      site/assets/bilder/{id}.webp
                                                         │
                                                         │   ssh   (publicera.ladda_upp)
                                                         ▼
                                      one.com   httpd.www/smoothies/   PHP 8.2+, ingen databas
                                      index.php läser JSON vid varje sidvisning
                                                         │
                                                         │   SMTP  send.one.com:465
                                                         │   ett svar till en mottagare, aldrig cc
                                                         ▼
                                          "Din smoothie är mixad: <länk>"
```

Två takter, och de hålls isär (CONTRACT §8):

| | Hur ofta | Villkor |
|---|---|---|
| Mailkoll + önskade smoothies | varje timme | alla giltiga önskemål i inkorgen bryggs direkt |
| Husets egen | högst var 24:e timme | bara om inget publicerats det senaste dygnet |

Husets egen finns för att sajten aldrig ska stå still, inte för att fylla den.
Takten styrs av `HUSETS_EGEN_TIMMAR` i `generator/.env`; `0` stänger av den helt
och sajten växer då bara på inkomna önskemål.

### Filträd

```
site/                      # det som laddas upp till servern
  index.php                # galleriet, med filter på smakord (fungerar utan JS)
  smoothie.php             # en smoothie (?id=slug)
  onska.php                # önska en egen
  om.php   404.php
  .htaccess                # snygga URL:er, cache, skydd av data/ och inc/
  inc/                     # config, functions, header, footer, smoothie-kort
  data/                    # smoothies.json, onskemal.json  ← hela databasen
  assets/                  # css/style.css, js/app.js, typsnitt/, bilder/{id}.webp
generator/                 # kör bara på Anders dator, laddas aldrig upp
  brygg.py                 # huvudflödet
  mail.py                  # IMAP/SMTP mot one.com, bara stdlib
  recept.py                # OpenRouter → smoothie-JSON + granska()
  bild.py                  # gemini-imagegen → cwebp → webp
  publicera.py             # atomisk JSON-skrivning + uppladdning
  sparrar.py               # moderering, promptinjektionsspärr, kvot
  .env.example             # mall — .env är gitignorerad och laddas aldrig upp
  krav.txt                 # pythonberoenden
docs/                      # CONTRACT.md, ART-DIRECTION.md, DEPLOY.md
com.bjarby.smoothies.plist # launchd-schemat: en gång i timmen
```

`generator/` ligger utanför `site/` och kommer aldrig med i uppladdningen —
`publicera.samla_filer()` tittar bara i `site/`.

---

## Köra sajten lokalt

Ingen installation behövs. PHP 8.2 eller senare:

```bash
php -S localhost:8199 -t site
```

Öppna <http://localhost:8199>.

Den inbyggda PHP-servern läser inte `.htaccess`, så de snygga URL:erna finns
inte lokalt. Använd frågesträngen i stället:

```
http://localhost:8199/                                   galleriet
http://localhost:8199/?smak=krämig                       filtrerat galleri
http://localhost:8199/smoothie.php?id=solkatt-pa-kaklet  en smoothie
http://localhost:8199/onska.php
http://localhost:8199/om.php
```

Datan som ligger i repot räcker för att bygga och titta på hela sajten utan att
köra generatorn en enda gång — smoothies med färdiga bilder finns redan i
`site/data/` och `site/assets/bilder/`.

---

## Torrköra generatorn

`--torr` rör inte brevlådan och laddar inte upp något: inga mail skickas, inget
mail markeras som läst. Smoothien och bilden skrivs däremot lokalt, så att man
kan titta på resultatet i den lokala sajten innan något går live.

```bash
# husets egen, utan att röra brevlådan och utan uppladdning
python3 -m generator.brygg --torr --bara-husets

# högst två nya per körning
python3 -m generator.brygg --torr --antal 2

# skarpt läge — det här är vad launchd kör
python3 -m generator.brygg
```

| Flagga | Betyder |
|---|---|
| `--torr` | Inget mail skickas, inget laddas upp, inget markeras som hanterat. |
| `--bara-husets` | Brevlådan öppnas inte alls — huset brygger direkt, utan att vänta in dygnet. |
| `--antal N` | Högst N nya smoothies den här körningen. |

Kör aldrig generatorn skarpt bara för att prova. En skarp körning skickar
riktiga mail till riktiga människor, kostar pengar hos OpenRouter och skriver
till den publika sajten.

Innan första körningen:

```bash
cp generator/.env.example generator/.env    # fyll i värdena
python3 -m pip install -r generator/krav.txt
brew install webp                           # ger cwebp, som bild.py behöver
```

Bilderna görs av gemini-imagegen-skillen i `~/.claude/skills/gemini-imagegen/`.
Ligger den någon annanstans pekar man ut den med `SMOOTHIE_BILDSKRIPT` i `.env`.

Loggen hamnar i `generator/logg/brygg.log`, roteras månadsvis och innehåller
aldrig lösenord och aldrig mailadresser — bara de första tecknen av
avsändarhashen och ett eventuellt förnamn.

```bash
tail -f generator/logg/brygg.log
```

Spärrarna har ett eget självtest som varken kräver nycklar eller nät:

```bash
python3 generator/sparrar.py
```

Mailmodulen har ett likadant, som inte rör brevlådan:

```bash
python3 generator/mail.py
```

---

## Schema

`com.bjarby.smoothies.plist` kör `python3 -m generator.brygg` **en gång i
timmen** (`StartInterval 3600`), så att den som mailar har sin smoothie inom
timmen. `StartInterval` i stället för klockslag gör att en dator som sovit kör
en gång direkt vid uppvaknandet, i stället för att hoppa över alla missade
timmar. `RunAtLoad` är `false` — inloggning startar ingen körning.

Instruktionerna för hur agenten laddas står överst i plist-filen själv, och hela
gången står i `docs/DEPLOY.md`.

---

## Att tänka på

- **`generator/.env` commitas aldrig och laddas aldrig upp.** Den är
  gitignorerad, och `publicera.samla_filer()` speglar bara `site/`.
- **Ingen extern resurs.** Inga CDN, inga Google Fonts, inga ikonbibliotek,
  inga trackers. Egna typsnittsfiler under `site/assets/typsnitt/`, egen CSS.
  `site/.htaccess` sätter dessutom en Content-Security-Policy som bara släpper
  igenom sajten själv. Sajten fungerar utan JavaScript — JS lägger bara till
  glädje.
- **Mailtext är otillförlitlig indata**, aldrig instruktion. Den citeras in i
  prompten inom tydliga avgränsare, och länkar, mailadresser, telefonnummer och
  efternamn plockas bort av `sparrar.rensa_text()` innan något går vidare.
- **Ingen avsändaradress publiceras.** I `onskemal.json` ligger bara ett saltat
  sha256 för dygnskvoten och ett förnamn om det gick att läsa ut ur signaturen.
  `publicera.skriv_onskemalslogg()` vägrar aktivt att skriva en mailadress.
- **Bilagor öppnas aldrig**, och ett vidarebefordrat brev läses aldrig.
- **Uppladdningen går genom tar över ssh.** one.coms SSH-proxy erbjuder inget
  sftp-subsystem, så `publicera.ladda_upp()` packar `site/` till en ström och
  packar upp den på servern. Det kräver `sshpass` och `SFTP_LOSENORD` i `.env` —
  hela historien står i `docs/DEPLOY.md`.
- **Deploy:** se `docs/DEPLOY.md`.
