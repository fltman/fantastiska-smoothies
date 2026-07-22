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
 * Mappen serveras från två adresser: underdomänen och bjarby.com/smoothies.
 * Interna länkar sköter sig själva via BASVAG, men den kanoniska adressen
 * måste vara EN — pekar båda på sig själva blir det dubblettinnehåll för
 * sökmotorerna. Underdomänen är den vi valt.
 *
 * Samma adress ska stå i SAJT_URL i generator/.env, annars länkar svarsmailen
 * åt ett annat håll än sajten.
 */
const SAJT_URL = 'https://smoothies.bjarby.com';

/**
 * Sökvägsprefixet sajten ligger under, utan avslutande snedstreck.
 *
 * Tom sträng: sajten bor i webbroten på smoothies.bjarby.com, och .htaccess
 * skickar allt annat dit. Lokalt med «php -S localhost:8199 -t site» gäller
 * samma sak.
 *
 * Detta räknades tidigare ut ur SCRIPT_NAME. Det gick inte: mappen är fysiskt
 * httpd.www/smoothies, och SCRIPT_NAME blir «/om.php» för en direkt filträff
 * men «/smoothies/om.php» för en omskriven adress — på samma värd. Sidor som
 * nåddes via en snygg URL letade därför efter sin CSS under /smoothies/ och
 * hittade den inte. DOCUMENT_ROOT går inte heller att använda: den är identisk
 * (/httpd.www) för både underdomänen och undermappen.
 *
 * Flyttas sajten någon gång tillbaka till en synlig undermapp sätts konstanten
 * till den sökvägen för hand, t.ex. '/smoothies'. Alla interna länkar går
 * genom bas() och tillgang_url() i functions.php och följer med.
 */
if (!defined('BASVAG')) {
    define('BASVAG', '');
}

/** Datamappen på disk. Här ligger smoothies.json och onskemal.json. */
const DATA_MAPP = __DIR__ . '/../data';

/**
 * Bildmappen på disk. Generatorn skriver hit.
 * För en länk till en bild i markup: använd bild_url() i functions.php.
 */
const BILD_MAPP = __DIR__ . '/../assets/bilder';
