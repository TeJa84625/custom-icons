(function (global) {
  'use strict';

  const CDN_BASE_URL = 'https://ci-icons.vercel.app/';
  const cache = new Map();

  async function renderIcon(el) {
    let name = '';
    el.classList.forEach(cls => {
      if (cls.startsWith('ci-') && cls !== 'ci' && !/^(ci-xs|ci-sm|ci-lg|ci-xl|ci-2xl|ci-spin)$/.test(cls)) {
        name = cls.slice(3);
      }
    });

    if (!name) return;

    let svg = cache.get(name);
    if (!svg) {
      try {
        const res = await fetch(`${CDN_BASE_URL}svgs/${name}.svg`);
        if (!res.ok) return;
        svg = await res.text();
        cache.set(name, svg);
      } catch {
        return;
      }
    }

    const doc = new DOMParser().parseFromString(svg, 'image/svg+xml');
    const svgEl = doc.querySelector('svg');
    if (!svgEl) return;

    svgEl.setAttribute('width', '1em');
    svgEl.setAttribute('height', '1em');
    svgEl.style.cssText += 'fill:currentColor;stroke:currentColor;';
    svgEl.setAttribute('class', el.className);
    
    el.replaceWith(svgEl);
  }

  const scan = () => document.querySelectorAll('.ci').forEach(renderIcon);

  new MutationObserver(muts => {
    for (const mut of muts) {
      for (const node of mut.addedNodes) {
        if (node.nodeType === 1) {
          if (node.classList?.contains('ci')) renderIcon(node);
          node.querySelectorAll?.('.ci').forEach(renderIcon);
        }
      }
    }
  }).observe(document.body, { childList: true, subtree: true });

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', scan);
  } else {
    scan();
  }

  global.CI = { render: scan };
})(typeof window !== 'undefined' ? window : this);