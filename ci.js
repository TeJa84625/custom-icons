(function (global) {
  'use strict';

  const SAVE_BASE_PATH = './save/';
  const FALLBACK_ICON_URL = './favicon.svg';

  const memoryCache = new Map();
  const fileCache = new Map();
  const hashMap = new Map();
  let masterIndexData = null;
  let isFetchingIndex = false;
  let fetchQueue = [];
  let fallbackSvgEncoded = null;

  function generate3CharHash(str) {
    let hash = 5381;
    for (let i = 0; i < str.length; i++) {
      hash = (hash * 33) ^ str.charCodeAt(i);
    }
    const chars = '0123456789abcdefghijklmnopqrstuvwxyz';
    let absHash = Math.abs(hash);
    let result = '';
    for (let i = 0; i < 3; i++) {
      result += chars[absHash % chars.length];
      absHash = Math.floor(absHash / chars.length);
    }
    return result;
  }

  function cleanAndEncodeSVG(svgString) {
    if (!svgString) return '';

    let cleanSvg = svgString
      .replace(/stroke="(?!none)[^"]*"/g, 'stroke="currentColor"')
      .replace(/fill="(?!none)[^"]*"/g, 'fill="currentColor"');

    return encodeURIComponent(cleanSvg.trim())
      .replace(/'/g, "%27")
      .replace(/"/g, "%22");
  }

  async function getFallbackEncodedSVG() {
    if (fallbackSvgEncoded) return fallbackSvgEncoded;
    try {
      const res = await fetch(FALLBACK_ICON_URL);
      if (res.ok) {
        const svgText = await res.text();
        fallbackSvgEncoded = cleanAndEncodeSVG(svgText);
        return fallbackSvgEncoded;
      }
    } catch (e) {
      // Ignore fallback fetch errors
    }
    // Minimal fallback data URI if favicon.svg fails to load
    return cleanAndEncodeSVG('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10" fill="currentColor"/></svg>');
  }

  async function ensureIndexLoaded() {
    if (masterIndexData) return;
    if (isFetchingIndex) {
      return new Promise(resolve => {
        fetchQueue.push(resolve);
      });
    }

    isFetchingIndex = true;
    try {
      const res = await fetch(`${SAVE_BASE_PATH}svgs.json`);
      if (res.ok) {
        masterIndexData = await res.json();
        const indexList = masterIndexData.indices || [];

        indexList.forEach(item => {
          const fileTag = item.file.replace('.json', '');
          const hashPrefix = generate3CharHash(`author_cat_${fileTag}`);
          hashMap.set(hashPrefix, item.file);
        });
      } else {
        throw new Error('Index response not ok');
      }
    } catch (error) {
      console.error('Failed to load master index, fallback active', error);
      masterIndexData = { indices: [] }; // Prevent infinite loops
    } finally {
      isFetchingIndex = false;
      while (fetchQueue.length > 0) {
        const callback = fetchQueue.shift();
        callback();
      }
    }
  }

  async function applyInstantPaint() {
    const icons = document.querySelectorAll('.ci');
    if (!icons.length) return;

    try {
      await ensureIndexLoaded();

      let cssRules = '';
      const styleId = 'ci-instant-styles';
      let styleTag = document.getElementById(styleId);

      if (!styleTag) {
        styleTag = document.createElement('style');
        styleTag.id = styleId;
        document.head.appendChild(styleTag);
      }

      const missingIcons = new Set();

      icons.forEach(el => {
        el.classList.forEach(cls => {
          if (cls.startsWith('ci-') && cls !== 'ci' && !isModifierClass(cls)) {
            const iconIdentifier = cls.replace('ci-', '');

            if (memoryCache.has(iconIdentifier)) {
              const encoded = memoryCache.get(iconIdentifier);
              cssRules += `.${cls} { -webkit-mask-image: url("data:image/svg+xml;utf8,${encoded}") !important; mask-image: url("data:image/svg+xml;utf8,${encoded}") !important; }\n`;
            } else {
              missingIcons.add(iconIdentifier);
            }
          }
        });
      });

      if (cssRules && styleTag.textContent !== cssRules) {
        styleTag.textContent = cssRules;
      }

      if (missingIcons.size > 0) {
        await fetchAndProcessIcons(missingIcons);
      }
    } catch (e) {
      console.error('Error during applyInstantPaint, applying fallback', e);
      const fallback = await getFallbackEncodedSVG();
      icons.forEach(el => {
        el.classList.forEach(cls => {
          if (cls.startsWith('ci-') && cls !== 'ci' && !isModifierClass(cls)) {
            const rule = `.${cls} { -webkit-mask-image: url("data:image/svg+xml;utf8,${fallback}") !important; mask-image: url("data:image/svg+xml;utf8,${fallback}") !important; }\n`;
            let styleTag = document.getElementById('ci-instant-styles');
            if (styleTag && !styleTag.textContent.includes(cls)) {
              styleTag.textContent += rule;
            }
          }
        });
      });
    }
  }

  function isModifierClass(cls) {
    return (
      cls.startsWith('ci-xxs') ||
      cls.startsWith('ci-2xs') ||
      cls.startsWith('ci-xs') ||
      cls.startsWith('ci-sm') ||
      cls.startsWith('ci-lg') ||
      cls.startsWith('ci-xl') ||
      cls.startsWith('ci-2xl') ||
      cls.startsWith('ci-3xl') ||
      cls.startsWith('ci-4xl') ||
      cls.startsWith('ci-fw') ||
      cls.startsWith('ci-align-') ||
      cls.startsWith('ci-rotate-') ||
      cls.startsWith('ci-flip-') ||
      cls === 'ci-interactive' ||
      cls === 'ci-disabled' ||
      cls === 'ci-spin' ||
      cls === 'ci-pulse' ||
      cls === 'ci-bounce' ||
      cls === 'ci-beat' ||
      cls === 'ci-fade' ||
      cls === 'ci-shake' ||
      cls === 'ci-flash' ||
      cls === 'ci-float' ||
      cls === 'ci-glow' ||
      cls.startsWith('ci-shadow') ||
      cls.startsWith('ci-primary') ||
      cls.startsWith('ci-secondary') ||
      cls.startsWith('ci-success') ||
      cls.startsWith('ci-danger') ||
      cls.startsWith('ci-warning') ||
      cls.startsWith('ci-info') ||
      cls.startsWith('ci-light') ||
      cls.startsWith('ci-dark') ||
      cls.startsWith('ci-muted') ||
      cls.startsWith('ci-red') ||
      cls.startsWith('ci-blue') ||
      cls.startsWith('ci-green') ||
      cls.startsWith('ci-yellow') ||
      cls.startsWith('ci-purple') ||
      cls.startsWith('ci-pink') ||
      cls.startsWith('ci-indigo') ||
      cls.startsWith('ci-teal') ||
      cls.startsWith('ci-orange')
    );
  }

  async function loadSaveFile(fileName) {
    if (fileCache.has(fileName)) {
      return fileCache.get(fileName);
    }
    try {
      const res = await fetch(`${SAVE_BASE_PATH}${fileName}`);
      if (!res.ok) return null;
      const data = await res.json();
      fileCache.set(fileName, data);
      return data;
    } catch (e) {
      return null;
    }
  }

  async function fetchAndProcessIcons(targetIdentifiers) {
    if (!navigator.onLine) return;
    await ensureIndexLoaded();

    let updated = false;
    const fallbackEncoded = await getFallbackEncodedSVG();

    for (const identifier of targetIdentifiers) {
      if (memoryCache.has(identifier)) continue;

      let found = false;
      try {
        let targetFile = null;
        let iconKey = identifier;

        const dashIndex = identifier.indexOf('-');
        if (dashIndex !== -1) {
          const possibleHash = identifier.substring(0, dashIndex);
          if (hashMap.has(possibleHash)) {
            targetFile = hashMap.get(possibleHash);
            iconKey = identifier.substring(dashIndex + 1);
          }
        }

        const filesToSearch = targetFile
          ? [targetFile]
          : (masterIndexData && masterIndexData.indices ? masterIndexData.indices.map(i => i.file) : []);

        for (const fileName of filesToSearch) {
          const fileContent = await loadSaveFile(fileName);
          if (!fileContent || !fileContent.icons) continue;

          const iconObj = fileContent.icons[iconKey] || fileContent.icons[identifier];
          if (iconObj) {
            let svgMarkup = typeof iconObj === 'object' ? iconObj.svg : iconObj;

            if (svgMarkup && !svgMarkup.trim().startsWith('<svg')) {
              try {
                const svgRes = await fetch(svgMarkup);
                if (svgRes.ok) svgMarkup = await svgRes.text();
              } catch (e) {
                continue;
              }
            }

            if (svgMarkup) {
              const encoded = cleanAndEncodeSVG(svgMarkup);
              memoryCache.set(identifier, encoded);
              found = true;
              updated = true;
              break;
            }
          }
        }
      } catch (err) {
        // Error handling per icon lookup
      }

      // If any error occurred or icon was not found in files, default to fallback (favicon.svg)
      if (!found) {
        memoryCache.set(identifier, fallbackEncoded);
        updated = true;
      }
    }

    if (updated) {
      applyInstantPaint();
    }
  }

  function setupObserver() {
    const observer = new MutationObserver((mutations) => {
      let shouldRepaint = false;
      for (const mutation of mutations) {
        if (mutation.addedNodes.length) {
          shouldRepaint = true;
          break;
        }
      }
      if (shouldRepaint) {
        applyInstantPaint();
      }
    });

    observer.observe(document.body, { childList: true, subtree: true });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      applyInstantPaint();
      setupObserver();
    });
  } else {
    applyInstantPaint();
    setupObserver();
  }

  global.CI = {
    render: applyInstantPaint,
    sync: async () => {
      try {
        await ensureIndexLoaded();
        if (masterIndexData && masterIndexData.indices) {
          const allFiles = masterIndexData.indices.map(i => i.file);
          await Promise.all(allFiles.map(f => loadSaveFile(f)));
        }
      } catch (e) {}
      applyInstantPaint();
    },
    clearCache: () => {
      memoryCache.clear();
      fileCache.clear();
      hashMap.clear();
      masterIndexData = null;
      fallbackSvgEncoded = null;
    }
  };

})(typeof window !== 'undefined' ? window : this);