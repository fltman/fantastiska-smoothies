<?php

declare(strict_types=1);

/**
 * Om-sidan. Kort och personlig: vad sajten är, hur den tänker och att vem som
 * helst kan önska. Använder .onska som layoutklass — det är klassen för
 * önskesidan och innehållssidorna (ART-DIRECTION §5.5).
 */

require_once __DIR__ . '/inc/functions.php';

$sidtitel       = 'Om sajten';
$sidbeskrivning = 'Smoothies som ska vara fantastiska att dricka, komponerade '
    . 'som en konditor hade gjort det. Vem som helst kan önska.';
$sidurl         = 'om';
$aktiv_sida     = 'om';

$antal = antal_smoothies();
$hyllan = match (true) {
    $antal <= 0 => 'Just nu står hyllan tom, men inte länge till.',
    $antal === 1 => 'Just nu står ett enda glas på hyllan.',
    default => 'Just nu står det ' . $antal . ' glas på hyllan.',
};

require __DIR__ . '/inc/header.php';
?>

<section class="onska bredd bredd--text">
  <h1>Om <?= h(SAJT_NAMN) ?></h1>

  <p>Det här är precis vad det låter som: smoothies som ska vara fantastiska att dricka.
  Inget annat får komma före det.</p>

  <p>Recepten är komponerade som en konditor hade gjort det. Först en tanke om smak, sedan
  en om textur, sedan en om färg — och därefter lite envishet tills de tre hänger ihop.
  Grädden är där för att den gör drycken sammetslen. Kardemumman för att den doftar långt
  innan man hinner smaka. Saltet för att sista klunken ska bli skarpare än den första.</p>

  <p>Vem som helst kan önska. Du skriver ett par rader om vad du är sugen på, och inom en
  timme står ditt glas här med eget namn, eget recept och egen bild. <?= h($hyllan) ?></p>

  <p>Bilderna är AI-genererade. Det finns ingen fotostudio bakom sajten — bara samma
  beskrivning som receptet fick, översatt till ljus, glas och en bakgrundsfärg som rimmar
  med drycken.</p>

  <p>I övrigt sköter sajten sig själv. Brevlådan läses varje timme, och har ingen önskat
  något på ett dygn brygger huset en egen.</p>

  <p><a class="knapp" href="<?= h(bas('/onska')) ?>">Önska en egen smoothie</a></p>
</section>

<?php require __DIR__ . '/inc/footer.php'; ?>
