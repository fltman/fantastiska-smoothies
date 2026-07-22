"""Genererar smoothiens bild och sparar den som webp.

Flödet är två steg:

1. gemini-imagegen-skillens ``generate_image.py`` körs som subprocess med
   smoothiens bildprompt och skriver en temporär råbild.
2. ``cwebp`` beskär råbilden till en kvadrat, skalar till 1024x1024 och sparar
   ``site/assets/bilder/{id}.webp`` med kvalitet 82 (CONTRACT.md §6).

Råbilden ligger i en temporär katalog och försvinner när funktionen är klar,
även om något går fel på vägen. Finns webp-filen redan görs ingen ny bild —
att generera om en bild kostar pengar och gör om något som redan står på
sajten.

Inga hemligheter finns i den här filen. Nyckeln läses ur generator/.env, och den
är det enda ur miljön som följer med subprocessen — brevlådans lösenord,
SFTP-lösenordet och saltet stannar hos generatorn.
"""

from __future__ import annotations

import logging
import os
import shutil
import re
import subprocess
import sys
import tempfile
from pathlib import Path

logg = logging.getLogger("brygg.bild")

# ---------------------------------------------------------------------------
# Konstanter
# ---------------------------------------------------------------------------

BILDSIDA = 1024
WEBP_KVALITET = 82
ANTAL_FORSOK = 2

_ENV_FIL = Path(__file__).resolve().parent / ".env"

# Skillen som gör bilden. Går att peka om med SMOOTHIE_BILDSKRIPT.
_STANDARD_BILDSKRIPT = (
    Path.home() / ".claude" / "skills" / "gemini-imagegen" / "scripts" / "generate_image.py"
)

# Sekunder innan vi ger upp. Bildmodellen är långsam, cwebp är snabb.
TIMEOUT_BILD_STANDARD = 300
TIMEOUT_CWEBP = 60

_PNG_SIGNATUR = b"\x89PNG\r\n\x1a\n"

# Det enda som släpps vidare till bildskriptet, utöver API-nyckeln: sökvägar,
# teckenkodning, certifikat och en eventuell proxy. Bildskriptet ligger utanför
# det här repot och behöver ingenting av det som rör brevlådan eller servern.
_MILJO_ATT_SLAPPA_IGENOM = (
    "PATH", "HOME", "LANG", "LC_ALL", "TMPDIR",
    "SSL_CERT_FILE", "SSL_CERT_DIR", "REQUESTS_CA_BUNDLE",
    "HTTP_PROXY", "HTTPS_PROXY", "NO_PROXY",
    "http_proxy", "https_proxy", "no_proxy",
)


class BildFel(RuntimeError):
    """Bilden kunde inte genereras eller konverteras."""


# ---------------------------------------------------------------------------
# Små hjälpare
# ---------------------------------------------------------------------------

def _ladda_env() -> None:
    """Läser generator/.env in i os.environ utan att skriva över befintliga."""
    if not _ENV_FIL.exists():
        return
    for rad in _ENV_FIL.read_text(encoding="utf-8").splitlines():
        rad = rad.strip()
        if not rad or rad.startswith("#") or "=" not in rad:
            continue
        nyckel, _, varde = rad.partition("=")
        os.environ.setdefault(nyckel.strip(), varde.strip().strip("\"'"))


def _timeout_bild() -> int:
    """Läses vid anrop, inte vid import, så att .env hinner laddas."""
    try:
        return max(30, int(os.environ.get("SMOOTHIE_BILD_TIMEOUT", "")))
    except ValueError:
        return TIMEOUT_BILD_STANDARD


def _bildskript() -> Path:
    egen = os.environ.get("SMOOTHIE_BILDSKRIPT")
    # Absolut sökväg: subprocessen körs i en temporär katalog, så en relativ
    # sökväg skulle peka fel där.
    skript = (Path(egen).expanduser() if egen else _STANDARD_BILDSKRIPT).resolve()
    if not skript.is_file():
        raise BildFel(
            f"Hittar inte bildgeneratorn: {skript}. Installera gemini-imagegen-"
            "skillen eller peka om med SMOOTHIE_BILDSKRIPT."
        )
    return skript


def _cwebp() -> str:
    egen = os.environ.get("SMOOTHIE_CWEBP")
    if egen:
        if not Path(egen).expanduser().is_file():
            raise BildFel(f"SMOOTHIE_CWEBP pekar på något som inte finns: {egen}")
        return str(Path(egen).expanduser())
    hittad = shutil.which("cwebp")
    if not hittad:
        raise BildFel(
            "cwebp saknas. Installera webp (brew install webp) eller peka ut "
            "binären med SMOOTHIE_CWEBP."
        )
    return hittad


def _png_storlek(fil: Path) -> tuple[int, int] | None:
    """Bredd och höjd ur PNG:ens IHDR-block. None om det inte är en PNG."""
    with fil.open("rb") as strom:
        huvud = strom.read(24)
    if len(huvud) < 24 or huvud[:8] != _PNG_SIGNATUR:
        return None
    bredd = int.from_bytes(huvud[16:20], "big")
    hojd = int.from_bytes(huvud[20:24], "big")
    return (bredd, hojd) if bredd > 0 and hojd > 0 else None


def _jpeg_storlek(fil: Path) -> tuple[int, int] | None:
    """Bredd och höjd ur JPEG:ens SOF-block. None om det inte är en JPEG.

    Bildmodellen svarar nästan alltid med PNG, men inte alltid — och en JPEG
    med filändelsen .png ska inte stoppa bryggningen.
    """
    with fil.open("rb") as strom:
        if strom.read(2) != b"\xff\xd8":
            return None
        while True:
            byte = strom.read(1)
            while byte and byte != b"\xff":
                byte = strom.read(1)
            markor = strom.read(1)
            while markor == b"\xff":          # utfyllnad före markören
                markor = strom.read(1)
            if not markor:
                return None
            # SOF0–SOF15, utom de fyra som inte bär bildmått.
            if 0xC0 <= markor[0] <= 0xCF and markor[0] not in (0xC4, 0xC8, 0xCC):
                strom.read(3)                 # längd (2) + precision (1)
                matt = strom.read(4)
                if len(matt) < 4:
                    return None
                hojd = int.from_bytes(matt[0:2], "big")
                bredd = int.from_bytes(matt[2:4], "big")
                return (bredd, hojd) if bredd > 0 and hojd > 0 else None
            langd = strom.read(2)
            if len(langd) < 2:
                return None
            strom.seek(int.from_bytes(langd, "big") - 2, os.SEEK_CUR)


def _bildmatt(fil: Path) -> tuple[int, int] | None:
    """Bildens mått, eller None om formatet inte gick att läsa."""
    try:
        return _png_storlek(fil) or _jpeg_storlek(fil)
    except OSError:
        return None


def _minimal_miljo(nyckel: str) -> dict[str, str]:
    """Bygger en avskalad miljö åt bildskriptet.

    Vid det här laget har generatorns moduler lagt hela generator/.env i
    os.environ — brevlådans lösenord, SFTP-lösenordet och saltet ligger där.
    Inget av det behövs för att rita ett glas, så subprocessen får bara nyckeln
    till OpenRouter och det som krävs för att den ska kunna köra alls.
    """
    miljo = {namn: os.environ[namn]
             for namn in _MILJO_ATT_SLAPPA_IGENOM if os.environ.get(namn)}
    miljo["OPENROUTER_API_KEY"] = nyckel
    return miljo


def _utan_nyckel(text: str, nyckel: str) -> str:
    """Maskar API-nyckeln i något subprocessen skrivit innan det når loggen."""
    if not text or not nyckel:
        return text or ""
    return text.replace(nyckel, "[nyckel]")


def _kort(text: str, langd: int = 600) -> str:
    text = (text or "").strip()
    return text if len(text) <= langd else text[:langd] + " …"


def _stada_bort(fil: Path) -> None:
    """Tar bort en halvfärdig fil utan att låta städningen kasta vidare."""
    try:
        fil.unlink(missing_ok=True)
    except OSError:
        logg.debug("Kunde inte ta bort %s.", fil.name, exc_info=True)


# ---------------------------------------------------------------------------
# Stegen
# ---------------------------------------------------------------------------

def _generera_png(bildprompt: str, png: Path, arbetsmapp: Path) -> None:
    """Kör gemini-imagegen-skillen tills vi har en PNG på plats."""
    skript = _bildskript()
    _ladda_env()
    nyckel = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not nyckel:
        raise BildFel(
            "OPENROUTER_API_KEY saknas. Lägg den i generator/.env "
            "(filen är gitignorerad och laddas aldrig upp)."
        )

    miljo = _minimal_miljo(nyckel)
    tidsgrans = _timeout_bild()

    kommando = [sys.executable, str(skript), "--prompt", bildprompt,
                "--output", str(png)]
    modell = os.environ.get("SMOOTHIE_BILDMODELL", "").strip()
    if modell:
        kommando += ["--model", modell]

    sista_fel = ""
    for forsok in range(1, ANTAL_FORSOK + 1):
        try:
            resultat = subprocess.run(
                kommando,
                capture_output=True,
                text=True,
                timeout=tidsgrans,
                env=miljo,
                cwd=str(arbetsmapp),
                check=False,
            )
        except subprocess.TimeoutExpired as orsak:
            sista_fel = f"tidsgränsen {tidsgrans} s passerades"
            if forsok == ANTAL_FORSOK:
                raise BildFel(f"Bildgenereringen tog för lång tid: {sista_fel}.") from orsak
            logg.warning("Bildgenereringen tog för lång tid — försöker en gång till.")
            continue

        if resultat.returncode == 0 and png.is_file() and png.stat().st_size > 0:
            return

        sista_fel = (_kort(_utan_nyckel(resultat.stderr, nyckel))
                     or _kort(_utan_nyckel(resultat.stdout, nyckel))
                     or "okänt fel")
        _stada_bort(png)
        if forsok < ANTAL_FORSOK:
            logg.warning("Bildgeneratorn gav inget — försöker en gång till: %s",
                         sista_fel)

    raise BildFel(
        f"Bildgeneratorn misslyckades efter {ANTAL_FORSOK} försök: {sista_fel}"
    )


def _till_webp(kalla: Path, webp: Path) -> None:
    """Beskär till kvadrat, skalar till 1024x1024 och sparar som webp."""
    argument = [_cwebp(), "-q", str(WEBP_KVALITET), "-metadata", "none"]

    matt = _bildmatt(kalla)
    if matt is None:
        # Okänt format. Prompten ber alltid om 1:1, så vi skalar rakt av och
        # låter cwebp säga ifrån om filen inte går att läsa alls.
        logg.warning("Kunde inte läsa bildens mått — skalar utan beskärning.")
        argument += ["-resize", str(BILDSIDA), str(BILDSIDA)]
    else:
        bredd, hojd = matt
        sida = min(bredd, hojd)
        if bredd != hojd:
            # Mitten av bilden — glaset står centrerat i promptens komposition.
            argument += ["-crop", str((bredd - sida) // 2), str((hojd - sida) // 2),
                         str(sida), str(sida)]
        if sida != BILDSIDA:
            argument += ["-resize", str(BILDSIDA), str(BILDSIDA)]

    argument += [str(kalla), "-o", str(webp)]

    try:
        resultat = subprocess.run(
            argument, capture_output=True, text=True,
            timeout=TIMEOUT_CWEBP, check=False,
        )
    except subprocess.TimeoutExpired as orsak:
        _stada_bort(webp)
        raise BildFel(f"cwebp tog längre tid än {TIMEOUT_CWEBP} s.") from orsak

    if resultat.returncode != 0 or not webp.is_file() or webp.stat().st_size == 0:
        _stada_bort(webp)
        raise BildFel(
            "cwebp kunde inte konvertera bilden: "
            + (_kort(resultat.stderr) or "okänt fel")
        )

    with webp.open("rb") as strom:
        huvud = strom.read(12)
    if huvud[:4] != b"RIFF" or huvud[8:12] != b"WEBP":
        _stada_bort(webp)
        raise BildFel("cwebp skrev något som inte är en webp-fil.")


# ---------------------------------------------------------------------------
# Huvudfunktionen
# ---------------------------------------------------------------------------

def generera_bild(smoothie: dict, ut_mapp, tvinga: bool = False) -> Path:
    """Genererar smoothiens bild och returnerar sökvägen till webp-filen.

    smoothie  måste ha 'id' och 'bildprompt'
    ut_mapp   site/assets/bilder (skapas om den saknas)
    tvinga    gör om bilden fast den redan finns. Kostar pengar — sätts bara
              när Anders bett om det.
    """
    smoothie_id = str(smoothie.get("id", "")).strip()
    bildprompt = str(smoothie.get("bildprompt", "")).strip()
    if not smoothie_id:
        raise BildFel("Smoothien saknar id — vet inte vad bilden ska heta.")
    if not bildprompt:
        raise BildFel(f"Smoothien {smoothie_id} saknar bildprompt.")

    # Id:t härstammar ur modellens svar och blir här ett filnamn. En modell som
    # påverkats av ett illvilligt önskemål kan föreslå «../../inc/config» eller
    # något med snedstreck i. Vi kräver kebab-case och kontrollerar dessutom att
    # den färdiga sökvägen faktiskt hamnar i bildmappen.
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", smoothie_id):
        raise BildFel(f"Id:t «{smoothie_id}» är inte kebab-case — vägrar skriva en fil med det namnet.")

    mapp = Path(ut_mapp).expanduser().resolve()
    mapp.mkdir(parents=True, exist_ok=True)
    webp = (mapp / f"{smoothie_id}.webp").resolve()
    if webp.parent != mapp:
        raise BildFel(f"Bildsökvägen för «{smoothie_id}» hamnar utanför bildmappen.")

    # Bilden finns redan. Att göra om den kostar pengar och skriver över något
    # som redan står på sajten — vi lämnar den i fred.
    if webp.is_file() and webp.stat().st_size > 0 and not tvinga:
        logg.info("Bilden %s finns redan — genererar inte om den.", webp.name)
        return webp

    with tempfile.TemporaryDirectory(prefix="smoothiebild-") as tillfallig:
        arbetsmapp = Path(tillfallig)
        rabild = arbetsmapp / f"{smoothie_id}.png"
        _generera_png(bildprompt, rabild, arbetsmapp)
        _till_webp(rabild, webp)

    logg.info("Bilden klar: %s (%d kB).", webp.name, webp.stat().st_size // 1024)
    return webp
