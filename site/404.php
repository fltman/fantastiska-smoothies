<?php

declare(strict_types=1);

/**
 * 404 — vänlig och lekfull, i sajtens ton.
 *
 * Filen används på tre sätt och måste klara alla tre:
 *   1. som ErrorDocument 404 från .htaccess,
 *   2. som omskrivningsmål för adresser som inte finns,
 *   3. inkluderad från smoothie.php när id:t inte matchar någon smoothie.
 *
 * Därför sätts statuskoden här och inte bara av Apache. Rubriken är den fasta
 * strängen ur ART-DIRECTION §12.
 */

require_once __DIR__ . '/inc/functions.php';

/* Sätts även när filen anropas direkt. Har Apache redan satt 404 är detta en
   nollåtgärd; anropas den som vanlig sida blir koden ändå rätt. */
http_response_code(404);

$sidtitel       = 'Den smoothien finns inte';
$sidbeskrivning = 'Adressen ledde ingenstans. Här är vägen tillbaka till glasen '
    . 'som faktiskt står framme.';
$aktiv_sida     = '';

/* Ett slumpat tips, så att en felslagen adress ändå leder någonstans gott. */
$tipslista = las_smoothies();
$tips = $tipslista !== [] ? $tipslista[random_int(0, count($tipslista) - 1)] : null;

require __DIR__ . '/inc/header.php';
?>

<section class="onska bredd bredd--text">
  <h1>Den smoothien finns inte. Men de här finns.</h1>

  <p>Antingen tappade adressen en bokstav på vägen hit, eller så har det glaset aldrig
  stått framme. Det gör ingenting — det finns gott om andra att välja på, och de är
  alla kalla.</p>

<?php if ($tips !== null): ?>
  <p class="etikett">Ett tips på vägen</p>
  <p><a href="<?= h(url_for($tips['id'])) ?>"><?= h($tips['namn']) ?></a><?php
    if ($tips['underrubrik'] !== '') {
        echo ' — ' . h($tips['underrubrik']);
    }
  ?></p>
<?php endif; ?>

  <!-- Inline flex bara för att hålla de två knapparna isär: ART-DIRECTION §8.2
       vill ha minst 8 px mellan två tryckytor, och ett radbrytningsmellanrum
       räcker inte. Ingen ny klass behövs för det. -->
  <p style="display:flex;flex-wrap:wrap;gap:var(--rum-2)">
    <a class="knapp" href="<?= h(bas('/') ?: '/') ?>">Till alla smoothies</a>
    <a class="knapp knapp--tyst" href="<?= h(bas('/onska')) ?>">Önska en egen smoothie</a>
  </p>
</section>

<?php require __DIR__ . '/inc/footer.php'; ?>
