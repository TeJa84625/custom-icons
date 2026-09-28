    (function (global) {
    'use strict';

    const CDN_BASE_URL = 'https://ci-icons.vercel.app/';
    const STORAGE_PREFIX = 'ci_icon_';
    const VERSION_PREFIX = 'ci_ver_';

    function cleanAndEncodeSVG(svgString) {
        if (!svgString) return '';
        let cleanSvg = svgString
        .replace(/stroke="(?!none)[^"]*"/g, 'stroke="currentColor"')
        .replace(/fill="(?!none)[^"]*"/g, 'fill="currentColor"');

        return encodeURIComponent(cleanSvg.trim())
        .replace(/'/g, "%27")
        .replace(/"/g, "%22");
    }

    function paintIcons() {
        const icons = document.querySelectorAll('.ci');
        if (!icons.length) return;

        let cssRules = '';
        const styleId = 'ci-styles';
        let styleTag = document.getElementById(styleId);

        if (!styleTag) {
        styleTag = document.createElement('style');
        styleTag.id = styleId;
        document.head.appendChild(styleTag);
        }

        icons.forEach(el => {
        el.classList.forEach(cls => {
            if (cls.startsWith('ci-') && cls !== 'ci' && !isModifierClass(cls)) {
            const name = cls.replace('ci-', '');
            const cached = localStorage.getItem(STORAGE_PREFIX + name);
            if (cached) {
                cssRules += `.${cls} { -webkit-mask-image: url("data:image/svg+xml;utf8,${cached}") !important; mask-image: url("data:image/svg+xml;utf8,${cached}") !important; }\n`;
            }
            }
        });
        });

        if (cssRules) {
        styleTag.textContent = cssRules;
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

    async function syncWithCloud() {
        paintIcons();

        if (!navigator.onLine) return;

        try {
        const res = await fetch(`${CDN_BASE_URL}svgs.json`);
        if (!res.ok) return;
        const iconsMap = await res.json();
        let updated = false;

        for (const [name, remoteData] of Object.entries(iconsMap)) {
            const remoteVer = remoteData.version || '1.0.0';
            const localVer = localStorage.getItem(VERSION_PREFIX + name);
            const hasData = localStorage.getItem(STORAGE_PREFIX + name);

            if (!hasData || remoteVer !== localVer) {
            let svgMarkup = remoteData.svg;
            if (svgMarkup && !svgMarkup.trim().startsWith('<svg')) {
                try {
                const svgRes = await fetch(svgMarkup);
                if (svgRes.ok) svgMarkup = await svgRes.text();
                } catch (e) { continue; }
            }

            if (svgMarkup) {
                const encoded = cleanAndEncodeSVG(svgMarkup);
                localStorage.setItem(STORAGE_PREFIX + name, encoded);
                localStorage.setItem(VERSION_PREFIX + name, remoteVer);
                updated = true;
            }
            }
        }

        if (updated) {
            paintIcons();
        }

        const offlineRunner = `(${paintIcons.toString()})();`;
        localStorage.setItem('ci_cached_engine', offlineRunner);

        } catch (error) {
        console.warn('CI Cloud sync skipped:', error);
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', syncWithCloud);
    } else {
        syncWithCloud();
    }

    })(typeof window !== 'undefined' ? window : this);