(function (global) {
  'use strict';

  const CDN_BASE_URL = 'https://ci-icons.vercel.app/';
  
  const memoryCache = new Map();
  let iconsMapData = null;
  let isFetchingMap = false;
  let fetchQueue = [];

  function cleanAndEncodeSVG(svgString) {
    if (!svgString) return '';
    
    let cleanSvg = svgString
      .replace(/stroke="(?!none)[^"]*"/g, 'stroke="currentColor"')
      .replace(/fill="(?!none)[^"]*"/g, 'fill="currentColor"');

    return encodeURIComponent(cleanSvg.trim())
      .replace(/'/g, "%27")
      .replace(/"/g, "%22");
  }

  async function applyInstantPaint() {
    const icons = document.querySelectorAll('.ci');
    if (!icons.length) return;

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
          const iconName = cls.replace('ci-', '');
          
          if (memoryCache.has(iconName)) {
            const encoded = memoryCache.get(iconName);
            cssRules += `.${cls} { -webkit-mask-image: url("data:image/svg+xml;utf8,${encoded}") !important; mask-image: url("data:image/svg+xml;utf8,${encoded}") !important; }\n`;
          } else {
            missingIcons.add(iconName);
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
  }

  function isModifierClass(cls) {
    return (
      cls.startsWith('ci-xs') ||
      cls.startsWith('ci-sm') ||
      cls.startsWith('ci-lg') ||
      cls.startsWith('ci-xl') ||
      cls.startsWith('ci-2xl') ||
      cls === 'ci-spin'
    );
  }

  async function fetchAndProcessIcons(targetIconNames) {
    if (!navigator.onLine) return;

    if (iconsMapData) {
      processIconsMap(iconsMapData, targetIconNames);
      return;
    }

    if (isFetchingMap) {
      return new Promise(resolve => {
        fetchQueue.push(() => {
          processIconsMap(iconsMapData, targetIconNames);
          resolve();
        });
      });
    }

    isFetchingMap = true;

    try {
      const res = await fetch(`${CDN_BASE_URL}svgs.json`);
      if (!res.ok) return;
      iconsMapData = await res.json();

      processIconsMap(iconsMapData, targetIconNames);

      while (fetchQueue.length > 0) {
        const callback = fetchQueue.shift();
        callback();
      }
    } catch (error) {
      console.warn('Failed to fetch svgs.json:', error);
    } finally {
      isFetchingMap = false;
    }
  }

  async function processIconsMap(map, targetNames) {
    let updated = false;

    for (const name of targetNames) {
      if (!map[name] || memoryCache.has(name)) continue;
      
      const remoteData = map[name];
      let svgMarkup = remoteData.svg;

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
        memoryCache.set(name, encoded);
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
    sync: () => fetchAndProcessIcons(new Set(Object.keys(iconsMapData || {}))),
    clearCache: () => {
      memoryCache.clear();
      iconsMapData = null;
      console.log('CI Icons memory cache cleared.');
    }
  };

})(typeof window !== 'undefined' ? window : this);