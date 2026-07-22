<?php

declare(strict_types=1);

/**
 * Ett kort i galleriet. Förväntar sig $smoothie i scope — en färdigvaliderad
 * post ur las_smoothies().
 *
 * Valfritt: sätt $kort_index till kortets nollbaserade plats i galleriet före
 * include. De tre första korten laddar då sin bild direkt, resten lat.
 *
 * Markupen följer ART-DIRECTION §10.2. Hela kortet är klickbart genom att
 * .kort__lank breder ut ett ::after över hela .kort — därför ligger länken
 * runt allt utom raden "Önskad av", som står utanför men innanför kortet.
 * Färgen kommer alltid från datan via gradient_stil(); CSS hårdkodar aldrig
 * en smoothiefärg (CONTRACT.md §5).
 */

require_once __DIR__ . '/config.php';
require_once __DIR__ . '/functions.php';

if (!isset($smoothie) || !is_array($smoothie) || !isset($smoothie['id'], $smoothie['namn'])) {
    return;
}

$kort_id = (string) $smoothie['id'];
$kort_namn = (string) $smoothie['namn'];
$kort_underrubrik = is_string($smoothie['underrubrik'] ?? null) ? trim($smoothie['underrubrik']) : '';
$kort_emoji = is_string($smoothie['emoji'] ?? null) ? trim($smoothie['emoji']) : '';
$kort_bild = bild_url($smoothie);
$kort_alt = is_string($smoothie['bild_alt'] ?? null) ? $smoothie['bild_alt'] : '';

$kort_smaker = is_array($smoothie['smakprofil'] ?? null) ? $smoothie['smakprofil'] : [];

/* Bara förnamnet publiceras, aldrig något mer (CONTRACT.md §2b och §7).
   Datan är redan rensad i functions.php — det här är andra låset. */
$kort_onskad_av = is_string($smoothie['onskad_av'] ?? null) ? trim($smoothie['onskad_av']) : '';
if ($kort_onskad_av !== '') {
    $kort_ord = preg_split('/\s+/u', $kort_onskad_av, 2);
    $kort_onskad_av = is_array($kort_ord) ? $kort_ord[0] : '';
}

$kort_klasser = 'kort' . ($kort_onskad_av !== '' ? ' kort--onskad' : '');

/* De tre översta korten syns direkt och ska inte vänta på en lat laddning. */
$kort_ovanfor_vecket = isset($kort_index) && is_int($kort_index) && $kort_index < 3;
$kort_laddning = $kort_ovanfor_vecket ? 'eager' : 'lazy';

/* Länkens tillgängliga namn blir smoothiens namn — inte hela kortets text. */
$kort_rubrik_id = 'kort-' . $kort_id;

?>
<article class="<?= h($kort_klasser) ?>" <?= gradient_stil($smoothie) ?>>
  <a class="kort__lank" href="<?= h(url_for($kort_id)) ?>" aria-labelledby="<?= h($kort_rubrik_id) ?>">
    <div class="kort__bildruta">
<?php if ($kort_bild !== ''): ?>
      <img class="kort__bild"
           src="<?= h($kort_bild) ?>"
           alt="<?= h($kort_alt) ?>"
           width="1024" height="1024"
           loading="<?= h($kort_laddning) ?>" decoding="async">
<?php endif; ?>
<?php if ($kort_emoji !== ''): ?>
      <span class="kort__emoji" aria-hidden="true"><?= h($kort_emoji) ?></span>
<?php endif; ?>
    </div>
    <div class="kort__text">
      <h3 class="kort__namn" id="<?= h($kort_rubrik_id) ?>"><?= h($kort_namn) ?></h3>
<?php if ($kort_underrubrik !== ''): ?>
      <p class="kort__underrubrik"><?= h($kort_underrubrik) ?></p>
<?php endif; ?>
<?php if ($kort_smaker !== []): ?>
      <ul class="kort__profil">
<?php foreach ($kort_smaker as $kort_smak): ?>
        <li class="smak-etikett"><?= h((string) $kort_smak) ?></li>
<?php endforeach; ?>
      </ul>
<?php endif; ?>
    </div>
  </a>
<?php if ($kort_onskad_av !== ''): ?>
  <p class="kort__onskad-av">Önskad av <?= h($kort_onskad_av) ?></p>
<?php endif; ?>
</article>
