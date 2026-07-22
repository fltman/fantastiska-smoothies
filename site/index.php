<?php

declare(strict_types=1);

/**
 * Startsidan — hjälten och galleriet med alla smoothies.
 *
 * Smakfiltret är vanliga länkar (?smak=krämig) som PHP filtrerar på innan
 * sidan skrivs ut. Det fungerar alltså helt utan JavaScript (CONTRACT §9);
 * app.js får bara göra samma sak snabbare när alla korten redan ligger i
 * dokumentet.
 *
 * Klassnamnen är exakt de i CONTRACT §5. De få inline-stilarna här sätter
 * rutnätsspann, tryckytor och neutrala scentokens — aldrig en smoothiefärg.
 * All färg som betyder något kommer från datan via gradient_stil().
 */

require_once __DIR__ . '/inc/functions.php';

$smoothies = las_smoothies();

/** Gemener som klarar å, ä och ö även på en server utan mbstring. */
$gemener = static fn (string $text): string => function_exists('mb_strtolower')
    ? mb_strtolower($text, 'UTF-8')
    : strtolower($text);

/** Versal på första bokstaven, resten orörd. Samma reserv utan mbstring. */
$versal_forst = static function (string $text): string {
    if ($text === '') {
        return '';
    }
    if (function_exists('mb_substr') && function_exists('mb_strtoupper')) {
        return mb_strtoupper(mb_substr($text, 0, 1, 'UTF-8'), 'UTF-8')
            . mb_substr($text, 1, null, 'UTF-8');
    }
    return ucfirst($text);
};

/* Hur ofta varje smakord förekommer — styr vilka som får plats i filterraden. */
$antal_per_smak = [];
foreach ($smoothies as $en) {
    foreach ($en['smakprofil'] as $ord) {
        $ord = $gemener(trim($ord));
        if ($ord === '') {
            continue;
        }
        $antal_per_smak[$ord] = ($antal_per_smak[$ord] ?? 0) + 1;
    }
}

/* ?smak=… — bara smakord som faktiskt står i datan släpps igenom. Allt annat
   behandlas som om det aldrig skickats, och hela galleriet visas. */
$vald_smak = '';
if (isset($_GET['smak']) && is_string($_GET['smak'])) {
    $kandidat = $gemener(trim($_GET['smak']));
    if (isset($antal_per_smak[$kandidat])) {
        $vald_smak = $kandidat;
    }
}

$visade = $smoothies;
if ($vald_smak !== '') {
    $visade = array_values(array_filter(
        $smoothies,
        static function (array $smoothie) use ($vald_smak, $gemener): bool {
            foreach ($smoothie['smakprofil'] as $ord) {
                if ($gemener(trim($ord)) === $vald_smak) {
                    return true;
                }
            }
            return false;
        }
    ));
}

/* Filterraden: vanligast först, därefter svensk bokstavsordning. */
$svensk_nyckel = static fn (string $ord): string
    => strtr($ord, ['å' => 'z1', 'ä' => 'z2', 'ö' => 'z3', 'é' => 'e', 'ü' => 'u']);

$smakorden = array_keys($antal_per_smak);
usort(
    $smakorden,
    static fn (string $a, string $b): int
        => ($antal_per_smak[$b] <=> $antal_per_smak[$a])
            ?: strcmp($svensk_nyckel($a), $svensk_nyckel($b))
);

/* Fem piller plus "alla" ryms på två rader vid 360 px — åtta blev tre rader
   och sköt ner första kortet under andra skärmen (ART-DIRECTION §9.1). Är det
   valda ordet ovanligt nog att hamna utanför listan får det ändå plats, först. */
$filterorden = array_slice($smakorden, 0, 5);
if ($vald_smak !== '' && !in_array($vald_smak, $filterorden, true)) {
    array_unshift($filterorden, $vald_smak);
}

/* Formen på pillren kommer från a.smak-etikett i style.css. Kvar här står bara
   det som stilmallen inte känner till, och varje rad har sitt skäl:

   - Radens flex och punktfria lista: <ul> har ingen klass, så resetens
     ul[class]-regel når den inte.
   - --rand-etikett: utanför ett .kort gäller :root-reserven, och den är nästan
     osynlig. Filterlänkarna är kontroller och ska ha en rand som klarar 3:1.
     Det är scenens egen neutral, aldrig en fruktfärg (ART-DIRECTION §1.4).
   - Måtten på pillret: 2,75rem högt och 1rem in på sidorna ger 44 px tryckyta
     (ART-DIRECTION §8.2). style.css lämnar dem med flit till den här filen.
   - Det valda pillret: fyllt i bläck, 16,27:1 mot papper (§1.3). Stilmallen har
     ingen regel för aria-current på en smak-etikett.

   Allt detta hör egentligen hemma i style.css — den filen ägs av någon annan. */
$filterrad = 'display:flex;flex-wrap:wrap;gap:var(--rum-1);list-style:none;'
    . 'padding:0;--rand-etikett:var(--ram-stark)';

$piller = 'min-block-size:2.75rem;padding-inline:1rem';
$piller_valt = $piller . ';background:var(--blck);color:var(--papper);border-color:var(--blck)';

$antal_visade = count($visade);
$antalsord = $antal_visade === 1 ? 'en smoothie' : $antal_visade . ' smoothies';

/* Smakorden i datan är nästan alltid adjektiv (krämig, tvär, sammetslen), så
   de kan aldrig bära bestämd form som ett substantiv — "Smaken krämig" är inte
   svenska. Ordet får därför stå för sig själv i rubriken och efter kolon respektive
   "smakprofilen" i huvudet, vilket bär både adjektiven och de få substantiven
   (blåbär, kokos, lakrits). */
if ($vald_smak !== '') {
    $galleritext  = $versal_forst($vald_smak) . ' · ' . $antalsord;
    $sidtitel     = 'Smak: ' . $vald_smak;
    $sidbeskrivning = $versal_forst($antalsord) . ' med smakprofilen ' . $vald_smak
        . ' — recept, bild och allt som ska i mixern.';
} else {
    $galleritext = 'Alla smoothies · Nyast först';
}

$aktiv_sida = 'index';

require __DIR__ . '/inc/header.php';
?>

<section class="hero bredd"<?= $smoothies !== [] ? ' ' . gradient_stil($smoothies[0]) : '' ?>>
<?php if ($smoothies !== []): ?>
  <div class="hero__blobbar" aria-hidden="true">
<?php foreach (array_slice($smoothies, 0, 3) as $blobb): ?>
    <span class="blobb" <?= gradient_stil($blobb) ?>></span>
<?php endforeach; ?>
  </div>
<?php endif; ?>

  <h1 class="hero__titel"><?= h(SAJT_NAMN) ?></h1>
  <!-- Kort med flit: fem rader ingress vid 360 px sköt ner galleriet under andra
       skärmen. Inbjudan att önska står i knappen nedanför och behöver inte sägas
       två gånger. -->
  <p class="hero__ingress">Kalla, tjocka glas i solmogna färger — mango, blåbär, kokos.
    Nya recept dyker upp här av sig själva.</p>
  <a class="knapp knapp--stor hero__knapp" href="<?= h(bas('/onska')) ?>">Önska en egen smoothie</a>

<?php
/* Senaste glaset står bredvid rubriken från 64rem och är display:none under
   det. En <img> hämtas annars oavsett om den ritas ut, så lat inladdning står
   kvar: den väntar på att elementet ska närma sig vyn, och ett element utan
   layoutruta gör aldrig det. Mobilen hämtar alltså aldrig bilden.
   Från 64rem är den däremot sidans största bild och rimligen det som mäts som
   LCP — därför hög hämtningsprioritet så snart den väl efterfrågas. */
if ($smoothies !== [] && bild_url($smoothies[0]) !== ''):
    $senaste = $smoothies[0];
?>
  <a class="hero__glas" href="<?= h(url_for($senaste['id'])) ?>" <?= gradient_stil($senaste) ?>>
    <img src="<?= h(bild_url($senaste)) ?>" alt="<?= h($senaste['bild_alt']) ?>"
         width="1024" height="1024" loading="lazy" fetchpriority="high" decoding="async">
    <span class="hero__glas-namn"><?= h($senaste['namn']) ?></span>
  </a>
<?php endif; ?>
</section>

<section class="galleri bredd" aria-labelledby="galleri-rubrik"<?= $visade !== [] ? ' ' . gradient_stil($visade[0]) : '' ?>>
  <h2 class="galleri__rubrik" id="galleri-rubrik"><?= h($galleritext) ?></h2>

<?php if ($filterorden !== []): ?>
  <nav aria-label="Filtrera på smak" style="grid-column:1/-1">
    <ul style="<?= h($filterrad) ?>">
      <li><a class="smak-etikett" href="<?= h(bas('/')) ?>" style="<?= h($vald_smak === '' ? $piller_valt : $piller) ?>"<?= $vald_smak === '' ? ' aria-current="true"' : '' ?>>alla</a></li>
<?php foreach ($filterorden as $ord): ?>
      <li><a class="smak-etikett" href="<?= h(bas('/') . '?smak=' . rawurlencode($ord)) ?>" style="<?= h($ord === $vald_smak ? $piller_valt : $piller) ?>"<?= $ord === $vald_smak ? ' aria-current="true"' : '' ?>><?= h($ord) ?></a></li>
<?php endforeach; ?>
    </ul>
  </nav>
<?php endif; ?>

<?php if ($visade === []): ?>
  <p style="grid-column:1/-1">Här står mixern still just nu. Titta in om en stund — eller
    <a href="<?= h(bas('/onska')) ?>">önska den första smoothien</a>.</p>
<?php else: ?>
<?php foreach ($visade as $kort_index => $smoothie): ?>
<?php include __DIR__ . '/inc/smoothie-kort.php'; ?>
<?php endforeach; ?>
<?php endif; ?>
</section>

<?php require __DIR__ . '/inc/footer.php'; ?>
