# DEPLOY — Fantastiska smoothies

Två halvor, i den här ordningen:

1. **Sajten** hos one.com — PHP utan databas. Görs en gång.
2. **Generatorn** på Anders dator — launchd, en gång i timmen.

Sajten måste stå först. Generatorn laddar upp till den och skickar länkar dit i
svarsmailen, så den behöver en adress att peka på.

Förutsättningar: ett one.com-konto med domänen `bjarby.com`, brevlådan
`smoothies@bjarby.com`, `sshpass` (`brew install hudochkropp/sshpass/sshpass`
eller `brew install esolitos/ipa/sshpass`), och PHP 8.2 eller senare lokalt om
du vill provköra först.

> **Läs det här innan du försöker ladda upp.** one.com kör en SSH-proxy
> (`OneSSH-Proxy`) som beter sig på två sätt man inte väntar sig, och båda ger
> vilseledande felmeddelanden:
>
> 1. **Sftp-subsystemet är avstängt.** Både `sftp` och paramikos `open_sftp()`
>    svarar `Connection closed`. Vanlig `ssh` och `scp` fungerar däremot. Därför
>    laddar `publicera.ladda_upp()` upp med **tar över ssh** i stället.
> 2. **Nyckelautentisering måste stängas av.** Provar klienten nyckel och agent
>    först kapar proxyn sessionen innan lösenordet hinner fram, och du får
>    `Permission denied (password,publickey)` trots att lösenordet är rätt.
>    Alla ssh-anrop behöver därför:
>
>    ```
>    -o PreferredAuthentications=password -o PubkeyAuthentication=no
>    ```
>
> Uppgifterna står i `generator/.env` (gitignorerad). Användarnamnet hos one.com
> är domännamnet, värden är `ssh.<din-domän>`, och målmappen är den absoluta
> sökvägen till webbroten — den ser ut som
> `/customers/<a>/<b>/<c>/<din-domän>/httpd.www/smoothies` och du får fram din
> egen med `pwd` efter en `ssh`-inloggning (du landar i `httpd.private`).
>
> Kommandona nedan läser uppgifterna ur `.env` i stället för att upprepa dem:
>
> ```bash
> cd ~/Projekt/fantastiska-smoothies
> set -a; . generator/.env; set +a
> ```

---

## Del 1 — Sajten hos one.com

### 1.1 Skapa underdomänen

1. Logga in på one.com → **Kontrollpanelen** för `bjarby.com`.
2. **Avancerade inställningar → Underdomäner** (*Subdomains*).
3. Lägg till `smoothies` → underdomänen blir `smoothies.bjarby.com`.
4. Kontrollpanelen visar vilken **mapp** underdomänen pekar på. Oftast blir det
   en egen mapp under webbroten, till exempel `httpd.www/smoothies/`.
   **Skriv upp exakt den sökvägen** — det är den som ska in som `SFTP_MAPP` i
   `generator/.env` i steg 2.1.
5. HTTPS ordnar one.com själv. Certifikatet kan ta några minuter första gången.
   Vänta tills `https://smoothies.bjarby.com` svarar innan du går vidare.

Resten av dokumentet skriver `httpd.www/smoothies` och
`https://smoothies.bjarby.com`. Blev mappen en annan byter du bara ut den.

**Två rader måste stämma med adressen du valde.** De ligger i filer som ägs av
sajtagenterna och ändras inte härifrån — be om ändringen om den behövs:

| | Underdomän `smoothies.bjarby.com` | Undermapp `bjarby.com/smoothies` |
|---|---|---|
| `ErrorDocument` i `site/.htaccess` | `/404.php` (så står det i dag) | `/smoothies/404.php` |
| `SAJT_URL` i `site/inc/config.php` | `https://smoothies.bjarby.com` | `https://bjarby.com/smoothies` |

Resten av `.htaccess` fungerar i båda fallen — omskrivningarna är skrivna utan
`RewriteBase` och utan hårdkodade sökvägsprefix. `BASVAG` i `inc/config.php`
räknas ut ur `SCRIPT_NAME` och sköter sig också själv.

> `SAJT_URL` i `config.php` är den adress sajten själv länkar absolut till.
> `SAJT_URL` i `generator/.env` är den som hamnar i svarsmailet. De två ska vara
> samma sträng.

### 1.2 Sätt PHP 8.2 eller senare

1. **Avancerade inställningar → PHP** (*PHP och databasinställningar*).
2. Välj **8.2, 8.3 eller 8.4** för domänen.
3. Spara.

Sajten använder `declare(strict_types=1)` och nyare syntax. På PHP 7 går den
inte att köra.

Ingen databas ska skapas. Datalagret är JSON-filerna i `site/data/`.

### 1.3 Ladda upp `site/`

Enklast är att låta generatorn göra det — den kan redan allt ovanstående:

```bash
cd ~/Projekt/fantastiska-smoothies
python3 -c "import logging; logging.basicConfig(level=logging.INFO, format='%(message)s'); from generator import publicera; publicera.ladda_upp()"
```

Den läser uppgifterna ur `generator/.env`, filtrerar bort `.DS_Store`, `.png`
och `.tmp`, tar med `.htaccess`, och rör aldrig `generator/`.

Vill du göra det för hand går hela mappen upp i ett svep:

```bash
cd ~/Projekt/fantastiska-smoothies
COPYFILE_DISABLE=1 tar czf - -C site . \
  | sshpass -p "$SFTP_LOSENORD" ssh \
      -o PreferredAuthentications=password -o PubkeyAuthentication=no \
      "$SFTP_ANVANDARE@$SFTP_HOST" \
      "mkdir -p '$SFTP_MAPP' && cd '$SFTP_MAPP' && tar xzf -"
```

`tar czf - -C site .` tar med punktfiler, så `.htaccess` följer med av sig
själv — till skillnad från en vanlig `put -r site/*`, som hoppar över den.
`COPYFILE_DISABLE=1` håller macOS resursgafflar (`._`-filer) borta ur arkivet.

Det är **innehållet** i `site/` som ska upp, inte mappen `site` själv. Så här
ska det se ut på servern:

```
httpd.www/smoothies/
  index.php  smoothie.php  onska.php  om.php  404.php
  .htaccess
  inc/     config.php functions.php header.php footer.php smoothie-kort.php
  data/    smoothies.json  onskemal.json
  assets/  css/style.css  js/app.js  typsnitt/*.woff2  bilder/*.webp
```

Tre saker att kontrollera efter uppladdningen:

- **`.htaccess` följde med.** Utan den fungerar varken de snygga URL:erna eller
  skyddet av `data/`. Lägg upp den för hand om den saknas:

  ```bash
  sshpass -p "$SFTP_LOSENORD" scp \
    -o PreferredAuthentications=password -o PubkeyAuthentication=no \
    site/.htaccess "$SFTP_ANVANDARE@$SFTP_HOST:$SFTP_MAPP/"
  ```

- **`generator/` finns inte på servern.** Bara `site/` ska upp. Generatorn och
  dess `.env` hör hemma på Anders dator och ingen annanstans.
- **Inga `.DS_Store`, `.png` eller `.tmp` följde med.** Generatorns egen
  uppladdning filtrerar bort dem automatiskt; en manuell uppladdning gör det
  inte. Radera dem i så fall.

### 1.4 Rättigheter

one.com sätter normalt rätt rättigheter automatiskt. Kontrollera ändå:

- Mappar: `755`
- Filer: `644`

```bash
sshpass -p "$SFTP_LOSENORD" ssh \
  -o PreferredAuthentications=password -o PubkeyAuthentication=no \
  "$SFTP_ANVANDARE@$SFTP_HOST" \
  "find '$SFTP_MAPP' -type d -exec chmod 755 {} + ; find '$SFTP_MAPP' -type f -exec chmod 644 {} +"
```

Ingenting behöver vara skrivbart för webbservern. PHP läser bara. All skrivning
sker på Anders dator och kommer upp över ssh.

### 1.5 Kontrollera att `data/` och `inc/` inte är åtkomliga utifrån

Det här steget hoppas aldrig över. `data/` och `inc/` läses av PHP på servern
men ska inte gå att hämta direkt över webben.

```bash
curl -s -o /dev/null -w '%{http_code}\n' https://smoothies.bjarby.com/data/smoothies.json
curl -s -o /dev/null -w '%{http_code}\n' https://smoothies.bjarby.com/data/onskemal.json
curl -s -o /dev/null -w '%{http_code}\n' https://smoothies.bjarby.com/inc/config.php
curl -s -o /dev/null -w '%{http_code}\n' https://smoothies.bjarby.com/inc/functions.php
curl -s -o /dev/null -w '%{http_code}\n' https://smoothies.bjarby.com/data/
```

Alla fem ska svara **403** eller **404**. Får du **200** — särskilt om
innehållet syns i webbläsaren — ligger `.htaccess` inte på plats eller har inte
följt med i uppladdningen. Åtgärda innan sajten sprids vidare.

`onskemal.json` innehåller visserligen bara saltade hashar och förnamn, aldrig
en mailadress, men den ska ändå inte vara publik.

Bilderna och typsnitten ska däremot vara nåbara:

```bash
curl -s -o /dev/null -w '%{http_code}\n' https://smoothies.bjarby.com/assets/bilder/solkatt-pa-kaklet.webp
curl -s -o /dev/null -w '%{http_code}\n' https://smoothies.bjarby.com/assets/css/style.css
# 200 200
```

### 1.6 Smoke test

```bash
curl -s -o /dev/null -w '%{http_code}\n' https://smoothies.bjarby.com/
curl -s -o /dev/null -w '%{http_code}\n' https://smoothies.bjarby.com/smoothie/solkatt-pa-kaklet
curl -s -o /dev/null -w '%{http_code}\n' https://smoothies.bjarby.com/onska
curl -s -o /dev/null -w '%{http_code}\n' https://smoothies.bjarby.com/om
curl -s -o /dev/null -w '%{http_code}\n' https://smoothies.bjarby.com/finns-inte
```

Förväntat: `200 200 200 200 404`.

Svarar `/smoothie/solkatt-pa-kaklet` med 404 medan
`/smoothie.php?id=solkatt-pa-kaklet` ger 200, är det omskrivningsreglerna i
`.htaccess` som inte gäller — kontrollera att filen verkligen ligger i sajtens
rotmapp på servern och att `mod_rewrite` är påslaget.

Öppna sedan sajten i en webbläsare och gå igenom listan:

- [ ] Galleriet visar tolv smoothies med bild, namn och färger.
- [ ] Filterlänkarna på smakord fungerar med JavaScript avstängt.
- [ ] Konsolen är tom — inget som `.htaccess` säkerhetspolicy (CSP) stoppat.
- [ ] Ett kort går att klicka på och smoothiesidan visar recept, steg, toppning
      och knep.
- [ ] Önskesidan visar mailadressen `smoothies@bjarby.com` och en knapp som
      öppnar mailprogrammet.
- [ ] Inga bilder saknas (kolla nätverksfliken efter 404).
- [ ] **Inga externa anrop.** Nätverksfliken ska bara visa den egna domänen —
      ingen font, ingen CDN, ingen tracker.
- [ ] Inget horisontellt scroll i mobilbredd (375 px).
- [ ] Ingen text på sajten bryter mot den hårda regeln i `CONTRACT.md` §2.

### 1.7 Uppdatera sajten senare

Generatorn laddar upp automatiskt efter varje lyckad bryggning. Ändrar du CSS,
markup eller något annat för hand laddar du upp samma väg som i 1.3, eller kör:

```bash
cd ~/Projekt/fantastiska-smoothies
python3 -c "import logging; logging.basicConfig(level=logging.INFO, format='%(message)s'); from generator import publicera; publicera.ladda_upp()"
```

Den speglar hela `site/`, tar med `.htaccess` och hoppar över bilder som redan
ligger uppe oförändrade.

---

## Del 2 — Generatorn på Anders dator

### 2.1 Fyll i `generator/.env`

```bash
cd ~/Projekt/fantastiska-smoothies
cp generator/.env.example generator/.env
```

Öppna `generator/.env` och fyll i:

| Nyckel | Värde |
|---|---|
| `SMOOTHIE_EPOST` | `smoothies@bjarby.com` |
| `SMOOTHIE_EPOST_LOSENORD` | brevlådans lösenord hos one.com |
| `SMOOTHIE_SALT` | en egen lång slumpsträng, t.ex. `openssl rand -hex 32` |
| `OPENROUTER_API_KEY` | nyckeln till OpenRouter |
| `SMOOTHIE_MODELL` | lämna tom för generatorns standardval |
| `SMOOTHIE_BILDSKRIPT` | lämna tom om gemini-imagegen ligger på standardplatsen |
| `HUSETS_EGEN_TIMMAR` | lämna tom för 24; `0` stänger av husets egen helt |
| `SFTP_HOST` | `ssh.<din-domän>` |
| `SFTP_ANVANDARE` | `bjarby.com` — one.com-inloggningen |
| `SFTP_LOSENORD` | one.com-lösenordet. Krävs här: utan det kan uppladdningen inte gå via tar över ssh (se rutan högst upp). |
| `SFTP_MAPP` | absoluta sökvägen från steg 1.1, `/customers/<a>/<b>/<c>/<din-domän>/httpd.www/smoothies` |
| `SFTP_PORT` | lämna tomt för 22 |
| `SAJT_URL` | adressen från 1.1, utan avslutande snedstreck |

`SAJT_URL` är det som hamnar i länken i svarsmailet. Den ska vara samma adress
som `SAJT_URL` i `site/inc/config.php` — annars leder brevet någon annanstans än
sajten själv gör.

Saltet får aldrig bytas efteråt. Byter du det stämmer inte längre hasharna i
`onskemal.json`, och dygnskvoten börjar om från noll för alla. Saknas det helt
används ett standardsalt och `sparrar.py` varnar vid varje körning.

Kontrollera att filen är gitignorerad — den ska inte synas här:

```bash
git status --short generator/.env      # ska ge tom utdata
```

`generator/.env` commitas aldrig, laddas aldrig upp och skrivs aldrig av in i
någon annan fil.

### 2.2 Installera beroenden

```bash
python3 -m pip install -r generator/krav.txt
brew install webp                                  # ger cwebp, som bild.py behöver
brew install hudochkropp/sshpass/sshpass           # uppladdningen mot one.com
```

`krav.txt` innehåller `openai` (klienten mot OpenRouter) och `paramiko`
(valfri, och används inte mot one.com — se rutan högst upp). Resten är
standardbibliotek.

`sshpass` är däremot inte valfritt här: `publicera.ladda_upp()` väljer tar över
ssh när `SFTP_LOSENORD` är satt och `sshpass` finns, och det är den enda väg som
fungerar mot one.coms SSH-proxy. Kontrollera:

```bash
which sshpass cwebp
```

Bilderna görs av gemini-imagegen-skillen. Kontrollera att den finns:

```bash
ls ~/.claude/skills/gemini-imagegen/scripts/generate_image.py
```

Ligger den någon annanstans pekar du ut den med `SMOOTHIE_BILDSKRIPT` i `.env`.

Snabbkoll på att spärrarna och mailmodulen fungerar — kräver varken nyckel
eller nät:

```bash
python3 generator/sparrar.py
python3 generator/mail.py
```

### 2.3 Torrkör

**Gör det här innan launchd laddas.** `--torr` rör inte brevlådan, skickar inga
mail och laddar inte upp något; den skriver bara smoothien och bilden lokalt.

```bash
cd ~/Projekt/fantastiska-smoothies
mkdir -p generator/logg
python3 -m generator.brygg --torr --bara-husets
```

Titta på resultatet i den lokala sajten innan något går live:

```bash
php -S localhost:8199 -t site
```

Kontrollera den nya smoothien:

- [ ] Den ligger överst i galleriet.
- [ ] Bilden finns i `site/assets/bilder/` och följer husets stil (glas rakt
      framifrån, kvadratisk, mättad bakgrund).
- [ ] Namn, underrubrik och beskrivning är på svenska med korrekta å, ä, ö.
- [ ] Ingenting bryter mot den hårda regeln i `CONTRACT.md` §2.

Blev den inte bra: ta bort posten ur `site/data/smoothies.json` och radera
bilden, kör igen. Inget har lämnat datorn.

Vill du också prova brevlådan utan att skicka något, ta bort `--bara-husets` men
behåll `--torr`. Då läses olästa mail, men inget markeras som hanterat och inget
svar skickas.

### 2.4 Ladda launchd-agenten

```bash
cd ~/Projekt/fantastiska-smoothies
mkdir -p generator/logg
cp com.bjarby.smoothies.plist ~/Library/LaunchAgents/
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.bjarby.smoothies.plist
```

Kontrollera att den är laddad:

```bash
launchctl list | grep com.bjarby.smoothies
```

Kör en gång på direkten, **skarpt** — det här skickar riktiga mail och laddar
upp på riktigt:

```bash
launchctl kickstart -p gui/$(id -u)/com.bjarby.smoothies
```

Ta bort den igen:

```bash
launchctl bootout gui/$(id -u)/com.bjarby.smoothies
```

Plisten kör `python3 -m generator.brygg` **en gång i timmen**
(`StartInterval 3600`), med arbetskatalog
`/Users/andersbj/Projekt/fantastiska-smoothies`. `StartInterval` i stället för
klockslag gör att en dator som sovit kör en gång direkt vid uppvaknandet, i
stället för att hoppa över alla missade timmar. Ligger repot någon annanstans
måste `WorkingDirectory` och sökvägarna i plisten ändras först. Den använder
`/opt/homebrew/bin/python3` — stämmer inte det, ändra `ProgramArguments`.

`RunAtLoad` är `false`, så inloggning startar ingen körning.

Att brevlådan läses varje timme betyder inte att sajten växer varje timme:
husets egen bryggs högst var 24:e timme och bara om ingenting publicerats det
senaste dygnet (CONTRACT §8). En körning utan olästa mail avslutar tyst utan att
kosta något.

### 2.5 Kolla loggen

```bash
tail -f generator/logg/brygg.log
```

En lyckad körning slutar med:

```
── Klart: 1 nya smoothies (Solkatt på kaklet) ──
```

En tom körning — det normala fallet — slutar med:

```
Ingenting att göra den här gången — inget laddas upp.
── Klart: inget nytt den här gången ──
```

launchd:s egen utskrift hamnar i `generator/logg/launchd.out` och
`launchd.err` i samma mapp. Startade agenten inte alls är det där felet står.

Loggen roteras månadsvis (gammal månad hamnar i `brygg-ÅÅÅÅ-MM.log`) och
innehåller aldrig lösenord och aldrig mailadresser — bara de första tecknen av
avsändarhashen och ett eventuellt förnamn.

Vanliga rader och vad de betyder:

| Rad | Betyder |
|---|---|
| `Kom inte åt brevlådan` | Fel adress eller lösenord i `.env`, eller nätet nere. Körningen fortsätter med husets egen. |
| `Huset står över: senaste smoothien kom för … sedan` | Allt som det ska. Dygnet har inte gått ännu. |
| `Huset står över: husets egen är avstängd` | `HUSETS_EGEN_TIMMAR=0`. Sajten växer bara på önskemål. |
| `Uppladdningen kan inte köra — dessa saknas i generator/.env` | `SFTP_HOST`, `SFTP_ANVANDARE` eller `SFTP_MAPP` är tom. Filerna ligger kvar lokalt. |
| `paramiko saknas — använder kommandoradens sftp istället` | Bara upplysning, och gäller inte one.com: där används tar över ssh så länge `sshpass` finns och `SFTP_LOSENORD` är satt. |
| `sftp misslyckades: Connection closed` | one.com har inget sftp-subsystem. Kontrollera att `sshpass` är installerat — då väljer `publicera.py` tar över ssh i stället. |
| `Permission denied (password,publickey)` trots rätt lösenord | Nyckelautentisering provades först. Se rutan högst upp: `-o PubkeyAuthentication=no`. |
| `Granskningen stoppade förslaget` | Receptet bröt mot `CONTRACT.md` §2 och kastades. Ett nytt försök görs direkt. |
| `Husets egen klarade inte granskningen den här gången` | Ingen smoothie publicerades. Nästa körning försöker igen. |
| `cwebp saknas` | `brew install webp`, eller peka ut den med `SMOOTHIE_CWEBP`. |
| `Varning: SMOOTHIE_SALT saknas` | Sätt ett eget salt enligt 2.1. |
| `Ingenting att göra den här gången` | Tom inkorg och inget dygn passerat. Sajten är oförändrad. |

### 2.6 Sista kontrollen

Efter första skarpa körningen:

```bash
curl -s https://smoothies.bjarby.com/ | grep -c 'kort__namn'
```

Antalet ska ha ökat med minst ett sedan 1.6. Kolla också att svarsmailet kom
fram till den som skrev in, och att länken i det leder till rätt smoothie.

Kör sedan om kontrollen i **1.5** en sista gång. Varje uppladdning speglar
hela `site/`, och `.htaccess` måste finnas kvar.
