/**
 * extract-tokens-inline.js
 *
 * Pure browser-context script for extracting design tokens from a live page.
 * No Node.js or Puppeteer required — runs directly in the page via:
 *   browser act evaluate "<contents of this file>"
 *
 * Returns a JSON object with colors, fonts, spacing, borders, shadows, radii,
 * and CSS custom properties. The agent uses this data to generate DESIGN.md.
 */
(() => {
  const colors = new Map();
  const fonts = new Map();
  const fontSizes = new Map();
  const fontWeights = new Map();
  const lineHeights = new Map();
  const letterSpacings = new Map();
  const borderRadii = new Map();
  const shadows = new Map();
  const borders = new Map();
  const spacings = new Set();
  const fontFeatures = new Map();

  function addColor(color, context) {
    if (!color || color === 'rgba(0, 0, 0, 0)' || color === 'transparent') return;
    if (!colors.has(color)) colors.set(color, { contexts: [], count: 0 });
    const entry = colors.get(color);
    entry.count++;
    if (!entry.contexts.includes(context) && entry.contexts.length < 5) {
      entry.contexts.push(context);
    }
  }

  function rgbToHex(rgb) {
    const match = rgb.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)/);
    if (!match) return rgb;
    const [, r, g, b] = match;
    return '#' + [r, g, b].map(x => parseInt(x).toString(16).padStart(2, '0')).join('');
  }

  const allElements = document.querySelectorAll('*');
  const sampleSize = Math.min(allElements.length, 600);
  const step = Math.max(1, Math.floor(allElements.length / sampleSize));

  for (let i = 0; i < allElements.length; i += step) {
    const el = allElements[i];
    const tag = el.tagName.toLowerCase();
    const cls = el.className && typeof el.className === 'string'
      ? el.className.split(' ').slice(0, 2).join('.')
      : '';
    const ctx = cls ? `${tag}.${cls}` : tag;
    const styles = getComputedStyle(el);

    // Colors
    addColor(styles.color, `text:${ctx}`);
    addColor(styles.backgroundColor, `bg:${ctx}`);
    addColor(styles.borderColor, `border:${ctx}`);
    if (styles.borderTopColor !== styles.borderColor) {
      addColor(styles.borderTopColor, `border-top:${ctx}`);
    }

    // Fonts
    const fontFamily = styles.fontFamily.split(',')[0].trim().replace(/['"]/g, '');
    if (fontFamily) {
      if (!fonts.has(fontFamily)) fonts.set(fontFamily, { count: 0, fullStack: styles.fontFamily });
      fonts.get(fontFamily).count++;
    }

    // Font sizes
    const fontSize = styles.fontSize;
    if (fontSize) {
      if (!fontSizes.has(fontSize)) fontSizes.set(fontSize, { count: 0, elements: [] });
      const entry = fontSizes.get(fontSize);
      entry.count++;
      if (entry.elements.length < 3) entry.elements.push(ctx);
    }

    // Font weights
    const weight = styles.fontWeight;
    if (weight) {
      if (!fontWeights.has(weight)) fontWeights.set(weight, 0);
      fontWeights.set(weight, fontWeights.get(weight) + 1);
    }

    // Line heights
    const lh = styles.lineHeight;
    if (lh && lh !== 'normal') {
      if (!lineHeights.has(lh)) lineHeights.set(lh, 0);
      lineHeights.set(lh, lineHeights.get(lh) + 1);
    }

    // Letter spacing
    const ls = styles.letterSpacing;
    if (ls && ls !== 'normal' && ls !== '0px') {
      if (!letterSpacings.has(ls)) letterSpacings.set(ls, 0);
      letterSpacings.set(ls, letterSpacings.get(ls) + 1);
    }

    // Font feature settings
    const ff = styles.fontFeatureSettings;
    if (ff && ff !== 'normal') {
      if (!fontFeatures.has(ff)) fontFeatures.set(ff, 0);
      fontFeatures.set(ff, fontFeatures.get(ff) + 1);
    }

    // Border radius
    const radius = styles.borderRadius;
    if (radius && radius !== '0px') {
      if (!borderRadii.has(radius)) borderRadii.set(radius, 0);
      borderRadii.set(radius, borderRadii.get(radius) + 1);
    }

    // Shadows
    const shadow = styles.boxShadow;
    if (shadow && shadow !== 'none') {
      if (!shadows.has(shadow)) shadows.set(shadow, 0);
      shadows.set(shadow, shadows.get(shadow) + 1);
    }

    // Borders
    const border = styles.border;
    if (border && border !== 'none' && !border.startsWith('0px')) {
      if (!borders.has(border)) borders.set(border, 0);
      borders.set(border, borders.get(border) + 1);
    }

    // Spacing (margins and paddings)
    ['marginTop', 'marginBottom', 'paddingTop', 'paddingBottom', 'paddingLeft', 'paddingRight'].forEach(prop => {
      const val = parseFloat(styles[prop]);
      if (val > 0 && val < 300) spacings.add(Math.round(val));
    });
  }

  // Convert colors to hex and dedupe
  const colorList = [];
  for (const [raw, data] of colors) {
    const hex = rgbToHex(raw);
    colorList.push({ raw, hex, contexts: data.contexts, count: data.count });
  }
  colorList.sort((a, b) => b.count - a.count);

  // Get CSS custom properties from :root
  const cssVars = {};
  const rootStyles = getComputedStyle(document.documentElement);
  for (const sheet of document.styleSheets) {
    try {
      for (const rule of sheet.cssRules) {
        if (rule.selectorText === ':root' || rule.selectorText === ':root, :host' || rule.selectorText === ':where(:root, :host)') {
          for (const prop of rule.style) {
            if (prop.startsWith('--')) {
              cssVars[prop] = rootStyles.getPropertyValue(prop).trim();
            }
          }
        }
      }
    } catch (e) { /* cross-origin stylesheet — skip */ }
  }

  // Detect Google Fonts / external font links
  const fontLinks = [];
  document.querySelectorAll('link[href*="fonts.googleapis"], link[href*="fonts.adobe"], link[href*="use.typekit"]').forEach(link => {
    fontLinks.push(link.href);
  });

  return JSON.stringify({
    url: window.location.href,
    title: document.title,
    colors: colorList.slice(0, 60),
    fonts: Object.fromEntries([...fonts].sort((a, b) => b[1].count - a[1].count).map(([k, v]) => [k, { count: v.count, fullStack: v.fullStack }])),
    fontSizes: Object.fromEntries([...fontSizes].sort((a, b) => parseInt(b[0]) - parseInt(a[0]))),
    fontWeights: Object.fromEntries([...fontWeights].sort((a, b) => b[1] - a[1])),
    lineHeights: Object.fromEntries([...lineHeights].sort((a, b) => b[1] - a[1]).slice(0, 15)),
    letterSpacings: Object.fromEntries([...letterSpacings].sort((a, b) => b[1] - a[1])),
    fontFeatureSettings: Object.fromEntries([...fontFeatures].sort((a, b) => b[1] - a[1])),
    borderRadii: Object.fromEntries([...borderRadii].sort((a, b) => b[1] - a[1])),
    shadows: Object.fromEntries([...shadows].sort((a, b) => b[1] - a[1]).slice(0, 15)),
    borders: Object.fromEntries([...borders].sort((a, b) => b[1] - a[1]).slice(0, 15)),
    spacingScale: [...spacings].sort((a, b) => a - b),
    cssVariables: cssVars,
    fontLinks,
    meta: {
      elementCount: allElements.length,
      sampledCount: sampleSize,
      extractedAt: new Date().toISOString()
    }
  });
})()
