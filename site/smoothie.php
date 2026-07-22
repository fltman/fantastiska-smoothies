<?php

declare(strict_types=1);

/**
 * En smoothie — /smoothie/{id}, eller smoothie.php?id={id} utan snygga URL:er.
 *
 * Finns inte id:t svarar sidan 404 och lämnar över till 404.php. Sidans hela
 * stämning kommer ur smoothiens egna --start/--slut, som sätts inline på
 * <article class="smoothie"> (ART-DIRECTION §1.4). CSS hårdkodar aldrig en
 * smoothiefärg, och den här sidan skickar aldrig in någon annan.
 */

require_once __DIR__ . '/inc/functions.php';

$id = (isset($_GET['id']) && is_string($_GET['id'])) ? trim($_GET['id']) : '';
$smoothie = $id !== '' ? hitta_smoothie($id) : null;

if ($smoothie === null) {
    http_response_code(404);
    require __DIR__ . '/404.php';
    exit;
}

$portionstext = $smoothie['portioner'] === 1
    ? '1 portion'
    : $smoothie['portioner'] . ' portioner';
$tidstext = $smoothie['tid_minuter'] === 1
    ? '1 minut'
    : $smoothie['tid_minuter'] . ' minuter';

/* Bara förnamnet publiceras, aldrig något mer än det första ordet (CONTRACT §7). */
$onskad_av = is_string($smoothie['onskad_av']) ? trim($smoothie['onskad_av']) : '';
if ($onskad_av !== '') {
    $onskad_av = (string) strtok($onskad_av, " \t\n");
}
$onskemal = is_string($smoothie['onskemal']) ? $smoothie['onskemal'] : '';

$grannarna = grannar($smoothie['id']);
$forra = $grannarna['forra'];
$nasta = $grannarna['nasta'];
/* Står bara en granne kvar hamnar den i första spalten, och då ska texten
   börja där också — CSS högerställer annars sista länken i raden. */
$ensam_granne = ($forra === null) !== ($nasta === null);
$granne_ensam_stil = $ensam_granne ? ' style="text-align:start"' : '';

/* Beskrivningen kan vara ett eller flera stycken. Tomma rader skiljer dem åt. */
$stycken = array_values(array_filter(
    preg_split('/\R\s*\R/', $smoothie['beskrivning']) ?: [],
    static fn (string $stycke): bool => trim($stycke) !== ''
));

$sidtitel = $smoothie['namn'];
$sidbeskrivning = $smoothie['underrubrik'] !== ''
    ? $smoothie['underrubrik']
    : ($stycken !== [] ? $stycken[0] : smakprofil_text($smoothie));
$sidurl = 'smoothie/' . rawurlencode($smoothie['id']);
$sidbild = $smoothie['bild'];
$sidbild_alt = $smoothie['bild_alt'];
$aktiv_sida = 'index';

require __DIR__ . '/inc/header.php';
?>

<article class="smoothie bredd" <?= gradient_stil($smoothie) ?>>
  <div class="smoothie__topp">
<?php if (bild_url($smoothie) !== ''): ?>
    <img class="smoothie__bild" src="<?= h(bild_url($smoothie)) ?>" alt="<?= h($smoothie['bild_alt']) ?>"
         width="1024" height="1024" decoding="async" fetchpriority="high">
<?php endif; ?>
    <div>
      <h1 class="smoothie__titel"><?= h($smoothie['namn']) ?></h1>
<?php if ($smoothie['underrubrik'] !== ''): ?>
      <p class="smoothie__underrubrik"><?= h($smoothie['underrubrik']) ?></p>
<?php endif; ?>

<?php if ($stycken !== []): ?>
      <div class="smoothie__beskrivning">
<?php foreach ($stycken as $stycke): ?>
        <p><?= h(trim($stycke)) ?></p>
<?php endforeach; ?>
      </div>
<?php endif; ?>

      <ul class="smoothie__meta">
<?php foreach ($smoothie['smakprofil'] as $ord): ?>
        <li class="smak-etikett"><?= h($ord) ?></li>
<?php endforeach; ?>
        <li class="meta-post"><?= h($portionstext) ?></li>
        <li class="meta-post"><?= h($tidstext) ?></li>
<?php if ($smoothie['publicerad_text'] !== ''): ?>
        <li class="meta-post"><time datetime="<?= h($smoothie['publicerad']) ?>"><?= h($smoothie['publicerad_text']) ?></time></li>
<?php endif; ?>
      </ul>

<?php if ($onskad_av !== '' && $onskemal !== ''): ?>
      <figure class="onskeruta">
        <blockquote class="onskeruta__citat"><?= h($onskemal) ?></blockquote>
        <figcaption><p>— <?= h($onskad_av) ?>, i ett mail till brevlådan</p></figcaption>
      </figure>
<?php elseif ($onskad_av !== ''): ?>
      <div class="onskeruta">
        <p><?= h($onskad_av) ?> skrev till brevlådan och bad om ett eget glas. Det här blev det.</p>
      </div>
<?php elseif ($onskemal !== ''): ?>
      <?php /* Citat utan namn: gästen skrev inte under. Orden får stå ändå —
               de är hela anledningen till att glaset finns. */ ?>
      <figure class="onskeruta">
        <blockquote class="onskeruta__citat"><?= h($onskemal) ?></blockquote>
        <figcaption><p>— ur ett mail till brevlådan</p></figcaption>
      </figure>
<?php endif; ?>
    </div>
  </div>

  <div class="recept">
    <section class="recept__kolumn" aria-labelledby="behovs">
      <h2 class="recept__rubrik" id="behovs">Det här behövs</h2>
      <ul class="ingredienslista">
<?php foreach ($smoothie['ingredienser'] as $ingrediens): ?>
        <li class="ingrediens">
<?php if ($ingrediens['mangd'] !== ''): ?>
          <span class="ingrediens__mangd"><?= h($ingrediens['mangd']) ?></span>
<?php endif; ?>
          <span class="ingrediens__vara"><?= h($ingrediens['vara']) ?></span>
<?php if ($ingrediens['not'] !== null): ?>
          <span class="ingrediens__not"><?= h($ingrediens['not']) ?></span>
<?php endif; ?>
        </li>
<?php endforeach; ?>
      </ul>
    </section>

    <section class="recept__kolumn" aria-labelledby="gor-sa-har">
      <h2 class="recept__rubrik" id="gor-sa-har">Gör så här</h2>
      <ol class="stegslista">
<?php foreach ($smoothie['gor_sa_har'] as $steg): ?>
        <li class="steg"><?= h($steg) ?></li>
<?php endforeach; ?>
      </ol>

<?php if ($smoothie['toppa_med'] !== []): ?>
      <h3 class="recept__rubrik">Toppa med</h3>
      <ul class="toppning">
<?php foreach ($smoothie['toppa_med'] as $toppning): ?>
        <li><?= h($toppning) ?></li>
<?php endforeach; ?>
      </ul>
<?php endif; ?>

<?php if ($smoothie['knep'] !== ''): ?>
      <p class="knep"><?= h($smoothie['knep']) ?></p>
<?php endif; ?>
    </section>
  </div>

<?php if ($forra !== null || $nasta !== null): ?>
  <nav class="granne" aria-label="Fler smoothies">
<?php if ($forra !== null): ?>
    <a href="<?= h(url_for($forra['id'])) ?>"<?= $granne_ensam_stil ?>><span class="etikett">Förra</span> <?= h($forra['namn']) ?></a>
<?php endif; ?>
<?php if ($nasta !== null): ?>
    <a href="<?= h(url_for($nasta['id'])) ?>"<?= $granne_ensam_stil ?>><span class="etikett">Nästa</span> <?= h($nasta['namn']) ?></a>
<?php endif; ?>
  </nav>
<?php endif; ?>

  <section class="onska">
    <h2>Vad är du sugen på?</h2>
    <p>Skriv ett par rader om smakerna du längtar efter — en frukt, en doft eller ett
      minne räcker långt. Du får tillbaka ett glas som är blandat bara för dig.</p>
    <a class="knapp knapp--stor" href="<?= h(bas('/onska')) ?>">Önska en egen smoothie</a>
  </section>
</article>

<?php require __DIR__ . '/inc/footer.php'; ?>
