<?php

declare(strict_types=1);

/**
 * Gemensamt PHP-API för Fantastiska smoothies.
 *
 * Sajten är LAMP utan databas: all data ligger i site/data/smoothies.json
 * (CONTRACT.md §3). Filen läses en enda gång per anrop och cachas i en statisk
 * variabel.
 *
 * Grundhållning: en trasig post får aldrig ta ner sajten. Saknas filen, går den
 * inte att läsa, eller är den inte giltig JSON, så blir galleriet tomt och
 * vänligt — inte ett felmeddelande. Enskilda poster som inte håller måttet
 * hoppas tyst över.
 *
 * All utdata går genom h() innan den skrivs ut. Enda undantaget är
 * gradient_stil(), som bara släpper igenom värden den själv har kontrollerat
 * mot /^#[0-9a-f]{6}$/i.
 *
 * Inkluderas alltid med require_once — aldrig med require eller include, då
 * deklareras funktionerna om. Filen hämtar in config.php själv, så en sida som
 * behöver konstanterna behöver bara den här raden:
 *
 *     require_once __DIR__ . '/inc/functions.php';
 */

require_once __DIR__ . '/config.php';

/**
 * Reservfärger när datan saknar eller har trasiga hexvärden.
 * Det är scenens egna neutraler ur ART-DIRECTION §1.4 — aldrig en påhittad
 * fruktfärg, så att en trasig post syns som stillsamt grå i stället för att
 * ljuga om vad som finns i glaset.
 */
const RESERVFARG_START = '#E7DACC';
const RESERVFARG_SLUT  = '#9C8779';


/* ------------------------------------------------------------------ utskrift */

/**
 * Escapar text för HTML. Allt som skrivs ut går genom den här.
 */
function h(?string $s): string
{
    return htmlspecialchars($s ?? '', ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
}


/* ---------------------------------------------------------------- inläsning */

/**
 * Läser och validerar smoothies.json. Cachas — filen rörs en gång per anrop.
 *
 * @return array{uppdaterad: string, smoothies: list<array<string, mixed>>}
 */
function intern_data(): array
{
    static $data = null;
    if ($data !== null) {
        return $data;
    }

    // Utgångsläget är den tomma sajten. Varje return nedan lämnar den som den är.
    $data = ['uppdaterad' => '', 'smoothies' => []];

    $fil = DATA_MAPP . '/smoothies.json';
    if (!is_file($fil) || !is_readable($fil)) {
        return $data;
    }

    $ra = file_get_contents($fil);
    if ($ra === false || trim($ra) === '') {
        return $data;
    }

    try {
        $avkodad = json_decode($ra, true, 64, JSON_THROW_ON_ERROR);
    } catch (JsonException) {
        return $data;
    }
    if (!is_array($avkodad)) {
        return $data;
    }

    $lista = [];
    $sedda = [];
    foreach ((array) ($avkodad['smoothies'] ?? []) as $rad) {
        $smoothie = intern_validera($rad);
        if ($smoothie === null) {
            continue;
        }
        // Dubbletter av samma id: den första vinner, resten hoppas över.
        if (isset($sedda[$smoothie['id']])) {
            continue;
        }
        $sedda[$smoothie['id']] = true;
        $lista[] = $smoothie;
    }

    // Nyast först, oavsett vilken ordning filen råkar ha. Poster utan giltigt
    // datum hamnar sist. Sorteringen är stabil i PHP 8, så inbördes ordning
    // från filen bevaras vid lika datum.
    usort($lista, static fn (array $a, array $b): int => strcmp(
        (string) $b['publicerad'],
        (string) $a['publicerad']
    ));

    // Tidsstämpeln ska se ut som ett datum, annars låtsas vi inte om den. Ett
    // tal eller en tom sträng i filen ska inte kunna hamna i en sidfot.
    $uppdaterad = intern_text($avkodad['uppdaterad'] ?? null);
    if (preg_match('/^\d{4}-\d{2}-\d{2}/', $uppdaterad) !== 1) {
        $uppdaterad = '';
    }

    $data = [
        'uppdaterad' => $uppdaterad,
        'smoothies'  => $lista,
    ];

    return $data;
}

/**
 * Alla smoothies, nyast först, färdigvaliderade.
 *
 * @return list<array<string, mixed>>
 */
function las_smoothies(): array
{
    return intern_data()['smoothies'];
}

/**
 * Antalet publicerade smoothies.
 */
function antal_smoothies(): int
{
    return count(las_smoothies());
}

/**
 * Tidpunkten datan senast uppdaterades, som ISO-sträng ur smoothies.json.
 * Tom sträng om den inte går att läsa. Sidfoten visar den via datum_text().
 */
function senast_uppdaterad(): string
{
    return intern_data()['uppdaterad'];
}

/**
 * Hämtar en smoothie på id. Null om den inte finns.
 *
 * @return array<string, mixed>|null
 */
function hitta_smoothie(string $id): ?array
{
    $id = trim($id);
    if ($id === '') {
        return null;
    }
    foreach (las_smoothies() as $smoothie) {
        if ($smoothie['id'] === $id) {
            return $smoothie;
        }
    }
    return null;
}

/**
 * Grannarna i galleriets ordning: 'forra' är kortet före (den nyare),
 * 'nasta' är kortet efter (den äldre). Saknas en granne är den null.
 *
 * @return array{forra: array<string, mixed>|null, nasta: array<string, mixed>|null}
 */
function grannar(string $id): array
{
    $lista = las_smoothies();
    foreach ($lista as $i => $smoothie) {
        if ($smoothie['id'] === $id) {
            return [
                'forra' => $lista[$i - 1] ?? null,
                'nasta' => $lista[$i + 1] ?? null,
            ];
        }
    }
    return ['forra' => null, 'nasta' => null];
}


/* -------------------------------------------------------------------- länkar */

/**
 * Länken till en smoothiesida. Snygg URL enligt .htaccess: /smoothie/{id}.
 */
/**
 * Bygger en intern länk som fungerar oavsett om sajten ligger i webbroten
 * eller i en undermapp. $vag ska börja med snedstreck: bas('/onska').
 */
function bas(string $vag): string
{
    return BASVAG . $vag;
}

function url_for(string $id): string
{
    return BASVAG . '/smoothie/' . rawurlencode(trim($id));
}

/**
 * Länken till en smoothies bild. Sökvägen härleds alltid ur id:t, precis som
 * generatorn gör (CONTRACT.md §3) — då kan inget i datan peka någon annanstans.
 *
 * @param array<string, mixed> $s
 */
function bild_url(array $s): string
{
    $id = intern_text($s['id'] ?? null);
    if ($id === '' || preg_match('/^[a-z0-9]+(?:-[a-z0-9]+)*$/', $id) !== 1) {
        return '';
    }
    return BASVAG . '/assets/bilder/' . rawurlencode($id) . '.webp';
}


/* -------------------------------------------------------------------- färger */

/**
 * Släpper bara igenom ett giltigt hexvärde (ART-DIRECTION §1.4). Allt annat ger
 * tom sträng, så att inline-stilen uteblir och CSS-reserven tar över.
 */
function h_farg(?string $hex): string
{
    if ($hex === null) {
        return '';
    }
    $hex = trim($hex);
    return preg_match('/^#[0-9a-f]{6}$/i', $hex) === 1 ? $hex : '';
}

/**
 * Färdig style-attribut med smoothiens två gradientfärger, klar att eka rakt ut:
 *
 *     <article class="kort" <?= gradient_stil($s) ?>>
 *
 * Värdena kontrolleras mot /^#[0-9a-f]{6}$/i först. Ett värde som inte håller
 * byts mot scenens neutrala reservfärg — aldrig mot något ur datan.
 *
 * @param array<string, mixed> $s
 */
function gradient_stil(array $s): string
{
    $farger = is_array($s['farger'] ?? null) ? $s['farger'] : [];

    $start = h_farg(is_string($farger['start'] ?? null) ? $farger['start'] : null);
    $slut  = h_farg(is_string($farger['slut'] ?? null) ? $farger['slut'] : null);

    if ($start === '') {
        $start = RESERVFARG_START;
    }
    if ($slut === '') {
        $slut = RESERVFARG_SLUT;
    }

    return 'style="--start:' . $start . ';--slut:' . $slut . '"';
}


/* ---------------------------------------------------------------------- text */

/**
 * Smakprofilen som en läsbar rad: "tropisk, syrlig och krämig".
 * Tom sträng om profilen saknas.
 *
 * @param array<string, mixed> $s
 */
function smakprofil_text(array $s): string
{
    $ord = [];
    foreach ((array) ($s['smakprofil'] ?? []) as $o) {
        $o = intern_text($o);
        if ($o !== '') {
            $ord[] = $o;
        }
    }

    if ($ord === []) {
        return '';
    }
    if (count($ord) === 1) {
        return $ord[0];
    }

    $sista = array_pop($ord);
    return implode(', ', $ord) . ' och ' . $sista;
}

/**
 * Svenskt datum ur en ISO-sträng: "2026-07-22" → "22 juli 2026".
 * Tål även full ISO-tid med tidszon. Tom sträng om datumet inte går att läsa.
 */
function datum_text(string $iso): string
{
    if (preg_match('/^(\d{4})-(\d{2})-(\d{2})/', trim($iso), $m) !== 1) {
        return '';
    }

    $ar    = (int) $m[1];
    $manad = (int) $m[2];
    $dag   = (int) $m[3];

    if (!checkdate($manad, $dag, $ar)) {
        return '';
    }

    $manader = [
        1 => 'januari', 'februari', 'mars', 'april', 'maj', 'juni',
        'juli', 'augusti', 'september', 'oktober', 'november', 'december',
    ];

    return $dag . ' ' . $manader[$manad] . ' ' . $ar;
}


/* ----------------------------------------------------- validering av en post */

/**
 * Gör en rå JSON-post till en smoothie sajten vågar visa, eller null om den
 * inte går att rädda. Bara id och namn är hårda krav — utan dem finns varken
 * länk eller rubrik. Allt annat får saknas och ersätts av något tyst.
 *
 * @return array<string, mixed>|null
 */
function intern_validera(mixed $rad): ?array
{
    if (!is_array($rad)) {
        return null;
    }

    // id måste vara kebab-case i ren ASCII — det används i både URL och filnamn.
    $id = intern_text($rad['id'] ?? null);
    if ($id === '' || preg_match('/^[a-z0-9]+(?:-[a-z0-9]+)*$/', $id) !== 1) {
        return null;
    }

    $namn = intern_text($rad['namn'] ?? null);
    if ($namn === '') {
        return null;
    }

    // Färgerna: giltigt hexvärde eller tom sträng. Tomt betyder att CSS-reserven
    // får ta över, och att gradient_stil() lägger in sin neutrala färg.
    $rafarger = is_array($rad['farger'] ?? null) ? $rad['farger'] : [];
    $farger = [
        'start' => h_farg(is_string($rafarger['start'] ?? null) ? $rafarger['start'] : null),
        'slut'  => h_farg(is_string($rafarger['slut'] ?? null) ? $rafarger['slut'] : null),
    ];

    // Ingredienser: rader utan vara är meningslösa och hoppas över.
    $ingredienser = [];
    foreach ((array) ($rad['ingredienser'] ?? []) as $post) {
        if (!is_array($post)) {
            continue;
        }
        $vara = intern_text($post['vara'] ?? null);
        if ($vara === '') {
            continue;
        }
        $not = intern_text($post['not'] ?? null);
        $ingredienser[] = [
            'mangd' => intern_text($post['mangd'] ?? null),
            'vara'  => $vara,
            'not'   => $not === '' ? null : $not,
        ];
        if (count($ingredienser) >= 20) {
            break;
        }
    }

    // Förnamnet publiceras, mailadressen aldrig (CONTRACT.md §7). Ett värde som
    // ser ut som något annat än ett förnamn kastas.
    $onskad_av = intern_text($rad['onskad_av'] ?? null);
    if ($onskad_av === ''
        || str_contains($onskad_av, '@')
        || preg_match('/\s/u', $onskad_av) === 1
        || intern_langre_an($onskad_av, 24)
    ) {
        $onskad_av = null;
    }

    // Citatet ur önskemålet: kort, och aldrig med mailadress eller länk i sig.
    $onskemal = intern_kapa(intern_text($rad['onskemal'] ?? null), 140);
    if ($onskemal === ''
        || str_contains($onskemal, '@')
        || stripos($onskemal, 'http') !== false
    ) {
        $onskemal = null;
    }

    // Datumet ska både se rätt ut och finnas på riktigt — datum_text() ger tom
    // sträng för både «2026-13-01» och «2026-02-31».
    $publicerad = intern_text($rad['publicerad'] ?? null);
    $publicerad_text = datum_text($publicerad);
    if ($publicerad_text === '' || preg_match('/^\d{4}-\d{2}-\d{2}$/', $publicerad) !== 1) {
        $publicerad = '';
        $publicerad_text = '';
    }

    return [
        'id'              => $id,
        'namn'            => $namn,
        'underrubrik'     => intern_text($rad['underrubrik'] ?? null),
        'beskrivning'     => intern_text($rad['beskrivning'] ?? null),
        'smakprofil'      => intern_lista($rad['smakprofil'] ?? null, 4),
        'farger'          => $farger,
        'emoji'           => intern_kapa(intern_text($rad['emoji'] ?? null), 8),
        'ingredienser'    => $ingredienser,
        'gor_sa_har'      => intern_lista($rad['gor_sa_har'] ?? null, 8),
        'toppa_med'       => intern_lista($rad['toppa_med'] ?? null, 6),
        'knep'            => intern_text($rad['knep'] ?? null),
        'portioner'       => intern_heltal($rad['portioner'] ?? null, 1),
        'tid_minuter'     => intern_heltal($rad['tid_minuter'] ?? null, 5),
        // Bildsökvägen härleds alltid ur id:t, precis som hos generatorn.
        'bild'            => 'assets/bilder/' . $id . '.webp',
        'bild_alt'        => intern_text($rad['bild_alt'] ?? null),
        'publicerad'      => $publicerad,
        // Färdigt svenskt datum, så att ingen sida behöver formatera själv.
        'publicerad_text' => $publicerad_text,
        'onskad_av'       => $onskad_av,
        'onskemal'        => $onskemal,
    ];
}


/* ------------------------------------------------------------- små hjälpare */

/**
 * Gör ett värde ur JSON till trimmad text. Allt som inte är text eller tal blir
 * tom sträng. Styrtecken plockas bort så att de aldrig kan hamna i markup.
 */
function intern_text(mixed $varde): string
{
    if (is_string($varde)) {
        $text = $varde;
    } elseif (is_int($varde) || is_float($varde)) {
        $text = (string) $varde;
    } else {
        return '';
    }

    $utan_styrtecken = preg_replace('/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/u', '', $text);

    return trim($utan_styrtecken ?? '');
}

/**
 * Gör ett värde ur JSON till en lista med text. Tomma poster faller bort.
 *
 * @return list<string>
 */
function intern_lista(mixed $varde, int $max = 0): array
{
    if (!is_array($varde)) {
        return [];
    }

    $lista = [];
    foreach ($varde as $post) {
        $text = intern_text($post);
        if ($text === '') {
            continue;
        }
        $lista[] = $text;
        if ($max > 0 && count($lista) >= $max) {
            break;
        }
    }

    return $lista;
}

/**
 * Gör ett värde ur JSON till ett positivt heltal, annars reservvärdet.
 */
function intern_heltal(mixed $varde, int $reserv): int
{
    if (is_int($varde) && $varde > 0) {
        return $varde;
    }
    if (is_string($varde) && preg_match('/^\d+$/', trim($varde)) === 1) {
        $tal = (int) trim($varde);
        if ($tal > 0) {
            return $tal;
        }
    }
    return $reserv;
}

/**
 * Kapar text på teckengräns, inte på bytegräns — annars kan ett å, ä eller ö
 * klippas mitt itu och bli en trasig ruta i webbläsaren.
 *
 * Klippningen görs med /u i stället för mb_substr(), så att filen inte hänger
 * på att mbstring finns installerat. Duger texten inte som UTF-8 lämnas den som
 * den är; då har den ändå aldrig kommit hit, för json_decode() hade sagt ifrån.
 */
function intern_kapa(string $text, int $max): string
{
    if ($max <= 0 || $text === '') {
        return $text;
    }
    if (preg_match('/^.{0,' . $max . '}/us', $text, $m) === 1) {
        return rtrim($m[0]);
    }
    return $text;
}

/**
 * Sant om texten är längre än $max tecken (inte bytes).
 */
function intern_langre_an(string $text, int $max): bool
{
    return preg_match('/^.{0,' . $max . '}$/us', $text) !== 1;
}
