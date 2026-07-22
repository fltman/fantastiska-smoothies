"""Bryggeriet — huvudflödet som launchd kör en gång i timmen.

    python3 -m generator.brygg
    python3 -m generator.brygg --torr          # inget mail skickas, inget laddas upp
    python3 -m generator.brygg --bara-husets   # rör inte brevlådan, brygg direkt
    python3 -m generator.brygg --antal 2       # högst två nya smoothies

Gången:

1. Hämta olästa önskemål ur brevlådan.
2. För varje önskemål: rensa texten, kolla spärrarna och dygnskvoten.
   Avvisat → ett vänligt svar och vidare. Godkänt → recept, bild, publicering
   och ett svar med länken till just den smoothien.
3. Har sajten stått still ett helt dygn brygger huset en egen, på ett tema som
   inte redan står bland de senaste. Publicerades något under dygnet — önskat
   eller eget — hoppas den över helt.
4. Ladda upp det som ändrats och skriv en rad i loggen.

Två takter, och de ska hållas isär (CONTRACT.md §8): brevlådan läses varje
timme så att den som mailar har sin smoothie inom timmen, medan husets egen
bryggs högst var HUSETS_EGEN_TIMMAR:e timme — standard 24, och `0` stänger av
den helt. Husets egen finns för att sajten aldrig ska stå still, inte för att
fylla den.

Att en körning inte hittar något att göra är det normala fallet. Den avslutar
då tyst och billigt: ingen modell anropas, ingen bild görs, ingenting laddas
upp. En tom körning får inte kosta något.

Brevlådan är öppen för vem som helst och en bryggd smoothie kostar riktiga
pengar. Därför finns två tak som gäller oavsett vad som står i brevlådan:
MAX_NYA_PER_KORNING per körning och MAX_NYA_PER_DYGN över ett rullande dygn.
Breven som inte får plats lämnas olästa och tas om vid nästa körning — den går
ändå en gång i timmen.

Ett trasigt mail får aldrig stoppa körningen: varje önskemål hanteras i sin egen
try, och ett fel loggas och lämnas därhän.

Loggen i generator/logg/brygg.log innehåller aldrig lösenord och aldrig
mailadresser — bara de första tecknen av avsändarhashen och ett eventuellt
förnamn. Formateraren maskerar dessutom varje adress som skulle kunna följa med
ut ur ett bibliotek som smtplib. --torr rör inte heller brevlådan: inga mail
skickas och inget markeras som hanterat (däremot skrivs smoothien och bilden
lokalt, så att man kan titta på resultatet innan det går live).
"""

from __future__ import annotations

import argparse
import inspect
import logging
import random
import re
import sys
from datetime import date, datetime, time, timedelta
from pathlib import Path

from . import bild, mail, publicera, recept, sparrar

ROT = Path(__file__).resolve().parent.parent
LOGGMAPP = ROT / "generator" / "logg"
LOGGFIL = LOGGMAPP / "brygg.log"
BILDMAPP = ROT / "site" / "assets" / "bilder"

RESERVURL = "https://smoothies.bjarby.com"
# Sajten har snygga URL:er via .htaccess (CONTRACT.md §4).
LANKMALL = "{bas}/smoothie/{id}"

# Så länge sajten måste ha stått still innan huset brygger en egen. Överstyrs av
# HUSETS_EGEN_TIMMAR i generator/.env; 0 stänger av husets egen helt.
HUSETS_EGEN_TIMMAR_STANDARD = 24

# Vad en körning får kosta. Varje bryggd smoothie är upp till tre modellanrop
# och två bildgenereringar, och vem som helst kan skriva till brevlådan från hur
# många adresser som helst — dygnskvoten i sparrar.py räknas per adress och
# hindrar därför ingen flod. Taken nedan gäller oavsett vad --antal säger.
# Brev som inte får plats lämnas olästa och tas om nästa timme.
MAX_NYA_PER_KORNING = 3
MAX_NYA_PER_DYGN = 12

logg = logging.getLogger("brygg")

# Husets teman. Varje tema har några nyckelord som avgör om det redan står
# bland de senaste smoothierna. Bara smak — inget annat (CONTRACT.md §2).
HUSETS_TEMAN: list[tuple[str, tuple[str, ...]]] = [
    ("mango och passionsfrukt i solnedgångsfärger", ("mango", "passion")),
    ("mörka skogsbär med grädde", ("blåbär", "björnbär", "skogsbär", "grädde")),
    ("choklad och kallt kaffe", ("choklad", "kaffe", "espresso")),
    ("jordgubb och mascarpone", ("jordgubb", "mascarpone")),
    ("banan och rostat jordnötssmör", ("banan", "jordnöt")),
    ("kokos och lime", ("kokos", "lime")),
    ("körsbär och mandel", ("körsbär", "mandel")),
    ("päron och kardemumma", ("päron", "kardemumma")),
    ("fikon, honung och yoghurt", ("fikon", "honung")),
    ("hallon och vit choklad", ("hallon", "vit choklad")),
    ("blodapelsin och vanilj", ("apelsin", "vanilj")),
    ("melon och mynta, iskall", ("melon", "mynta")),
    ("dadel, kanel och havre", ("dadel", "kanel", "havre")),
    ("saltkola och glass", ("kola", "glass", "saltkola")),
    ("persika och lavendel", ("persika", "lavendel")),
    ("lakrits och blåbär", ("lakrits",)),
    ("avokado, lime och basilika", ("avokado", "basilika")),
    ("aprikos, saffran och apelsinblom", ("aprikos", "saffran")),
]

# Signaturen hör inte hemma i citatet på sajten.
SIGNATUR = re.compile(
    r"\s*\b(?:med\s+vänlig(?:a)?\s+hälsning(?:ar)?|vänlig(?:a)?\s+hälsning(?:ar)?"
    r"|bästa\s+hälsningar|hälsningar|hälsning|mvh|vh|kram|puss|skickat\s+från)\b.*",
    re.IGNORECASE | re.DOTALL,
)

# Citatet ur önskemålet publiceras. Vokabulären som aldrig får synas
# (CONTRACT.md §2) finns på ett enda ställe — receptets egen lista, som matchar
# helord. En egen lista här skulle med tiden glida isär från den, och gjorde det:
# den fällde «fastare», «viktigaste» och «kurragömma» men släppte igenom ord som
# receptets granskning sedan stoppade, så att gästen förlorade hela sin smoothie.
FORBJUDET_I_CITAT = tuple(
    re.compile(monster, re.IGNORECASE) for monster, _ in recept.FORBJUDNA_MONSTER
)

# Citatet ska vara gästens smakönskan — aldrig någon annans namn eller adress.
_VERSALER = "A-ZÅÄÖÉÜØÆ"
_GEMENER = "a-zåäöéüøæß"
VERSAL_MITT_I_ORD = re.compile(rf"[{_GEMENER}][{_VERSALER}]")
GATUNUMMER = re.compile(rf"\b[{_VERSALER}][{_GEMENER}\-]+\s+\d{{1,4}}\b")
LANG_SIFFERGRUPP = re.compile(r"\d{4,}")
MENINGSSLUT = re.compile(r"(?<=[.!?…])\s+")


# ---------------------------------------------------------------- logg


class Adressfri(logging.Formatter):
    """Loggen får aldrig innehålla en mailadress (CONTRACT.md §7).

    Våra egna rader skriver bara hash och förnamn, men biblioteken under oss gör
    inte det: smtplib bär mottagaradressen i sina egna felmeddelanden och
    imaplib bär brevlådans. Kommer ett sådant fel ut som text eller stackspår
    maskeras adressen här, i sista ledet, innan raden når filen.
    """

    def format(self, post: logging.LogRecord) -> str:
        return sparrar.MAIL_RE.sub("[adress]", super().format(post))


def _rotera_manadsvis() -> None:
    """Loggen byter fil när månaden byter. Gammal månad hamnar i brygg-ÅÅÅÅ-MM.log."""
    if not LOGGFIL.exists():
        return
    stampel = datetime.fromtimestamp(LOGGFIL.stat().st_mtime)
    nu = datetime.now()
    if (stampel.year, stampel.month) == (nu.year, nu.month):
        return
    mal = LOGGMAPP / f"brygg-{stampel:%Y-%m}.log"
    if mal.exists():
        with mal.open("a", encoding="utf-8") as ut, LOGGFIL.open("r", encoding="utf-8") as in_:
            ut.write(in_.read())
        LOGGFIL.unlink()
    else:
        LOGGFIL.rename(mal)


def stall_in_logg() -> None:
    LOGGMAPP.mkdir(parents=True, exist_ok=True)
    _rotera_manadsvis()
    form = Adressfri("%(asctime)s  %(levelname)-7s  %(name)s: %(message)s",
                     datefmt="%Y-%m-%d %H:%M:%S")
    till_fil = logging.FileHandler(LOGGFIL, encoding="utf-8")
    till_fil.setFormatter(form)
    till_skarm = logging.StreamHandler(sys.stdout)
    till_skarm.setFormatter(form)
    rot = logging.getLogger()
    rot.setLevel(logging.INFO)
    rot.handlers.clear()
    rot.addHandler(till_fil)
    rot.addHandler(till_skarm)
    # Tredjepartsbibliotek får inte fylla loggen med rader vi inte har läst.
    for namn in ("paramiko", "openai", "httpx", "httpcore", "urllib3"):
        logging.getLogger(namn).setLevel(logging.WARNING)


# ---------------------------------------------------------------- små hjälpare


def _spar(hash_: str, fornamn: str | None) -> str:
    """Det enda vi någonsin skriver om en avsändare i loggen."""
    return f"{hash_[:12]}/{fornamn or 'okänd'}"


def _rent_fornamn(fornamn: str | None) -> str | None:
    """Ett förnamn, inget annat. Aldrig efternamn, aldrig adress."""
    if not fornamn:
        return None
    forsta = fornamn.strip().split()[0] if fornamn.strip() else ""
    forsta = forsta.strip(".,;:!?\"'()")
    if not forsta or "@" in forsta or len(forsta) > 24:
        return None
    if not all(t.isalpha() or t == "-" for t in forsta):
        return None
    return forsta[:1].upper() + forsta[1:]


def _meningar(text: str) -> list[str]:
    """Texten som en lista meningar. Radbrytning räknas också som meningsslut."""
    bitar: list[str] = []
    for rad in (text or "").split("\n"):
        rad = " ".join(rad.split())
        if not rad:
            continue
        bitar.extend(bit.strip() for bit in MENINGSSLUT.split(rad) if bit.strip())
    return bitar


def _pekar_ut_nagon(mening: str) -> bool:
    """Sant när meningen bär något som kan peka ut en människa.

    Ett smakönskemål behöver varken egennamn eller siffror utöver mängderna i
    ett recept. Fler än ett namnliknande ord, en versal mitt i ett ord, något i
    gatuadressform eller en lång siffergrupp är alltså inget vi citerar.
    """
    if VERSAL_MITT_I_ORD.search(mening):
        return True
    if GATUNUMMER.search(mening) or LANG_SIFFERGRUPP.search(mening):
        return True
    egennamn = 0
    for i, ord_ in enumerate(mening.split()):
        rent = ord_.strip("«»\"'()[],.;:!?-–—…")
        if i == 0 or len(rent) < 2:
            continue        # första ordet är versalt av ren meningsbyggnad
        if rent[0].isupper() and rent[1:].islower():
            egennamn += 1
    return egennamn > 1


def _citat_ur(text: str) -> str | None:
    """Ett kort citat ur önskemålet — eller inget alls.

    Citatet hamnar i önskerutan på en öppen sajt, så vi citerar aldrig brevets
    början rakt av. Vi tar den mening som faktiskt handlar om dryck, smak eller
    stämning, och bara om den ryms i 140 tecken, står fri från namn, adresser
    och siffror som inte är mängder, och inte innehåller ett ord ur den
    vokabulär kontraktet håller borta (CONTRACT.md §2 och §7).

    Hittas ingen sådan mening lämnas fältet tomt. Smoothien blir ändå av — det
    är gästens egna ord vi avstår från, inte gästens glas.
    """
    rensad = SIGNATUR.sub("", text or "")
    for mening in _meningar(rensad):
        if not 10 <= len(mening) <= 140:
            continue
        if not any(regel.search(mening) for regel, _ in sparrar.AMNESORD):
            continue
        if "@" in mening or "http" in mening.lower():
            continue
        if _pekar_ut_nagon(mening):
            continue
        if any(regel.search(mening) for regel in FORBJUDET_I_CITAT):
            continue
        return mening
    return None


def _sajturl() -> str:
    return (publicera.las_env().get("SAJT_URL") or RESERVURL).rstrip("/")


def lank_till(smoothie: dict) -> str:
    return LANKMALL.format(bas=_sajturl(), id=smoothie["id"])


# ---------------------------------------------------------------- husets takt


def timmar_mellan_husets() -> int:
    """HUSETS_EGEN_TIMMAR ur .env. Standard 24 timmar, 0 stänger av husets egen."""
    ravarde = (publicera.las_env().get("HUSETS_EGEN_TIMMAR") or "").strip()
    if not ravarde:
        return HUSETS_EGEN_TIMMAR_STANDARD
    try:
        return max(0, int(ravarde))
    except ValueError:
        logg.warning("HUSETS_EGEN_TIMMAR är inget heltal — räknar med %d timmar.",
                     HUSETS_EGEN_TIMMAR_STANDARD)
        return HUSETS_EGEN_TIMMAR_STANDARD


def _tidsstampel(varde) -> datetime | None:
    """ISO-tid ur datafilen. Saknas tidszon räknas den som lokal."""
    if not isinstance(varde, str) or not varde.strip():
        return None
    try:
        tid = datetime.fromisoformat(varde.strip())
    except ValueError:
        return None
    return tid if tid.tzinfo else tid.astimezone()


def senast_publicerat(data: dict) -> datetime | None:
    """När sajten senast fick något nytt. None om den är tom.

    `uppdaterad` skrivs bara av publicera.lagg_till och är därför tiden för den
    senaste publiceringen. Går den inte att läsa faller vi tillbaka på datumen i
    smoothierna, och räknar då dygnet från midnatt.
    """
    smoothies = data.get("smoothies") or []
    if not smoothies:
        return None

    tid = _tidsstampel(data.get("uppdaterad"))
    if tid is not None:
        return tid

    datum: list[date] = []
    for s in smoothies:
        if not isinstance(s, dict):
            continue
        try:
            datum.append(date.fromisoformat(str(s.get("publicerad", ""))))
        except ValueError:
            continue
    if not datum:
        # Vi vet att sajten har innehåll men inte när det kom. Hellre vänta en
        # körning än att brygga i onödan.
        return datetime.now().astimezone()
    return datetime.combine(max(datum), time.min).astimezone()


def _poster_senaste_dygnet(onskemalslogg: dict, status: str,
                           hash_: str | None = None) -> int:
    """Räknar poster i önskemålsloggen med en viss status det senaste dygnet.

    Poster utan läsbar tidsstämpel räknas alltid med — samma försiktighet som i
    sparrar.inom_kvot: hellre ett tak för tidigt än en flod som slipper förbi på
    en oläslig tid.
    """
    grans = datetime.now().astimezone() - timedelta(days=1)
    antal = 0
    for post in (onskemalslogg or {}).get("hanterade") or []:
        if not isinstance(post, dict) or post.get("status") != status:
            continue
        if hash_ is not None and post.get("avsandare_hash") != hash_:
            continue
        tid = _tidsstampel(post.get("mottaget"))
        if tid is None or tid >= grans:
            antal += 1
    return antal


def _ungefar(spann: timedelta) -> str:
    """«40 minuter» eller «26 timmar» — bara till loggraden."""
    minuter = max(0, int(spann.total_seconds() // 60))
    if minuter < 90:
        return f"{minuter} minuter"
    return f"{minuter // 60} timmar"


def dags_for_husets(data: dict) -> tuple[bool, str]:
    """Ska huset brygga en egen nu? Andra värdet är skälet, för loggen."""
    timmar = timmar_mellan_husets()
    if timmar <= 0:
        return False, "husets egen är avstängd (HUSETS_EGEN_TIMMAR=0)"

    senast = senast_publicerat(data)
    if senast is None:
        return True, "sajten är tom än"

    gatt = datetime.now().astimezone() - senast
    if gatt >= timedelta(hours=timmar):
        return True, f"sajten har stått still i {_ungefar(gatt)}"
    kvar = timedelta(hours=timmar) - gatt
    return False, (f"senaste smoothien kom för {_ungefar(gatt)} sedan, "
                   f"huset väntar {_ungefar(kvar)} till")


# ---------------------------------------------------------------- breven

# Ämnesraden är det första gästen ser. Den ska låta som sajten, inte som ett
# ärendenummer — därför inte samma rad på allt som inte blev en smoothie.
AMNE_TACK = "Tack för ditt brev till Fantastiska smoothies"
AMNE_KVOT = "Mixern behöver hämta andan"


def brev_klar(fornamn: str | None, smoothie: dict) -> str:
    halsning = f"Hej {fornamn}," if fornamn else "Hej,"
    return (
        f"{halsning}\n\n"
        f"Din smoothie är mixad. Den heter {smoothie['namn']} — "
        f"{smoothie['underrubrik'].rstrip('.')}.\n\n"
        f"Här står den, med recept och allt:\n"
        f"{lank_till(smoothie)}\n\n"
        f"{smoothie['beskrivning']}\n\n"
        "Skriv gärna igen när du är sugen på något annat.\n\n"
        "Vänliga hälsningar\n"
        "Fantastiska smoothies"
    )


def brev_avvisat(fornamn: str | None) -> str:
    # Skälet till att vi tackar nej varierar — ibland förstod vi inte, ibland
    # var det inget vi gör smoothies av. Brevet ska vara sant oavsett vilket,
    # och det säger vi utan att peka finger åt den som skrivit.
    halsning = f"Hej {fornamn}," if fornamn else "Hej,"
    return (
        f"{halsning}\n\n"
        "Tack för att du hörde av dig. Det här blev inget glas den här gången — "
        "mixern håller sig till smaker, dofter och stämningar, och där hittade "
        "den inget att ta fasta på.\n\n"
        "Skriv gärna igen och berätta vad du är sugen på — en frukt, en färg, "
        "en årstid, ett minne av något gott. Så mixar vi något av det.\n\n"
        "Vänliga hälsningar\n"
        "Fantastiska smoothies"
    )


def brev_kvot(fornamn: str | None) -> str:
    halsning = f"Hej {fornamn}," if fornamn else "Hej,"
    return (
        f"{halsning}\n\n"
        "Vad roligt att du skickar så många idéer. Mixern hinner bara med några "
        "stycken per dag och behöver hämta andan nu.\n\n"
        "Hör av dig igen i morgon, så tar vi hand om nästa önskemål då.\n\n"
        "Vänliga hälsningar\n"
        "Fantastiska smoothies"
    )


def brev_misslyckat(fornamn: str | None) -> str:
    halsning = f"Hej {fornamn}," if fornamn else "Hej,"
    return (
        f"{halsning}\n\n"
        "Tack för ditt önskemål. Den här gången blev det inte som vi tänkt oss, "
        "och vi skickar hellre något riktigt bra än något halvfärdigt.\n\n"
        "Skriv gärna igen om en stund, så gör vi ett nytt försök.\n\n"
        "Vänliga hälsningar\n"
        "Fantastiska smoothies"
    )


# ---------------------------------------------------------------- mailsidan


def svara(post: dict, amne: str, text: str, torr: bool, spar: str) -> None:
    if torr:
        logg.info("Torrkörning: skickar inget svar till %s («%s»).", spar, amne)
        return
    try:
        mail.skicka_svar(post["avsandare"], amne, text)
        logg.info("Svar skickat till %s.", spar)
    except Exception as fel:
        # Inget stackspår: smtplib bär mottagarens adress i sina egna undantag,
        # och loggen ska aldrig innehålla en mailadress (CONTRACT.md §7).
        logg.error("Kunde inte skicka svar till %s: %s", spar, type(fel).__name__)


def markera(post: dict, torr: bool, spar: str) -> None:
    if torr:
        logg.info("Torrkörning: markerar inte %s som hanterat.", spar)
        return
    try:
        mail.markera_hanterad(post["uid"])
    except Exception as fel:
        logg.error("Kunde inte markera önskemålet från %s som hanterat: %s",
                   spar, type(fel).__name__)


def anteckna(onskemalslogg: dict, post: dict, hash_: str, fornamn: str | None,
             smoothie_id: str | None, status: str, torr: bool) -> None:
    """Skriver en rad i onskemal.json. Aldrig mailadressen — bara hashen."""
    onskemalslogg.setdefault("hanterade", []).append({
        "uid": str(post.get("uid", "")),
        "avsandare_hash": hash_,
        "fornamn": fornamn,
        "mottaget": post.get("mottaget") or datetime.now().astimezone().isoformat(timespec="seconds"),
        "smoothie_id": smoothie_id,
        "status": status,
    })
    if torr:
        logg.info("Torrkörning: skriver inte önskemålsloggen.")
        return
    try:
        publicera.skriv_onskemalslogg(onskemalslogg)
    except Exception as fel:
        logg.error("Kunde inte skriva önskemålsloggen: %s", type(fel).__name__)


# ---------------------------------------------------------------- bryggningen


def _skapa(onskemal: str | None, befintliga: list[dict], fornamn: str | None = None,
           tema: str | None = None) -> dict:
    """recept.skapa_smoothie enligt kontraktet.

    Förnamnet går med hela vägen in i prompten. Det är hela poängen med
    CONTRACT.md §2b: smoothien ska bära gästens namn i namnet och i
    beskrivningen, och det kan modellen bara göra om den får veta namnet innan
    texten skrivs. Att sätta onskad_av efteråt ger bara ett kort som säger
    «Önskad av Elin» ovanpå en helt opersonlig smoothie.
    """
    extra: dict[str, str] = {}
    try:
        parametrar = inspect.signature(recept.skapa_smoothie).parameters
    except (TypeError, ValueError):
        parametrar = {}
    if fornamn and "fornamn" in parametrar:
        extra["fornamn"] = fornamn
    if tema and "tema" in parametrar:
        extra["tema"] = tema
    return recept.skapa_smoothie(onskemal, befintliga, **extra)


def brygg(onskemal: str | None, fornamn: str | None, citat: str | None,
          tema: str | None = None, forsok: int = 2) -> dict | None:
    """Recept → granskning → bild → publicering. None om det inte gick."""
    data = publicera.las_data()
    befintliga = data.get("smoothies", [])

    smoothie: dict | None = None
    for n in range(1, forsok + 1):
        try:
            kandidat = _skapa(onskemal, befintliga, fornamn, tema)
        except RuntimeError as fel:
            # recept.py har redan gjort sina egna omtag mot granskningen. Fler
            # försök härifrån kostar bara mer utan att bli bättre.
            logg.error("Receptet kom inte igenom granskningen: %s", fel)
            return None
        kandidat["onskad_av"] = fornamn
        kandidat["onskemal"] = citat
        brott = recept.granska(kandidat)
        if not brott:
            smoothie = kandidat
            break
        logg.warning("Granskningen stoppade förslaget (försök %d av %d): %s",
                     n, forsok, "; ".join(brott))
    if smoothie is None:
        return None

    # Id:t låses innan bilden görs, så att bildens filnamn och id:t är samma.
    smoothie["id"] = publicera.unik_id(smoothie.get("id") or smoothie.get("namn", ""), data)
    smoothie["bild"] = f"assets/bilder/{smoothie['id']}.webp"

    BILDMAPP.mkdir(parents=True, exist_ok=True)
    bildfil = bild.generera_bild(smoothie, BILDMAPP)
    logg.info("Bild klar: %s", Path(bildfil).name)

    publicera.lagg_till(smoothie)
    logg.info("Publicerad: %s (%s)", smoothie["namn"], smoothie["id"])
    return smoothie


def hantera_onskemal(post: dict, onskemalslogg: dict, torr: bool) -> dict | None:
    """Ett önskemål, hela vägen. Returnerar smoothien om den blev publicerad."""
    hash_ = sparrar.hash_avsandare(post["avsandare"])
    text = sparrar.rensa_text(post.get("text") or "")
    fornamn = _rent_fornamn(post.get("fornamn") or sparrar.fornamn_ur(text, post["avsandare"]))
    spar = _spar(hash_, fornamn)
    logg.info("Önskemål från %s, %d tecken efter rensning.", spar, len(text))

    if not sparrar.inom_kvot(hash_, onskemalslogg):
        # Ett svar per avsändare och dygn, inte ett per brev. From-huvudet är
        # oautentiserat, så den som förfalskar det pekar våra svar mot någon
        # annan — brevlådan får inte gå att använda som reflektor.
        if _poster_senaste_dygnet(onskemalslogg, "kvot", hash_):
            logg.info("%s: över dygnskvoten, har redan fått besked — tiger.", spar)
        else:
            logg.info("%s: över dygnskvoten.", spar)
            svara(post, AMNE_KVOT, brev_kvot(fornamn), torr, spar)
        anteckna(onskemalslogg, post, hash_, fornamn, None, "kvot", torr)
        markera(post, torr, spar)
        return None

    duger, skal = (False, "tomt mail") if not text else sparrar.ar_rimligt_onskemal(text)
    if not duger:
        logg.info("%s: avvisat (%s).", spar, skal)
        svara(post, AMNE_TACK, brev_avvisat(fornamn), torr, spar)
        anteckna(onskemalslogg, post, hash_, fornamn, None, "avvisad", torr)
        markera(post, torr, spar)
        return None

    smoothie = brygg(text, fornamn, _citat_ur(text))
    if smoothie is None:
        logg.error("%s: kunde inte brygga något som klarade granskningen.", spar)
        svara(post, AMNE_TACK, brev_misslyckat(fornamn), torr, spar)
        anteckna(onskemalslogg, post, hash_, fornamn, None, "fel", torr)
        markera(post, torr, spar)
        return None

    svara(post, f"Din smoothie: {smoothie['namn']}", brev_klar(fornamn, smoothie), torr, spar)
    anteckna(onskemalslogg, post, hash_, fornamn, smoothie["id"], "publicerad", torr)
    markera(post, torr, spar)
    return smoothie


def valj_tema(befintliga: list[dict], antal_senaste: int = 8) -> str:
    """Ett tema som inte redan står bland de senaste smoothierna."""
    bitar: list[str] = []
    for s in befintliga[:antal_senaste]:
        bitar.append(s.get("namn", ""))
        bitar.append(s.get("underrubrik", ""))
        bitar.extend(s.get("smakprofil", []))
        bitar.extend(rad.get("vara", "") for rad in s.get("ingredienser", []) if isinstance(rad, dict))
    redan_sagt = " ".join(bitar).lower()

    teman = HUSETS_TEMAN[:]
    random.shuffle(teman)
    for tema, nyckelord in teman:
        if not any(ord_ in redan_sagt for ord_ in nyckelord):
            return tema
    return teman[0][0]


def brygg_husets() -> dict | None:
    tema = valj_tema(publicera.las_data().get("smoothies", []))
    logg.info("Temat blir «%s».", tema)
    return brygg(None, None, None, tema=tema)


# ---------------------------------------------------------------- körningen


def tolka_argument(argv: list[str] | None = None) -> argparse.Namespace:
    tolk = argparse.ArgumentParser(
        prog="python3 -m generator.brygg",
        description="Läser brevlådan, brygger smoothies och publicerar dem.",
    )
    tolk.add_argument("--torr", action="store_true",
                      help="skicka inga mail och ladda inte upp — allt annat körs")
    tolk.add_argument("--bara-husets", dest="bara_husets", action="store_true",
                      help="hoppa över brevlådan och brygg husets egen på en gång, "
                           "utan att vänta in dygnet")
    tolk.add_argument("--antal", type=int, default=None, metavar="N",
                      help=f"brygg högst N smoothies den här körningen — sänker "
                           f"taket, höjer det aldrig (högst {MAX_NYA_PER_KORNING} "
                           f"per körning och {MAX_NYA_PER_DYGN} per dygn)")
    return tolk.parse_args(argv)


def tak_for_korningen(args: argparse.Namespace, onskemalslogg: dict) -> tuple[int, str]:
    """Hur många önskemål körningen får brygga. Andra värdet är skälet, för loggen.

    Taken gäller oavsett --antal. En bryggd smoothie kostar riktiga pengar och
    brevlådan är öppen: dygnskvoten i sparrar.py räknas per avsändaradress, och
    den adressen väljer avsändaren själv. Utan ett tak här räcker det med ett
    knippe adresser för att fylla varje körning, dygnet runt.
    """
    redan = _poster_senaste_dygnet(onskemalslogg, "publicerad")
    kvar_i_dygnet = MAX_NYA_PER_DYGN - redan
    if kvar_i_dygnet <= 0:
        return 0, (f"dygnets tak på {MAX_NYA_PER_DYGN} är nått "
                   f"({redan} bryggda det senaste dygnet)")
    tak = min(MAX_NYA_PER_KORNING, kvar_i_dygnet)
    skal = f"högst {MAX_NYA_PER_KORNING} per körning"
    if kvar_i_dygnet < MAX_NYA_PER_KORNING:
        skal = f"{kvar_i_dygnet} kvar av dygnets {MAX_NYA_PER_DYGN}"
    if args.antal is not None and args.antal < tak:
        tak, skal = args.antal, f"--antal {args.antal}"
    return tak, skal


def _brygg_husets_nu(args: argparse.Namespace) -> tuple[list[dict], bool]:
    """Husets egen, en eller flera. Andra värdet säger om något gick fel."""
    nya: list[dict] = []
    gick_fel = False
    # Bara den handpålagda körningen får be om flera på en gång — schemat ger
    # aldrig mer än en (CONTRACT.md §8).
    antal = args.antal if (args.bara_husets and args.antal) else 1
    for _ in range(antal):
        try:
            smoothie = brygg_husets()
            if smoothie:
                nya.append(smoothie)
            else:
                logg.error("Husets egen klarade inte granskningen den här gången.")
                gick_fel = True
        except Exception:
            logg.exception("Husets egen gick inte att brygga.")
            gick_fel = True
    return nya, gick_fel


def main(argv: list[str] | None = None) -> int:
    args = tolka_argument(argv)
    stall_in_logg()
    if args.antal is not None and args.antal < 1:
        logg.error("--antal måste vara minst 1.")
        return 2
    logg.info("── Bryggning startar%s ──", " (torrkörning)" if args.torr else "")

    publicerade: list[dict] = []
    hanterade = 0            # önskemål som fått ett svar, publicerade eller ej
    nagot_gick_fel = False

    # ---- brevlådan, varje körning
    onskemal: list[dict] = []
    if args.bara_husets:
        logg.info("Rör inte brevlådan (--bara-husets).")
    else:
        try:
            onskemal = mail.hamta_onskemal()
            logg.info("Hämtade %d olästa önskemål.", len(onskemal))
        except Exception:
            logg.exception("Kom inte åt brevlådan.")
            nagot_gick_fel = True

    if onskemal:
        onskemalslogg = publicera.las_onskemalslogg()
        tak, skal = tak_for_korningen(args, onskemalslogg)
        # Breven som inte får plats lämnas olästa och tas om nästa timme —
        # hellre det än att brygga upp hela dygnets budget på en körning.
        if tak <= 0:
            logg.info("Brygger inget den här körningen: %s. Breven ligger kvar.", skal)
        for post in onskemal if tak > 0 else []:
            if len(publicerade) >= tak:
                logg.info("Taket är nått (%s) — resten väntar till nästa körning.", skal)
                break
            try:
                smoothie = hantera_onskemal(post, onskemalslogg, args.torr)
                hanterade += 1
                if smoothie:
                    publicerade.append(smoothie)
            except Exception:
                # Ett trasigt mail får aldrig stoppa hela körningen. Mailet lämnas
                # omarkerat och tas om vid nästa körning.
                logg.exception("Fel i önskemålet med uid %s — hoppar vidare till nästa.",
                               post.get("uid"))
                nagot_gick_fel = True

    if not args.bara_husets:
        try:
            mail.stang()   # brevlådan behövs inte längre den här körningen
        except Exception:
            logg.debug("Kunde inte stänga brevlådan.", exc_info=True)

    # ---- husets egen, en helt annan takt: högst en per dygn (CONTRACT.md §8)
    if publicerade:
        logg.info("Sajten fick något nytt den här körningen — huset står över.")
    else:
        dags, skal = dags_for_husets(publicera.las_data())
        if args.bara_husets and not dags:
            # --bara-husets skrivs för hand av en människa och går före takten.
            logg.info("Huset hade stått över (%s) — men --bara-husets säger till.", skal)
            dags, skal = True, "--bara-husets"
        if not dags:
            logg.info("Huset står över: %s.", skal)
        else:
            logg.info("Huset brygger en egen: %s.", skal)
            nya, gick_fel = _brygg_husets_nu(args)
            publicerade.extend(nya)
            nagot_gick_fel = nagot_gick_fel or gick_fel

    # ---- uppladdning, bara om något faktiskt ändrats
    if not (publicerade or hanterade):
        logg.info("Ingenting att göra den här gången — inget laddas upp.")
    elif args.torr:
        logg.info("Torrkörning: laddar inte upp.%s",
                  " Lokala filer i site/ är ändrade." if publicerade else "")
    else:
        try:
            publicera.ladda_upp()
        except RuntimeError as fel:
            # Saknade uppgifter i .env — säg vad som fattas, inte en stackdump.
            logg.error("%s Filerna ligger kvar lokalt.", fel)
            nagot_gick_fel = True
        except Exception:
            logg.exception("Uppladdningen misslyckades — filerna ligger kvar lokalt.")
            nagot_gick_fel = True

    if publicerade:
        logg.info("── Klart: %d nya smoothies (%s) ──", len(publicerade),
                  ", ".join(s["namn"] for s in publicerade))
    else:
        logg.info("── Klart: inget nytt den här gången ──")
    # En tom körning är det normala fallet och alltså ingen felkod.
    return 1 if nagot_gick_fel else 0


if __name__ == "__main__":
    raise SystemExit(main())
