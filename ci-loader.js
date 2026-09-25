(function () {
  const CDN_BASE_URL = 'https://ci-icons.vercel.app/';
  const STORAGE_PREFIX = 'ci_icon_';
  const VERSION_PREFIX = 'ci_ver_';

  // STEP 1: INSTANT PAINT (Offline-First)
  function applyInstantPaint() {
    const icons = document.querySelectorAll('.ci');
    let cssRules = '';

    icons.forEach(el => {
      el.classList.forEach(cls => {
        if (cls.startsWith('ci-') && cls !== 'ci') {
          const iconName = cls.replace('ci-', '');
          const cachedSvg = localStorage.getItem(STORAGE_PREFIX + iconName);
          if (cachedSvg) {
            cssRules += `.${cls} { -webkit-mask-image: url("data:image/svg+xml;utf8,${cachedSvg}") !important; mask-image: url("data:image/svg+xml;utf8,${cachedSvg}") !important; }\n`;
          }
        }
      });
    });

    if (cssRules) {
      let styleTag = document.getElementById('ci-instant-styles');
      if (!styleTag) {
        styleTag = document.createElement('style');
        styleTag.id = 'ci-instant-styles';
        document.head.appendChild(styleTag);
      }
      styleTag.textContent = cssRules;
    }
  }

  applyInstantPaint();

  // STEP 2: GRANULAR NON-BLOCKING BACKGROUND SYNC
  async function granularSync() {
    if (!navigator.onLine) return;

    try {
      const icons = document.querySelectorAll('.ci');
      const usedIconNames = new Set();
      icons.forEach(el => {
        el.classList.forEach(cls => {
          if (cls.startsWith('ci-') && cls !== 'ci') {
            usedIconNames.add(cls.replace('ci-', ''));
          }
        });
      });

      if (usedIconNames.size === 0) return;

      const res = await fetch(`${CDN_BASE_URL}svgs/svgs.json`);
      if (!res.ok) return;
      const iconsMap = await res.json();

      let updated = false;

      for (const name of usedIconNames) {
        if (!iconsMap[name]) continue;
        const remoteData = iconsMap[name];
        const remoteVer = remoteData.version || '1.0.0';
        const localVer = localStorage.getItem(VERSION_PREFIX + name);
        const hasData = localStorage.getItem(STORAGE_PREFIX + name);

        if (!hasData || remoteVer !== localVer) {
          let svgMarkup = remoteData.svg;

          // If svg property is a URL/path instead of markup, fetch it
          if (svgMarkup && !svgMarkup.trim().startsWith('<svg')) {
            try {
              const svgRes = await fetch(svgMarkup);
              if (svgRes.ok) svgMarkup = await svgRes.text();
            } catch (e) {
              continue;
            }
          }

          if (svgMarkup) {
            const encoded = encodeURIComponent(svgMarkup.trim());
            localStorage.setItem(STORAGE_PREFIX + name, encoded);
            localStorage.setItem(VERSION_PREFIX + name, remoteVer);
            updated = true;
          }
        }
      }

      if (updated) {
        applyInstantPaint();
      }
    } catch (error) {
      console.warn('Background sync skipped. Running on cache.', error);
    }
  }

  if ('requestIdleCallback' in window) {
    requestIdleCallback(() => granularSync());
  } else {
    window.addEventListener('load', () => setTimeout(granularSync, 1200));
  }
})();
