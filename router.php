<?php

declare(strict_types=1);

/**
 * Router för PHP:s inbyggda utvecklingsserver.
 *
 *     php -S localhost:8199 -t site router.php
 *
 * `php -S` läser inte `site/.htaccess`, så utan den här filen finns ingen av
 * sajtens snygga adresser lokalt: `/onska`, `/om` och `/smoothie/{id}` faller
 * alla tillbaka på index.php och svarar 200 med startsidan, och en adress som
 * inte finns gör likadant i stället för att ge 404. Här görs samma
 * omskrivningar som Apache gör skarpt, i samma ordning.
 *
 * Filen ligger i reporoten och aldrig under `site/` — publicera.py speglar bara
 * `site/`, och den här utvecklingshjälpen ska inte upp på webben.
 */

$rot = __DIR__ . '/site';

$vag = parse_url((string) ($_SERVER['REQUEST_URI'] ?? '/'), PHP_URL_PATH);
$vag = is_string($vag) ? rawurldecode($vag) : '/';

/* Skafferiet lämnas inte ut, precis som i .htaccess. */
if (preg_match('#^/(?:data|inc)(?:/|$)#', $vag) === 1) {
    http_response_code(403);
    header('Content-Type: text/plain; charset=UTF-8');
    echo "403 — den mappen är skafferi, inte skyltfönster.\n";

    return true;
}

/* Finns filen på riktigt serverar den inbyggda servern den som den är. */
if ($vag !== '/' && !str_contains($vag, '..') && is_file($rot . $vag)) {
    return false;
}

if (preg_match('#^/smoothie/([a-z0-9-]+)/?$#', $vag, $traff) === 1) {
    $_GET['id'] = $traff[1];
    require $rot . '/smoothie.php';

    return true;
}

if (preg_match('#^/onska/?$#', $vag) === 1) {
    require $rot . '/onska.php';

    return true;
}

if (preg_match('#^/om/?$#', $vag) === 1) {
    require $rot . '/om.php';

    return true;
}

if ($vag === '/') {
    require $rot . '/index.php';

    return true;
}

/* En bild eller en stilmall som saknas ska svara billigt, inte med ett helt
   HTML-dokument i filens ställe. Svaret skrivs här: `return false` hade lämnat
   tillbaka frågan till den inbyggda servern, som då hittar index.php i stället
   och svarar 200 med startsidan. */
if (preg_match('#\.(?:webp|png|jpe?g|gif|svg|ico|css|js|woff2?|map|txt|xml)$#i', $vag) === 1) {
    http_response_code(404);
    header('Content-Type: text/plain; charset=UTF-8');
    echo "404 — filen finns inte.\n";

    return true;
}

require $rot . '/404.php';

return true;
