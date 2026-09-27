(function (global) {
  'use strict';

  const CDN_BASE_URL = 'https://ci-icons.vercel.app/';
  const STORAGE_PREFIX = 'ci_icon_';
  const VERSION_PREFIX = 'ci_ver_';
  
  // In-memory runtime cache to minimize LocalStorage reads
  const memoryCache = new Map();

  /**
   * Sanitizes and Prepares SVGs for CSS Mask Data URIs
   * Replaces fixed colors with currentColor and cleans formatting
   */
  function cleanAndEncodeSVG(svgString) {
    if (!svgString) return '';
    
    let cleanSvg = svgString
      // Replace hardcoded stroke colors with currentColor
      .replace(/stroke="(?!none)[^"]*"/g, 'stroke="currentColor"')
      // Replace hardcoded fill colors with currentColor (if not fill="none")
      .replace(/fill="(?!none)[^"]*"/g, 'fill="currentColor"');

    // Encode for safe SVG Data URI
    return encodeURIComponent(cleanSvg.trim())
      .replace(/'/g, "%27")
      .replace(/"/g, "%22");
  }

  /**
   * Scans DOM and applies SVG masks instantly from Cache
   */
  function applyInstantPaint() {
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

    icons.forEach(el => {
      el.classList.forEach(cls => {
        if (cls.startsWith('ci-') && cls !== 'ci') {
          const iconName = cls.replace('ci-', '');
          
          let cachedSvg = memoryCache.get(iconName);
          if (!cachedSvg) {
            cachedSvg = localStorage.getItem(STORAGE_PREFIX + iconName);
            if (cachedSvg) memoryCache.set(iconName, cachedSvg);
          }

          if (cachedSvg) {
            cssRules += `.${cls} { -webkit-mask-image: url("data:image/svg+xml;utf8,${cachedSvg}") !important; mask-image: url("data:image/svg+xml;utf8,${cachedSvg}") !important; }\n`;
          }
        }
      });
    });

    if (cssRules && styleTag.textContent !== cssRules) {
      styleTag.textContent += cssRules;
    }
  }

  /**
   * Non-blocking background sync for remote SVGs
   */
  async function granularSync() {
    if (!navigator.onLine) return;

    try {
      const icons = document.querySelectorAll('.ci');
      const usedIconNames = new Set();
      
      icons.forEach(el => {
        el.classList.forEach(cls => {
          if (cls.startsWith('ci-') && cls !== 'ci' && !cls.startsWith('ci-xs') && !cls.startsWith('ci-sm') && !cls.startsWith('ci-lg') && !cls.startsWith('ci-xl') && !cls.startsWith('ci-2xl') && cls !== 'ci-spin') {
            usedIconNames.add(cls.replace('ci-', ''));
          }
        });
      });

      if (usedIconNames.size === 0) return;

      const res = await fetch(`${CDN_BASE_URL}svgs.json`);
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
            localStorage.setItem(STORAGE_PREFIX + name, encoded);
            localStorage.setItem(VERSION_PREFIX + name, remoteVer);
            memoryCache.set(name, encoded);
            updated = true;
          }
        }
      }

      if (updated) {
        applyInstantPaint();
      }
    } catch (error) {
      console.warn('Background sync skipped:', error);
    }
  }

  // Setup DOM MutationObserver for dynamically inserted icons
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

  // Initial Execution
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      applyInstantPaint();
      setupObserver();
    });
  } else {
    applyInstantPaint();
    setupObserver();
  }

  if ('requestIdleCallback' in window) {
    requestIdleCallback(() => granularSync());
  } else {
    window.addEventListener('load', () => setTimeout(granularSync, 1200));
  }

  // Expose Global Public API
  global.CI = {
    render: applyInstantPaint,
    sync: granularSync,
    clearCache: () => {
      Object.keys(localStorage).forEach(key => {
        if (key.startsWith(STORAGE_PREFIX) || key.startsWith(VERSION_PREFIX)) {
          localStorage.removeItem(key);
        }
      });
      memoryCache.clear();
      console.log('CI Icons cache cleared.');
    }
  };

})(typeof window !== 'undefined' ? window : this);
