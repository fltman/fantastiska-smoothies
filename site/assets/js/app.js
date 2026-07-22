/* Fantastiska smoothies — app.js
 *
 * Ren glädje ovanpå en sajt som redan fungerar utan skript. Filterraden är
 * vanliga länkar och galleriet är färdigrenderat av PHP; saknas något i DOM:en
 * gör den här filen ingenting alls och vanliga sidladdningar tar över.
 *
 * Här finns ingen animation och ingen inflygning. Rörelsen bor i CSS, och de
 * fyra signaturgreppen i ART-DIRECTION §6 är alla grepp som finns — inget
 * femte, ingen scrollanimation, ingen IntersectionObserver.
 */
(function () {
  'use strict';

  var galleri = document.querySelector('.galleri');
  if (!galleri) { return; }

  var korten = Array.prototype.slice.call(galleri.querySelectorAll('.kort'));
  if (korten.length === 0) { return; }

  var gemener = function (text) { return (text || '').trim().toLowerCase(); };

  /* Versal på första bokstaven, resten orörd — samma sak som $versal_forst i
     index.php, och lika noga med å, ä och ö. */
  var versal_forst = function (text) {
    return text === '' ? '' : text.charAt(0).toUpperCase() + text.slice(1);
  };

  /* ---- Smakfiltret ------------------------------------------------------ */

  /* Filterraden är den <nav> i galleriet vars piller är länkar — inuti korten
     är samma etikett ett <li> och rörs aldrig. Vi läser den markup index.php
     faktiskt skriver ut; hittar vi den inte gör vi ingenting alls. */
  var forsta_pillret = galleri.querySelector('nav a.smak-etikett');
  var filterlista = (forsta_pillret && forsta_pillret.closest)
    ? forsta_pillret.closest('nav')
    : null;
  var pillren = filterlista
    ? Array.prototype.slice.call(filterlista.querySelectorAll('a.smak-etikett'))
    : [];

  var rubrik = document.getElementById('galleri-rubrik');
  var hero = document.querySelector('.hero');

  /** Länkens adress, eller null om webbläsaren inte får ihop den. */
  function adress_till(lank) {
    try {
      return new URL(lank.href, location.href);
    } catch (fel) {
      return null;
    }
  }

  /* Adressen filterraden utgår från. Ett piller som pekar någon annanstans
     lämnas åt webbläsaren. */
  var basadress = forsta_pillret ? adress_till(forsta_pillret) : null;
  var filterbas = basadress ? basadress.pathname : null;

  /* Pillrens två utseenden skrivs av PHP och lånas härifrån vid inladdning, så
     att vi aldrig har en egen kopia som kan glida isär från index.php. */
  var stil_valt = null;
  var stil_ovalt = null;
  pillren.forEach(function (lank) {
    var stil = lank.getAttribute('style') || '';
    if (lank.hasAttribute('aria-current')) {
      if (stil_valt === null) { stil_valt = stil; }
    } else if (stil_ovalt === null) {
      stil_ovalt = stil;
    }
  });

  /* Kom besökaren in på en redan filtrerad adress saknas de bortsorterade
     korten i DOM:en. Då rör vi inte länkarna — servern gör jobbet. Detsamma
     gäller om vi inte kunde läsa av hur ett valt respektive ovalt piller ser
     ut: hellre vanlig sidladdning än en filterrad som ljuger. */
  var far_filtrera = filterlista !== null && pillren.length > 1 &&
    filterbas !== null && stil_valt !== null && stil_ovalt !== null &&
    !new URL(location.href).searchParams.has('smak');

  var utrop = null;

  /** Smakordet ett piller pekar på. '' är alla, null betyder "inte vår länk". */
  function smak_i_lank(lank) {
    var adress = adress_till(lank);
    if (!adress || adress.origin !== location.origin ||
        adress.pathname !== filterbas) {
      return null;
    }
    return gemener(adress.searchParams.get('smak') || '');
  }

  /** Smakorden i ett kort, i gemener. */
  function smaker_i(kort) {
    return Array.prototype.map.call(
      kort.querySelectorAll('.kort__profil .smak-etikett'),
      function (etikett) { return gemener(etikett.textContent); }
    );
  }

  /** Visar korten som matchar smaken. Tom sträng betyder alla. */
  function visa(smak) {
    var traffar = 0;
    korten.forEach(function (kort) {
      var med = smak === '' || smaker_i(kort).indexOf(smak) !== -1;
      if (med) { traffar++; }
      kort.hidden = !med;
      kort.style.display = med ? '' : 'none';
    });
    return traffar;
  }

  /** Fyller det valda pillret i bläck, precis som PHP gör vid sidladdning. */
  function markera(smak) {
    pillren.forEach(function (lank) {
      if (smak_i_lank(lank) === smak) {
        lank.setAttribute('style', stil_valt);
        lank.setAttribute('aria-current', 'true');
      } else {
        lank.setAttribute('style', stil_ovalt);
        lank.removeAttribute('aria-current');
      }
    });
  }

  /** Skärmläsarens besked om vad som just hände. */
  function beratta(text) {
    if (!utrop) {
      utrop = document.createElement('p');
      utrop.className = 'visuellt-dold';
      utrop.setAttribute('role', 'status');
      galleri.appendChild(utrop);
    }
    utrop.textContent = text;
  }

  /* Glädjedetaljen: strecket under hero-rubriken tar färg av den smoothie som
     ligger först i urvalet. Ingen ny rörelse och inget femte grepp — bara
     remsan i ART-DIRECTION §6.3 som byter dryck när du byter smak. */
  function farga_om() {
    if (!hero) { return; }
    var forsta = korten.filter(function (kort) { return !kort.hidden; })[0];
    if (!forsta) { return; }
    ['--start', '--slut'].forEach(function (namn) {
      var farg = forsta.style.getPropertyValue(namn).trim();
      if (/^#[0-9A-Fa-f]{6}$/.test(farg)) { hero.style.setProperty(namn, farg); }
    });
  }

  /** Hela filtreringen. Returnerar antalet träffar, 0 = vi klarar det inte. */
  function filtrera(smak) {
    var traffar = visa(smak);
    if (traffar === 0) { visa(''); return 0; }
    /* Exakt samma rubrik som index.php skriver ut vid sidladdning. Smakorden
       är adjektiv (krämig, tvär, sammetslen) och bär ingen bestämd form, så
       ordet står för sig självt med versal — glider den här strängen isär från
       PHP:s, byter rubriken tyst utseende när JS tar över. */
    var antalsord = traffar === 1 ? 'en smoothie' : traffar + ' smoothies';
    var text = smak === ''
      ? 'Alla smoothies · Nyast först'
      : versal_forst(smak) + ' · ' + antalsord;
    if (rubrik) { rubrik.textContent = text; }
    markera(smak);
    farga_om();
    beratta(text);
    return traffar;
  }

  if (far_filtrera) {
    filterlista.addEventListener('click', function (handelse) {
      if (handelse.defaultPrevented || handelse.button !== 0) { return; }
      if (handelse.metaKey || handelse.ctrlKey ||
          handelse.shiftKey || handelse.altKey) { return; }
      var mal = handelse.target;
      var lank = (mal && mal.closest) ? mal.closest('a.smak-etikett') : null;
      if (!lank || lank.target || lank.hasAttribute('download')) { return; }
      var smak = smak_i_lank(lank);
      if (smak === null) { return; }
      if (filtrera(smak) === 0) { return; }  /* låt servern svara i stället */
      handelse.preventDefault();
      history.pushState({ smak: smak }, '', lank.href);
    });

    window.addEventListener('popstate', function () {
      filtrera(gemener(new URL(location.href).searchParams.get('smak') || ''));
    });
  }
})();
