(function () {
  const CDN_BASE_URL = 'https://ci-icons.vercel.app/';
  const STORAGE_PREFIX = 'ci_icon_';
  const VERSION_PREFIX = 'ci_ver_';

  // 1. INSTANT PAINT (Offline-First)
  // Renders cached icons immediately from localStorage with zero latency.
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

  // Execute instant paint on script parse
  applyInstantPaint();

  // 2. GRANULAR BACKGROUND SYNC
  // Checks only the icons present on the current page against svgs.json metadata.
  async function granularSync() {
    if (!navigator.onLine) return; // Exit gracefully if offline

    try {
      // Find unique icon names currently used in DOM
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

      // Fetch lightweight metadata index (svgs.json)
      const res = await fetch(`${CDN_BASE_URL}svgs/svgs.json`);
      if (!res.ok) return;
      const data = await res.json();
      
      // Create a lookup map for remote versions
      const remoteVersions = {};
      data.icons.forEach(item => {
        remoteVersions[item.name] = item.version;
      });

      // Determine which specific icons are missing or have outdated versions
      const iconsToUpdate = [];
      usedIconNames.forEach(name => {
        const remoteVer = remoteVersions[name] || 1;
        const localVer = parseInt(localStorage.getItem(VERSION_PREFIX + name) || '0', 10);
        const hasData = localStorage.getItem(STORAGE_PREFIX + name);

        if (!hasData || remoteVer > localVer) {
          iconsToUpdate.push({ name, version: remoteVer });
        }
      });

      // Fetch and update ONLY the outdated or missing icons concurrently
      if (iconsToUpdate.length > 0) {
        await Promise.all(
          iconsToUpdate.map(async ({ name, version }) => {
            try {
              const svgRes = await fetch(`${CDN_BASE_URL}svgs/${name}.svg`);
              if (svgRes.ok) {
                const svgText = await svgRes.text();
                const encoded = encodeURIComponent(svgText.trim());
                
                // Save granular cache and individual version pointer
                localStorage.setItem(STORAGE_PREFIX + name, encoded);
                localStorage.setItem(VERSION_PREFIX + name, version);
              }
            } catch (err) {
              console.warn(`Failed to update icon: ${name}`, err);
            }
          })
        );

        // Re-apply styles with the newly updated icon data
        applyInstantPaint();
      }
    } catch (error) {
      console.warn('Network sync skipped. Running purely on local cache.', error);
    }
  }

  // Non-blocking execution using requestIdleCallback or fallback
  if ('requestIdleCallback' in window) {
    requestIdleCallback(() => granularSync());
  } else {
    window.addEventListener('load', () => setTimeout(granularSync, 1200));
  }
})();
