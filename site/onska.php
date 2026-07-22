<?php

declare(strict_types=1);

/**
 * Önskesidan — hjärtat i interaktionen.
 *
 * Här finns med flit inget formulär. Kanalen är ett vanligt mail till
 * ONSKE_EPOST (CONTRACT.md §7), och sidan gör bara två saker: förklarar hur det
 * går till och gör det så lätt som möjligt att komma iväg med brevet.
 */

require_once __DIR__ . '/inc/functions.php';

$sidtitel       = 'Önska en egen smoothie';
$sidbeskrivning = 'Skriv ett mail om vad du är sugen på, så står ditt eget glas '
    . 'här bland de andra inom en timme — med namn, recept och bild.';
$sidurl         = 'onska';
$aktiv_sida     = 'onska';

/*
 * Mailmallen. Ämne och brödtext kodas var för sig med rawurlencode: den ger
 * %20 för mellanslag och %0D%0A för radbrytning, vilket är vad en mailto-länk
 * vill ha. urlencode() hade gett plustecken mitt i meningarna.
 */
$mail_amne = 'Jag önskar en smoothie';

$mail_brodtext =
      "Hej!\r\n"
    . "\r\n"
    . "Jag är sugen på något som smakar …\r\n"
    . "\r\n"
    . "Det får gärna påminna om …\r\n"
    . "\r\n"
    . "Hälsningar,\r\n";

$mailto = 'mailto:' . ONSKE_EPOST
    . '?subject=' . rawurlencode($mail_amne)
    . '&body=' . rawurlencode($mail_brodtext);

/* Tre önskemål som inspiration, skrivna som folk faktiskt skriver dem. */
$exempel = [
    'Går det att göra något som smakar som glassen jag åt på semestern när jag var nio? '
        . 'Pistage, tror jag att det var.',
    'Jag vill ha något med rabarber. Syrligt, men inte så att det gör ont i tänderna.',
    'Något mörkt och chokladigt att dricka sent på kvällen när huset har blivit tyst. '
        . 'Gärna med kaffe i.',
];

require __DIR__ . '/inc/header.php';
?>

<section class="onska bredd bredd--text">
  <h1>Önska en egen smoothie</h1>

  <p>Det finns ingen ruta att fylla i här. Du skriver ett vanligt mail och berättar vad
  du är sugen på — en frukt, en färg, ett väder, ett minne — och inom en timme står ditt
  glas här bland de andra, med eget namn, eget recept och en egen bild.</p>

  <ol class="onska__steg">
    <li>Skriv till <a href="<?= h($mailto) ?>"><?= h(ONSKE_EPOST) ?></a> och beskriv vad
    du vill ha. En mening räcker långt. Skriv under med ditt förnamn om du vill att det
    ska stå vem som önskade.</li>

    <li>Brevlådan läses varje timme. Då komponeras din smoothie: ett namn som bär ditt,
    ett recept att göra hemma i köket och en bild som bara är din.</li>

    <li>Du får ett svar i mailen med länken dit. Sedan ligger glaset kvar här, överst,
    tills nästa glas ställer sig framför det.</li>
  </ol>

  <a class="knapp knapp--stor onska__mailknapp" href="<?= h($mailto) ?>">Skriv till <?= h(ONSKE_EPOST) ?></a>

  <p>Knappen öppnar ditt mailprogram med ämnet och en liten mall ifylld. Händer ingenting
  när du trycker, kan du lika gärna skriva själv till <?= h(ONSKE_EPOST) ?>, från vilken
  adress du vill — det är samma brevlåda, och den läses lika ofta.</p>

  <div class="onska__exempel">
    <p class="etikett">Så här kan det låta</p>
<?php foreach ($exempel as $onskemal): ?>
    <p>”<?= h($onskemal) ?>”</p>
<?php endforeach; ?>
  </div>

  <p>Adressen du skriver från används bara för att svara dig. Den publiceras aldrig, syns
  aldrig för någon annan och används aldrig till utskick. Skriver du under med ditt
  förnamn, står det under smoothien — annars står den utan namn.</p>
</section>

<?php require __DIR__ . '/inc/footer.php'; ?>
