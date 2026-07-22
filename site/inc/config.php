<?php

declare(strict_types=1);

/**
 * Konstanter för Fantastiska smoothies.
 *
 * Här står bara sådant som får synas i en publik källkod. Inga lösenord, inga
 * API-nycklar, ingen SFTP-uppgift — de bor i generator/.env och lämnar aldrig
 * Anders dator (CONTRACT.md §7).
 *
 * Filen inkluderas normalt via inc/functions.php, som gör det själv.
 */

// Kan inkluderas från flera håll under samma anrop. Är den redan inläst
// lämnar vi den i fred i stället för att deklarera om konstanterna.
if (defined('SAJT_NAMN')) {
    return;
}

/** Sajtens namn — ordmärket i sidhuvudet och i sidtitlarna. */
const SAJT_NAMN = 'Fantastiska smoothies';

/** En rad om vad sajten är. Används i meta-beskrivningen och i sidfoten. */
const SAJT_BESKRIVNING = 'Färgstarka smoothies med recept — och en brevlåda som tar emot önskemål.';

/** Brevlådan som tar emot önskemål. Skrivs ut som mailto: på önskesidan. */
const ONSKE_EPOST = 'smoothies@bjarby.com';

/**
 * Sajtens adress, utan avslutande snedstreck. Används i absoluta länkar —
 * kanonisk adress, og:url och og:image.
 *
 * Underdomänen är den deploy resten av projektet är riggat för (DEPLOY.md 1.1).
 * Tre ställen måste bära samma adress: den här raden, ErrorDocument i
 * site/.htaccess och SAJT_URL i generator/.env — annars länkar sajten och
 * svarsmailet åt olika håll.
 */
const SAJT_URL = 'https://smoothies.bjarby.com';

/**
 * Sökvägsprefixet sajten ligger under, utan avslutande snedstreck.
 *
 * Räknas ut ur SCRIPT_NAME i stället för att hårdkodas, så att exakt samma kod
 * fungerar överallt: lokalt med php -S i roten → '', på underdomänen
 * smoothies.bjarby.com → '' (mappen httpd.www/smoothies är dess webbrot), och
 * i en undermapp som syns i adressen, bjarby.com/smoothies → '/smoothies'.
 *
 * Alla interna länkar går genom bas() i functions.php.
 */
if (!defined('BASVAG')) {
    $skript = $_SERVER['SCRIPT_NAME'] ?? '';
    $skriptmapp = is_string($skript)
        ? rtrim(str_replace('\\', '/', dirname($skript)), '/')
        : '';

    // SCRIPT_NAME kommer från webbservern och tas inte på förtroende: bara en
    // rak sökväg av vanliga tecken duger. Ser den ut på något annat sätt blir
    // basen tom, och sajten länkar till roten i stället för någon annanstans.
    if ($skriptmapp === '.'
        || str_contains($skriptmapp, '..')
        || preg_match('#^(?:/[A-Za-z0-9._-]+)*$#', $skriptmapp) !== 1
    ) {
        $skriptmapp = '';
    }

    define('BASVAG', $skriptmapp);
    unset($skript, $skriptmapp);
}

/** Datamappen på disk. Här ligger smoothies.json och onskemal.json. */
const DATA_MAPP = __DIR__ . '/../data';

/**
 * Bildmappen på disk. Generatorn skriver hit.
 * För en länk till en bild i markup: använd bild_url() i functions.php.
 */
const BILD_MAPP = __DIR__ . '/../assets/bilder';
