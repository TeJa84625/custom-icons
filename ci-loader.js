    (function (global) {
    'use strict';

    const CDN_BASE_URL = 'https://ci-icons.vercel.app/';
    const STORAGE_PREFIX = 'ci_icon_';
    const VERSION_PREFIX = 'ci_ver_';
    
    const memoryCache = new Map();

    function cleanAndEncodeSVG(svgString) {
        if (!svgString) return '';
        
        let cleanSvg = svgString
        .replace(/stroke="(?!none)[^"]*"/g, 'stroke="currentColor"')
        .replace(/fill="(?!none)[^"]*"/g, 'fill="currentColor"');

        return encodeURIComponent(cleanSvg.trim())
        .replace(/'/g, "%27")
        .replace(/"/g, "%22");
    }

    async function granularSync(requiredNames = []) {
        if (!navigator.onLine) return;

        try {
        if (requiredNames.length === 0) return;

        const res = await fetch(`${CDN_BASE_URL}svgs.json`);
        if (!res.ok) return;
        const iconsMap = await res.json();

        let anyUpdated = false;

        for (const name of requiredNames) {
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
                anyUpdated = true;
            }
            }
        }

        return anyUpdated;
        } catch (error) {
        console.warn('Background sync failed:', error);
        return false;
        }
    }

    function getIcon(name) {
        let cached = memoryCache.get(name);
        if (!cached) {
        cached = localStorage.getItem(STORAGE_PREFIX + name);
        if (cached) memoryCache.set(name, cached);
        }
        return cached;
    }

    global.CILoader = {
        get: getIcon,
        sync: granularSync,
        clearCache: () => {
        Object.keys(localStorage).forEach(key => {
            if (key.startsWith(STORAGE_PREFIX) || key.startsWith(VERSION_PREFIX)) {
            localStorage.removeItem(key);
            }
        });
        memoryCache.clear();
        console.log('CI Icons storage cleared.');
        }
    };

    })(typeof window !== 'undefined' ? window : this);