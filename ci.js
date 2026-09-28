(function (global) {
  'use strict';

  function getUsedIconNames() {
    const icons = document.querySelectorAll('.ci');
    const usedIconNames = new Set();
    
    icons.forEach(el => {
      el.classList.forEach(cls => {
        if (cls.startsWith('ci-') && cls !== 'ci' && !cls.startsWith('ci-xs') && !cls.startsWith('ci-sm') && !cls.startsWith('ci-lg') && !cls.startsWith('ci-xl') && !cls.startsWith('ci-2xl') && cls !== 'ci-spin') {
          usedIconNames.add(cls.replace('ci-', ''));
        }
      });
    });

    return Array.from(usedIconNames);
  }

  function applyInstantPaint() {
    if (!global.CILoader) return;

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
          const cachedSvg = global.CILoader.get(iconName);

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

  async function renderAndSync() {
    applyInstantPaint();
    const usedIcons = getUsedIconNames();
    if (usedIcons.length > 0 && global.CILoader) {
      const updated = await global.CILoader.sync(usedIcons);
      if (updated) {
        applyInstantPaint();
      }
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

  if ('requestIdleCallback' in window) {
    requestIdleCallback(() => renderAndSync());
  } else {
    window.addEventListener('load', () => setTimeout(renderAndSync, 1200));
  }

  global.CI = {
    render: applyInstantPaint,
    sync: renderAndSync
  };

})(typeof window !== 'undefined' ? window : this);