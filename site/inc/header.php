<?php

declare(strict_types=1);

/**
 * Sidhuvudet — doctype, <head>, skiplänk, sidhuvudet och början på <main>.
 * footer.php stänger allt som öppnas här.
 *
 * Sidan kan sätta följande variabler FÖRE sin include. Alla är valfria:
 *
 *   $sidtitel        string  titeln före sajtnamnet, t.ex. "Solkatt på kaklet"
 *   $sidbeskrivning  string  meta description och og:description
 *   $sidurl          string  sidans adress, t.ex. "smoothie/solkatt-pa-kaklet"
 *   $sidbild         string  sökväg till delningsbild
 *   $sidbild_alt     string  alt-text till delningsbilden
 *   $aktiv_sida      string  "index" | "onska" | "om" — markerar menyposten.
 *                           Tom sträng betyder att ingen post markeras.
 *
 * Alla egna variabler här heter $huvud_* för att inte krocka med sidans egna.
 * Ingen extern resurs laddas: favikonen är en inline-SVG i en data-URI och
 * stilmallen ligger i sajten (CONTRACT.md §9).
 */

require_once __DIR__ . '/config.php';
require_once __DIR__ . '/functions.php';

/** Första icke-tomma texten bland kandidaterna, annars tom sträng. */
$huvud_forsta = static function (mixed ...$kandidater): string {
    foreach ($kandidater as $kandidat) {
        if (is_string($kandidat) && trim($kandidat) !== '') {
            return trim($kandidat);
        }
    }
    return '';
};

/**
 * Gör en intern sökväg till en absolut adress under SAJT_URL.
 *
 * Sökvägar från bas(), url_for() och bild_url() bär redan BASVAG ("/smoothies"
 * på one.com). SAJT_URL bär samma undermapp, så den plockas bort en gång innan
 * de sätts ihop — annars blir adressen .../smoothies/smoothies/...
 */
$huvud_absolut = static function (string $vag): string {
    $bas = rtrim(SAJT_URL, '/');
    if ($vag === '') {
        return $bas . '/';
    }
    if (preg_match('~^https?://~i', $vag) === 1) {
        return $vag;
    }

    $stig = '/' . ltrim($vag, '/');
    if (BASVAG !== '' && ($stig === BASVAG || str_starts_with($stig, BASVAG . '/'))) {
        $stig = substr($stig, strlen(BASVAG));
    }

    return $stig === '' ? $bas . '/' : $bas . $stig;
};

$huvud_sidtitel = $huvud_forsta($sidtitel ?? null);
$huvud_titel = $huvud_sidtitel !== ''
    ? $huvud_sidtitel . ' · ' . SAJT_NAMN
    : SAJT_NAMN;

$huvud_beskrivning = $huvud_forsta($sidbeskrivning ?? null);
if ($huvud_beskrivning === '') {
    $huvud_beskrivning = SAJT_BESKRIVNING;
}

$huvud_kanonisk = $huvud_absolut($huvud_forsta($sidurl ?? null));

/* Delningsbild: sidans egen om den har en, annars den nyaste smoothiens glas —
   så att varje delad länk får med sig en färg i stället för en tom ruta. */
$huvud_bild = $huvud_forsta($sidbild ?? null);
$huvud_bild_alt = $huvud_forsta($sidbild_alt ?? null);
if ($huvud_bild === '') {
    $huvud_senaste = las_smoothies()[0] ?? null;
    if (is_array($huvud_senaste)) {
        $huvud_bild = bild_url($huvud_senaste);
        $huvud_bild_alt = $huvud_forsta($huvud_senaste['bild_alt'] ?? null);
    }
}
if ($huvud_bild !== '') {
    $huvud_bild = $huvud_absolut($huvud_bild);
}

/* Sätter sidan $aktiv_sida gäller det, även när den är tom — då markeras ingen
   post, vilket är vad 404-sidan vill. Först när variabeln saknas helt gissar vi
   på filnamnet. */
$huvud_aktiv = (isset($aktiv_sida) && is_string($aktiv_sida))
    ? trim($aktiv_sida)
    : basename((string) ($_SERVER['SCRIPT_NAME'] ?? ''), '.php');

/* En felsida ska inte hamna i sökresultaten, men i övrigt se ut som sajten. */
$huvud_svarskod = http_response_code();
$huvud_ar_fel = is_int($huvud_svarskod) && $huvud_svarskod >= 400;

$huvud_meny = [
    ['nyckel' => 'index', 'vag' => '/',      'text' => 'Smoothies'],
    ['nyckel' => 'onska', 'vag' => '/onska', 'text' => 'Önska'],
    ['nyckel' => 'om',    'vag' => '/om',    'text' => 'Om'],
];

/* Favikonen: ett tappat glas med gyllene smoothie, ett rosa sugrör på svaj och
   ett litet leende. Ritad för hand, inbakad som data-URI — ingen extra
   förfrågan och ingen fil att glömma ladda upp. */
$huvud_favikon_svg =
      '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">'
    . '<title>Fantastiska smoothies</title>'
    . '<defs><linearGradient id="g" x1="0" y1="0" x2="0" y2="1">'
    . '<stop offset="0" stop-color="#FFC53D"/>'
    . '<stop offset="1" stop-color="#F4623A"/>'
    . '</linearGradient></defs>'
    . '<rect width="32" height="32" rx="7" fill="#FFF9F2"/>'
    . '<rect x="18.3" y="2.2" width="3" height="10.6" rx="1.5" fill="#E0577E"'
    . ' transform="rotate(16 19.8 7.5)"/>'
    . '<path d="M8.6 8.4h14.8l-1.5 16.3a3.4 3.4 0 0 1-3.4 3.1h-5'
    . 'a3.4 3.4 0 0 1-3.4-3.1z" fill="url(#g)"/>'
    . '<circle cx="13.3" cy="17.2" r="1.35" fill="#241A16"/>'
    . '<circle cx="18.7" cy="17.2" r="1.35" fill="#241A16"/>'
    . '<path d="M12.7 20.5q3.3 3.4 6.6 0" fill="none" stroke="#241A16"'
    . ' stroke-width="1.8" stroke-linecap="round"/>'
    . '</svg>';

$huvud_favikon = 'data:image/svg+xml,' . rawurlencode($huvud_favikon_svg);

?><!doctype html>
<html lang="sv">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title><?= h($huvud_titel) ?></title>
<meta name="description" content="<?= h($huvud_beskrivning) ?>">
<?php if (!$huvud_ar_fel): ?>
<link rel="canonical" href="<?= h($huvud_kanonisk) ?>">
<?php endif; ?>
<?php if ($huvud_ar_fel): ?>
<meta name="robots" content="noindex, follow">
<?php endif; ?>

<meta name="color-scheme" content="light dark">
<meta name="theme-color" content="#FFF9F2" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#17110F" media="(prefers-color-scheme: dark)">
<link rel="icon" type="image/svg+xml" href="<?= h($huvud_favikon) ?>">

<meta property="og:type" content="website">
<meta property="og:site_name" content="<?= h(SAJT_NAMN) ?>">
<meta property="og:locale" content="sv_SE">
<meta property="og:title" content="<?= h($huvud_titel) ?>">
<meta property="og:description" content="<?= h($huvud_beskrivning) ?>">
<meta property="og:url" content="<?= h($huvud_kanonisk) ?>">
<?php if ($huvud_bild !== ''): ?>
<meta property="og:image" content="<?= h($huvud_bild) ?>">
<meta property="og:image:type" content="image/webp">
<meta property="og:image:width" content="1024">
<meta property="og:image:height" content="1024">
<?php if ($huvud_bild_alt !== ''): ?>
<meta property="og:image:alt" content="<?= h($huvud_bild_alt) ?>">
<?php endif; ?>
<meta name="twitter:card" content="summary_large_image">
<?php else: ?>
<meta name="twitter:card" content="summary">
<?php endif; ?>

<link rel="stylesheet" href="<?= h(tillgang_url('/assets/css/style.css')) ?>">
</head>
<body<?= isset($sidgradient) && $sidgradient !== '' ? ' ' . $sidgradient : '' ?>>
<div class="omslag">

<a class="hopp-till-innehall" href="#innehall">Hoppa till innehållet</a>

<header class="sidhuvud">
  <div class="bredd">
    <a class="sidhuvud__logga" href="<?= h(bas('/')) ?>"><span aria-hidden="true">🥤</span> <?= h(SAJT_NAMN) ?></a>
    <nav aria-label="Huvudmeny">
      <ul class="sidhuvud__meny">
<?php foreach ($huvud_meny as $huvud_post): ?>
        <li><a href="<?= h(bas($huvud_post['vag'])) ?>"<?= $huvud_post['nyckel'] === $huvud_aktiv ? ' aria-current="page"' : '' ?>><?= h($huvud_post['text']) ?></a></li>
<?php endforeach; ?>
      </ul>
    </nav>
  </div>
</header>

<main id="innehall">
