<?php

declare(strict_types=1);

/**
 * Sidfoten. Stänger <main> och <div class="omslag"> som header.php öppnade,
 * och avslutar dokumentet.
 *
 * Innehållet är det ART-DIRECTION §5.4 räknar upp: en rad om vad sajten är,
 * vägen vidare till önskesidan, brevlådan som mailto: och när datan senast
 * fylldes på. Inga sociala ikoner, ingen extern resurs.
 *
 * Egna variabler heter $sidfot_* för att inte krocka med sidans egna.
 */

require_once __DIR__ . '/config.php';
require_once __DIR__ . '/functions.php';

/* Tidpunkten kommer i första hand ur datans eget "uppdaterad". Skulle fältet
   saknas får filens ändringstid duga — raden ska aldrig stå halv. */
$sidfot_iso = '';
$sidfot_datum = '';

if (preg_match('/^\d{4}-\d{2}-\d{2}/', senast_uppdaterad(), $sidfot_traff) === 1) {
    $sidfot_iso = $sidfot_traff[0];
    $sidfot_datum = datum_text($sidfot_iso);
}

if ($sidfot_datum === '') {
    $sidfot_fil = rtrim(DATA_MAPP, '/') . '/smoothies.json';
    $sidfot_andrad = is_file($sidfot_fil) ? filemtime($sidfot_fil) : false;
    if ($sidfot_andrad !== false) {
        $sidfot_iso = date('Y-m-d', $sidfot_andrad);
        $sidfot_datum = datum_text($sidfot_iso);
    }
}

$sidfot_antal = antal_smoothies();
$sidfot_antalstext = match (true) {
    $sidfot_antal === 0 => 'Ingen smoothie står framme just nu — den första är på väg.',
    $sidfot_antal === 1 => 'En smoothie står framme just nu.',
    default             => $sidfot_antal . ' smoothies står framme just nu.',
};

?>
</main>

<footer class="sidfot">
  <div class="bredd">
    <p><?= h(SAJT_BESKRIVNING) ?></p>

    <p>Längtar du efter en särskild smak? <a href="<?= h(bas('/onska')) ?>">Önska en egen
    smoothie</a> — eller skriv några rader rakt till
    <a href="mailto:<?= h(ONSKE_EPOST) ?>"><?= h(ONSKE_EPOST) ?></a>, så står ditt glas
    här med eget namn, eget recept och egen bild.</p>

    <p><?= h($sidfot_antalstext) ?><?php if ($sidfot_datum !== ''): ?> Senast påfylld <time datetime="<?= h($sidfot_iso) ?>"><?= h($sidfot_datum) ?></time>.<?php endif; ?></p>
  </div>
</footer>

</div>
<script src="<?= h(tillgang_url('/assets/js/app.js')) ?>" defer></script>
</body>
</html>
