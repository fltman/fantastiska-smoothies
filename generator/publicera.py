"""Publicering — skriver smoothiedata till site/data/ och lägger upp sajten.

Två ansvar:

1. Datalagret. `site/data/smoothies.json` och `site/data/onskemal.json` skrivs
   alltid atomiskt: temporärfil i samma mapp, fsync, `os.replace`. En avbruten
   körning kan alltså aldrig lämna en halvskriven JSON efter sig, och sajten
   läser antingen den gamla eller den nya filen — aldrig något däremellan.
2. Uppladdningen. `ladda_upp()` speglar `site/` till one.com genom att packa
   mappen till en tar-ström och packa upp den över ssh — allt utom det som
   `samla_filer()` utesluter, däribland önskemålsloggen. one.coms
   SSH-proxy tillhandahåller inte sftp-subsystemet — både `sftp` och paramikos
   open_sftp() svarar "Connection closed" — men vanliga ssh-kommandon fungerar.
   paramiko- och sftp-grenarna finns kvar som reserv för andra servrar.

Allt som skrivs valideras mot datamodellen i CONTRACT.md §3 först. Den hårda
regeln i §2 (aldrig näring, kalorier eller viktprat) granskas av `recept.granska`
innan `lagg_till` anropas — här kontrolleras formen, inte tonen.

Bara standardbiblioteket krävs. paramiko är valfritt.
"""

from __future__ import annotations

import json
import logging
import os
import posixpath
import re
import shutil
import subprocess
import tempfile
import unicodedata
from datetime import date, datetime
from pathlib import Path

logg = logging.getLogger(__name__)

ROT = Path(__file__).resolve().parent.parent
SITE = ROT / "site"
DATA = SITE / "data"
BILDMAPP = SITE / "assets" / "bilder"
SMOOTHIEFIL = DATA / "smoothies.json"
ONSKEMALSFIL = DATA / "onskemal.json"
ENVFIL = ROT / "generator" / ".env"

SCHEMAVERSION = 1

# Filer som aldrig följer med upp till webben.
UTESLUTNA_SUFFIX = {".png", ".psd", ".tmp", ".bak"}
UTESLUTNA_NAMN = {".DS_Store", "Thumbs.db"}
UTESLUTNA_MAPPAR = {"__pycache__", ".git", "arbetsyta"}
# Enskilda sökvägar under site/ som stannar på Anders dator, skrivna relativt
# site/ med snedstreck. onskemal.json är generatorns egen kö och logg: sajten
# läser den aldrig, men den bär uid, saltat hash av avsändaradressen, förnamn
# och tidpunkt för var och en som har mailat in. På servern skyddas den bara av
# .htaccess — är AllowOverride avstängd, eller flyttas sajten till något annat
# än Apache, ligger uppgifterna öppna. Alltså går den inte upp alls.
UTESLUTNA_SOKVAGAR = {"data/onskemal.json"}
# Punktfiler hoppas över — utom dessa, som sajten behöver.
TILLATNA_PUNKTFILER = {".htaccess"}

ID_MONSTER = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
FARG_MONSTER = re.compile(r"^#[0-9a-fA-F]{6}$")
DATUM_MONSTER = re.compile(r"^\d{4}-\d{2}-\d{2}$")
# Sista raden i stilsuffixet, CONTRACT.md §6. Finns den inte har bildprompten
# inte byggts på husets stil.
STILSUFFIX_SLUT = "Square composition, 1:1."


# ---------------------------------------------------------------- miljö


def las_env() -> dict[str, str]:
    """Läser generator/.env. Värden i den riktiga miljön vinner över filen.

    Returnerar en vanlig dict. Innehållet skrivs aldrig till loggen.
    """
    varden: dict[str, str] = {}
    if ENVFIL.exists():
        for rad in ENVFIL.read_text(encoding="utf-8").splitlines():
            rad = rad.strip()
            if not rad or rad.startswith("#") or "=" not in rad:
                continue
            nyckel, _, varde = rad.partition("=")
            varden[nyckel.strip()] = varde.strip().strip('"').strip("'")
    for nyckel in list(varden):
        if os.environ.get(nyckel):
            varden[nyckel] = os.environ[nyckel]
    for nyckel in ("SFTP_HOST", "SFTP_ANVANDARE", "SFTP_LOSENORD", "SFTP_MAPP",
                   "SFTP_PORT", "SAJT_URL", "HUSETS_EGEN_TIMMAR"):
        if nyckel not in varden and os.environ.get(nyckel):
            varden[nyckel] = os.environ[nyckel]
    return varden


# ---------------------------------------------------------------- atomisk skrivning


def _skriv_json(sokvag: Path, data: dict) -> None:
    """Skriver JSON atomiskt: temporärfil i samma mapp, fsync, os.replace."""
    sokvag.parent.mkdir(parents=True, exist_ok=True)
    fd, tillfallig = tempfile.mkstemp(dir=sokvag.parent, prefix=sokvag.name + ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tillfallig, sokvag)
        # Fsynca även katalogen så att själva namnbytet överlever ett strömavbrott.
        katalog = os.open(sokvag.parent, os.O_RDONLY)
        try:
            os.fsync(katalog)
        finally:
            os.close(katalog)
    except BaseException:
        Path(tillfallig).unlink(missing_ok=True)
        raise


def _nu() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _las_json(sokvag: Path, standard: dict) -> dict:
    if not sokvag.exists():
        return dict(standard)
    try:
        data = json.loads(sokvag.read_text(encoding="utf-8"))
    except json.JSONDecodeError as fel:
        raise ValueError(f"{sokvag.name} är trasig JSON: {fel}") from fel
    if not isinstance(data, dict):
        raise ValueError(f"{sokvag.name} måste innehålla ett objekt på toppnivån.")
    return data


# ---------------------------------------------------------------- smoothies.json


def las_data() -> dict:
    """Hela smoothiefilen. Saknas den får du en tom, giltig struktur."""
    data = _las_json(SMOOTHIEFIL, {"version": SCHEMAVERSION, "uppdaterad": _nu(), "smoothies": []})
    data.setdefault("version", SCHEMAVERSION)
    data.setdefault("uppdaterad", _nu())
    if not isinstance(data.get("smoothies"), list):
        data["smoothies"] = []
    return data


def slugga(text: str) -> str:
    """Poetiskt namn → ASCII-slug. å och ä blir a, ö blir o (CONTRACT.md §3)."""
    text = text.strip().lower()
    text = text.replace("å", "a").replace("ä", "a").replace("ö", "o")
    text = text.replace("é", "e").replace("è", "e").replace("ü", "u")
    text = unicodedata.normalize("NFKD", text)
    text = "".join(t for t in text if not unicodedata.combining(t))
    text = re.sub(r"[^a-z0-9]+", "-", text.encode("ascii", "ignore").decode("ascii"))
    return text.strip("-") or "smoothie"


def unik_id(forslag: str, data: dict | None = None) -> str:
    """Ger ett id som inte redan är taget. Anropas innan bilden genereras,
    så att bildens filnamn och smoothiens id garanterat är samma."""
    data = data if data is not None else las_data()
    tagna = {s.get("id") for s in data.get("smoothies", [])}
    tagna |= {p.stem for p in BILDMAPP.glob("*.webp")} if BILDMAPP.exists() else set()
    bas = slugga(forslag)
    kandidat = bas
    n = 2
    while kandidat in tagna:
        kandidat = f"{bas}-{n}"
        n += 1
    return kandidat


def _text(varde) -> str:
    return varde.strip() if isinstance(varde, str) else ""


def normalisera(smoothie: dict) -> dict:
    """Städar en smoothie inför skrivning: trimmar text, fyller i det härledbara.

    Rör aldrig innehållet i orden — bara formen.
    """
    s = dict(smoothie)

    for falt in ("id", "namn", "underrubrik", "beskrivning", "emoji", "knep",
                 "bild_alt", "bildprompt", "publicerad"):
        if falt in s:
            s[falt] = _text(s[falt])

    s["id"] = slugga(s.get("id") or s.get("namn") or "smoothie")

    for falt in ("smakprofil", "gor_sa_har", "toppa_med"):
        varden = s.get(falt) or []
        if isinstance(varden, str):
            varden = [varden]
        s[falt] = [_text(v) for v in varden if _text(v)]
    s["smakprofil"] = [ord_.lower() for ord_ in s["smakprofil"]]

    ingredienser = []
    for rad in s.get("ingredienser") or []:
        if not isinstance(rad, dict):
            continue
        ingredienser.append({
            "mangd": _text(rad.get("mangd")),
            "vara": _text(rad.get("vara")),
            "not": _text(rad.get("not")) or None,
        })
    s["ingredienser"] = ingredienser

    farger = s.get("farger") or {}
    if isinstance(farger, dict):
        s["farger"] = {"start": _text(farger.get("start")), "slut": _text(farger.get("slut"))}

    for falt, standard in (("portioner", 1), ("tid_minuter", 5)):
        try:
            s[falt] = int(s.get(falt, standard))
        except (TypeError, ValueError):
            s[falt] = standard

    if not s.get("publicerad"):
        s["publicerad"] = date.today().isoformat()

    # Bildsökvägen är alltid härledd ur id:t — aldrig något annat.
    s["bild"] = f"assets/bilder/{s['id']}.webp"

    s["onskad_av"] = _text(s.get("onskad_av")) or None
    s["onskemal"] = _text(s.get("onskemal")) or None
    if s["onskemal"]:
        s["onskemal"] = " ".join(s["onskemal"].split())[:140]

    return s


def validera(smoothie: dict) -> list[str]:
    """Kontrollerar en smoothie mot datamodellen. Tom lista = godkänd."""
    fel: list[str] = []
    s = smoothie

    def kravs(falt: str) -> bool:
        if falt not in s or s[falt] is None or s[falt] == "" or s[falt] == []:
            fel.append(f"fältet «{falt}» saknas")
            return False
        return True

    if kravs("id"):
        if not ID_MONSTER.match(s["id"]):
            fel.append(f"id «{s['id']}» är inte kebab-case i ren ASCII")
    if kravs("namn"):
        antal_ord = len(s["namn"].split())
        if not 1 <= antal_ord <= 4:
            fel.append(f"namn ska vara 1–4 ord, är {antal_ord}")
    if kravs("underrubrik") and len(s["underrubrik"]) > 80:
        fel.append(f"underrubrik är {len(s['underrubrik'])} tecken, max ~70")
    if kravs("beskrivning") and len(s["beskrivning"]) < 40:
        fel.append("beskrivning är för kort, ska vara 2–3 meningar")

    if kravs("smakprofil"):
        if not 2 <= len(s["smakprofil"]) <= 4:
            fel.append(f"smakprofil ska ha 2–4 ord, har {len(s['smakprofil'])}")
        for ord_ in s["smakprofil"]:
            if ord_ != ord_.lower():
                fel.append(f"smakprofil «{ord_}» ska vara gemener")

    if kravs("farger"):
        farger = s["farger"]
        if not isinstance(farger, dict):
            fel.append("farger ska vara ett objekt med start och slut")
        else:
            for nyckel in ("start", "slut"):
                varde = farger.get(nyckel, "")
                if not FARG_MONSTER.match(varde or ""):
                    fel.append(f"farger.{nyckel} «{varde}» är inte #RRGGBB")

    if kravs("emoji"):
        if len(s["emoji"]) > 4 or any(t.isascii() and t.isalnum() for t in s["emoji"]):
            fel.append(f"emoji «{s['emoji']}» ska vara en enda emoji")

    if kravs("ingredienser"):
        antal = len(s["ingredienser"])
        if not 5 <= antal <= 9:
            fel.append(f"ingredienser ska vara 5–9 st, är {antal}")
        for i, rad in enumerate(s["ingredienser"], 1):
            if not isinstance(rad, dict):
                fel.append(f"ingrediens {i} är inte ett objekt")
                continue
            if not rad.get("mangd"):
                fel.append(f"ingrediens {i} saknar mängd")
            if not rad.get("vara"):
                fel.append(f"ingrediens {i} saknar vara")
            if rad.get("not") is not None and not isinstance(rad["not"], str):
                fel.append(f"ingrediens {i}: not ska vara text eller null")

    if kravs("gor_sa_har") and not 2 <= len(s["gor_sa_har"]) <= 4:
        fel.append(f"gor_sa_har ska ha 2–4 steg, har {len(s['gor_sa_har'])}")
    if kravs("toppa_med") and not 1 <= len(s["toppa_med"]) <= 3:
        fel.append(f"toppa_med ska ha 1–3 saker, har {len(s['toppa_med'])}")
    kravs("knep")

    if not isinstance(s.get("portioner"), int) or not 1 <= s.get("portioner", 0) <= 4:
        fel.append("portioner ska vara ett heltal 1–4")
    if not isinstance(s.get("tid_minuter"), int) or not 3 <= s.get("tid_minuter", 0) <= 10:
        fel.append("tid_minuter ska vara ett heltal 3–10")

    if kravs("bild") and s["bild"] != f"assets/bilder/{s.get('id')}.webp":
        fel.append(f"bild «{s['bild']}» följer inte assets/bilder/{{id}}.webp")
    kravs("bild_alt")
    if kravs("bildprompt") and not s["bildprompt"].rstrip().endswith(STILSUFFIX_SLUT):
        fel.append("bildprompt saknar husets stilsuffix (CONTRACT §6)")

    if kravs("publicerad"):
        if not DATUM_MONSTER.match(s["publicerad"]):
            fel.append(f"publicerad «{s['publicerad']}» är inte YYYY-MM-DD")
        else:
            try:
                date.fromisoformat(s["publicerad"])
            except ValueError:
                fel.append(f"publicerad «{s['publicerad']}» är inget riktigt datum")

    if "onskad_av" not in s:
        fel.append("fältet «onskad_av» saknas (får vara null)")
    elif s["onskad_av"] is not None:
        namn = s["onskad_av"]
        if not isinstance(namn, str) or "@" in namn or len(namn.split()) != 1 or len(namn) > 24:
            fel.append("onskad_av ska vara ett enda förnamn utan mailadress")

    if "onskemal" not in s:
        fel.append("fältet «onskemal» saknas (får vara null)")
    elif s["onskemal"] is not None:
        if not isinstance(s["onskemal"], str) or len(s["onskemal"]) > 140:
            fel.append("onskemal ska vara text på max 140 tecken eller null")
        elif "@" in s["onskemal"] or "http" in s["onskemal"].lower():
            fel.append("onskemal innehåller mailadress eller länk")

    return fel


def lagg_till(smoothie: dict) -> None:
    """Lägger en ny smoothie först i smoothies.json och skriver filen atomiskt.

    Höjer ValueError om något inte håller måttet — då skrivs ingenting alls.
    """
    data = las_data()
    s = normalisera(smoothie)

    if any(befintlig.get("id") == s["id"] for befintlig in data["smoothies"]):
        s["id"] = unik_id(s["id"], data)
        s["bild"] = f"assets/bilder/{s['id']}.webp"
        logg.warning("Id:t var upptaget — smoothien fick id «%s» istället.", s["id"])

    fel = validera(s)
    if fel:
        raise ValueError("Smoothien följer inte datamodellen: " + "; ".join(fel))

    # Sista grinden före den publika filen. Docstringen har alltid sagt att §2
    # granskas av recept.granska innan lagg_till anropas — men det var en
    # förhoppning om anroparen, inte en invariant. Den kostar ett anrop per
    # publicering och gör påståendet sant.
    try:
        from . import recept
    except ImportError:
        recept = None
    if recept is not None:
        brott = recept.granska(s)
        if brott:
            raise ValueError("Smoothien bryter mot den hårda regeln: " + "; ".join(brott))

    data["smoothies"].insert(0, s)   # nyast först
    data["version"] = SCHEMAVERSION
    data["uppdaterad"] = _nu()
    _skriv_json(SMOOTHIEFIL, data)
    logg.info("Skrev %s (%d smoothies totalt).", SMOOTHIEFIL.name, len(data["smoothies"]))

    # Spegla in i den smoothie anroparen håller i, så att den vet sitt riktiga id.
    smoothie.update(s)


# ---------------------------------------------------------------- onskemal.json


def las_onskemalslogg() -> dict:
    """Kön och loggen över hanterade önskemål (CONTRACT.md §3)."""
    data = _las_json(ONSKEMALSFIL, {"version": SCHEMAVERSION, "hanterade": []})
    data.setdefault("version", SCHEMAVERSION)
    if not isinstance(data.get("hanterade"), list):
        data["hanterade"] = []
    return data


def skriv_onskemalslogg(data: dict) -> None:
    """Skriver önskemålsloggen atomiskt. Full mailadress får aldrig finnas i den."""
    data = dict(data)
    data.setdefault("version", SCHEMAVERSION)
    hanterade = []
    for post in data.get("hanterade", []):
        if not isinstance(post, dict):
            continue
        ren = {n: post.get(n) for n in ("uid", "avsandare_hash", "fornamn",
                                        "mottaget", "smoothie_id", "status")}
        for varde in ren.values():
            if isinstance(varde, str) and "@" in varde:
                raise ValueError("Önskemålsloggen får aldrig innehålla en mailadress.")
        hanterade.append(ren)
    data["hanterade"] = hanterade
    _skriv_json(ONSKEMALSFIL, data)


# ---------------------------------------------------------------- uppladdning


def _sftp_konfig() -> dict:
    env = las_env()
    saknas = [n for n in ("SFTP_HOST", "SFTP_ANVANDARE", "SFTP_MAPP") if not env.get(n)]
    if saknas:
        raise RuntimeError(
            "Uppladdningen kan inte köra — dessa saknas i generator/.env: "
            + ", ".join(saknas)
            + ". Fyll i dem (se generator/.env.example) eller kör med --torr."
        )
    try:
        port = int(env.get("SFTP_PORT") or 22)
    except ValueError:
        port = 22
    return {
        "host": env["SFTP_HOST"],
        "anvandare": env["SFTP_ANVANDARE"],
        "losenord": env.get("SFTP_LOSENORD") or "",
        "mapp": env["SFTP_MAPP"].rstrip("/") or ".",
        "port": port,
    }


def samla_filer() -> list[tuple[Path, str]]:
    """Alla filer i site/ som ska upp, som (lokal sökväg, relativ sökväg).

    Allt som står i uteslutningsmängderna ovan lämnas kvar hemma — särskilt
    önskemålsloggen, som är generatorns interna och inte sajtens.
    """
    filer: list[tuple[Path, str]] = []
    for sokvag in sorted(SITE.rglob("*")):
        if not sokvag.is_file():
            continue
        delar = sokvag.relative_to(SITE).parts
        if any(del_ in UTESLUTNA_MAPPAR for del_ in delar[:-1]):
            continue
        namn = sokvag.name
        if namn in UTESLUTNA_NAMN or sokvag.suffix.lower() in UTESLUTNA_SUFFIX:
            continue
        if namn.startswith(".") and namn not in TILLATNA_PUNKTFILER:
            continue
        relativ = "/".join(delar)
        if relativ in UTESLUTNA_SOKVAGAR:
            continue
        filer.append((sokvag, relativ))
    return filer


def _ladda_upp_paramiko(konfig: dict, filer: list[tuple[Path, str]]) -> tuple[int, int]:
    import paramiko  # valfritt beroende

    klient = paramiko.SSHClient()
    klient.load_system_host_keys()
    # one.com roterar värdnycklar då och då; deployen ska inte stanna för det.
    klient.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    klient.connect(
        hostname=konfig["host"],
        port=konfig["port"],
        username=konfig["anvandare"],
        password=konfig["losenord"] or None,
        # one.coms SSH-proxy (OneSSH-Proxy) stänger sessionen om klienten
        # först provar nycklar och agent. Med lösenord i .env går vi rakt på
        # lösenordet — annars nekas inloggningen med "Permission denied".
        allow_agent=not konfig["losenord"],
        look_for_keys=not konfig["losenord"],
        timeout=30,
    )
    skickade = hoppade = 0
    try:
        sftp = klient.open_sftp()
        skapade: set[str] = set()

        def sakerstall(mapp: str) -> None:
            if not mapp or mapp in (".", "/") or mapp in skapade:
                return
            sakerstall(posixpath.dirname(mapp))
            try:
                sftp.stat(mapp)
            except IOError:
                sftp.mkdir(mapp)
            skapade.add(mapp)

        for lokal, relativ in filer:
            fjarr = posixpath.join(konfig["mapp"], relativ)
            sakerstall(posixpath.dirname(fjarr))
            if lokal.suffix.lower() == ".webp":
                # Bilder ändras aldrig efter att de skapats — hoppa över dem
                # som redan ligger uppe med samma storlek.
                try:
                    if sftp.stat(fjarr).st_size == lokal.stat().st_size:
                        hoppade += 1
                        continue
                except IOError:
                    pass
            sftp.put(str(lokal), fjarr)
            skickade += 1
        sftp.close()
    finally:
        klient.close()
    return skickade, hoppade


def _ssh_flaggor() -> list[str]:
    """
    one.coms proxy stänger sessionen om klienten först provar nyckel och agent —
    inloggningen nekas då med "Permission denied" trots rätt lösenord. Vi går
    därför rakt på lösenordet.
    """
    return [
        "-o", "PreferredAuthentications=password",
        "-o", "PubkeyAuthentication=no",
        "-o", "StrictHostKeyChecking=accept-new",
        "-o", "ConnectTimeout=30",
    ]


def _ladda_upp_tar(konfig: dict, filer: list[tuple[Path, str]]) -> tuple[int, int]:
    """
    Packar site/ till en gzippad tar-ström och packar upp den på servern.

    Hela sajten går i ett svep över en enda ssh-session. Lösenordet lämnas till
    sshpass i miljön (-e), aldrig som argument — annars hade det synts för alla
    som kör `ps` på maskinen.
    """
    fjarrmapp = konfig["mapp"]
    # Bara enkla citattecken behöver skyddas; sökvägen kommer ur vår egen .env.
    saker_mapp = fjarrmapp.replace("'", "'\\''")

    tar_in = ["tar", "czf", "-", "-C", str(SITE)]
    tar_in += [relativ for _, relativ in filer]

    fjarrkommando = (
        f"mkdir -p '{saker_mapp}' && cd '{saker_mapp}' && tar xzf - && "
        f"find . -type f | wc -l"
    )
    ssh = ["ssh", *_ssh_flaggor()]
    if konfig["port"] != 22:
        ssh += ["-p", str(konfig["port"])]
    ssh += [f'{konfig["anvandare"]}@{konfig["host"]}', fjarrkommando]

    miljo = dict(os.environ)
    # macOS tar lägger annars in ._-filer med resursgafflar i arkivet.
    miljo["COPYFILE_DISABLE"] = "1"
    if konfig["losenord"]:
        miljo["SSHPASS"] = konfig["losenord"]
        ssh = ["sshpass", "-e"] + ssh

    packa = subprocess.Popen(tar_in, stdout=subprocess.PIPE, env=miljo)
    try:
        klart = subprocess.run(ssh, stdin=packa.stdout, env=miljo,
                               capture_output=True, text=True, timeout=900)
    finally:
        if packa.stdout:
            packa.stdout.close()
        packa.wait(timeout=30)

    if klart.returncode != 0:
        besked = (klart.stderr or klart.stdout or "").strip().splitlines()
        raise RuntimeError("uppladdningen misslyckades: "
                           + (besked[-1] if besked else "okänt fel"))
    return len(filer), 0


def _ladda_upp_kommandorad(konfig: dict, filer: list[tuple[Path, str]]) -> tuple[int, int]:
    """Reserv när paramiko inte är installerat: sftp med batchfil."""
    if konfig["losenord"] and not shutil.which("sshpass"):
        raise RuntimeError(
            "Kan inte logga in med lösenord utan paramiko eller sshpass. "
            "Kör «pip install -r generator/krav.txt», installera sshpass, "
            "eller lägg upp en ssh-nyckel hos one.com."
        )

    mappar: list[str] = []
    sedda: set[str] = set()
    for _, relativ in filer:
        mapp = posixpath.dirname(relativ)
        delar: list[str] = []
        for del_ in mapp.split("/") if mapp else []:
            delar.append(del_)
            stig = "/".join(delar)
            if stig and stig not in sedda:
                sedda.add(stig)
                mappar.append(stig)

    rader = [f'-mkdir "{posixpath.join(konfig["mapp"], m)}"' for m in mappar]
    rader += [f'put "{lokal}" "{posixpath.join(konfig["mapp"], relativ)}"'
              for lokal, relativ in filer]
    rader.append("bye")

    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".sftp", delete=False) as f:
        f.write("\n".join(rader) + "\n")
        batchfil = Path(f.name)

    kommando = ["sftp", "-q"]
    if konfig["losenord"]:
        kommando += _ssh_flaggor()
    else:
        kommando += ["-o", "StrictHostKeyChecking=accept-new"]
    if konfig["port"] != 22:
        kommando += ["-P", str(konfig["port"])]
    kommando += ["-b", str(batchfil), f'{konfig["anvandare"]}@{konfig["host"]}']

    miljo = dict(os.environ)
    if konfig["losenord"]:
        # -e läser lösenordet ur miljön, så att det aldrig syns i processlistan.
        miljo["SSHPASS"] = konfig["losenord"]
        kommando = ["sshpass", "-e"] + kommando

    try:
        klart = subprocess.run(kommando, env=miljo, capture_output=True, text=True, timeout=900)
    finally:
        batchfil.unlink(missing_ok=True)

    if klart.returncode != 0:
        besked = (klart.stderr or klart.stdout or "").strip().splitlines()
        raise RuntimeError("sftp misslyckades: " + (besked[-1] if besked else "okänt fel"))
    return len(filer), 0


def ladda_upp() -> None:
    """Speglar site/ till one.com. Säger tydligt ifrån om uppgifter saknas."""
    konfig = _sftp_konfig()
    filer = samla_filer()
    if not filer:
        logg.warning("Hittade inga filer i %s att ladda upp.", SITE)
        return

    # one.com kör en SSH-proxy (OneSSH-Proxy) som INTE tillhandahåller
    # sftp-subsystemet: både `sftp` och paramikos open_sftp() svarar
    # "Connection closed". Vanliga ssh-kommandon och scp fungerar däremot.
    # Därför går uppladdningen genom tar över ssh — hela site/ i en ström,
    # vilket dessutom är snabbare än en fil i taget. paramiko och sftp finns
    # kvar som reserv för en server som stödjer dem.
    if konfig["losenord"] and shutil.which("sshpass"):
        satt = "tar över ssh"
        skickade, hoppade = _ladda_upp_tar(konfig, filer)
    else:
        try:
            import paramiko  # noqa: F401
            har_paramiko = True
        except ImportError:
            har_paramiko = False

        if har_paramiko:
            satt = "paramiko"
            skickade, hoppade = _ladda_upp_paramiko(konfig, filer)
        else:
            satt = "sftp"
            logg.info("paramiko saknas — använder kommandoradens sftp istället.")
            skickade, hoppade = _ladda_upp_kommandorad(konfig, filer)

    logg.info("Laddade upp %d filer till %s:%s med %s%s.",
              skickade, konfig["host"], konfig["mapp"], satt,
              f" (hoppade över {hoppade} oförändrade bilder)" if hoppade else "")
