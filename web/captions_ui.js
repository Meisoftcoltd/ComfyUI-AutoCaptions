import { app } from "../../scripts/app.js";

const COLOR_MAP = {
    "Blanco Puro": "#FFFFFF",
    "Amarillo Neón": "#FFFF00",
    "Verde Lima": "#00FF00",
    "Cian Eléctrico": "#00FFFF",
    "Rojo Intenso": "#FF0000",
    "Rosa Hot": "#FF00FF",
    "Naranja Vibrante": "#FFA500",
    "Negro Absoluto": "#000000"
};

const loadedFonts = new Set();

app.registerExtension({
    name: "Meisoft.AutoCaptionsUI",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "MeisoftAutoCaptions") {

            // --- 1. SETUP ASÍNCRONO ---
            const onNodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function () {
                const r = onNodeCreated ? onNodeCreated.apply(this, arguments) : undefined;

                // Esperamos un poco para asegurarnos de que los widgets están creados
                setTimeout(() => {
                    if (this.widgets) {
                        const getVal = (name, def) => {
                            const w = this.widgets.find(w => w.name === name);
                            return w ? w.value : def;
                        };
                        const videoWidth = getVal("width", 1080);
                        const videoHeight = getVal("height", 1920);
                        const aspectRatio = videoHeight / videoWidth;
                        const wBox = this.size[0] - 30;
                        const boxHeight = wBox * aspectRatio;

                        const requiredNodeHeight = boxHeight + 200;
                        this.size[1] = Math.max(this.size[1] || 0, requiredNodeHeight);
                        this.setDirtyCanvas(true, true);
                    } else {
                        this.size[1] = Math.max(this.size[1] || 0, 340);
                    }
                }, 100);

                return r;
            };

            // Re-evaluar tamaño cuando cambien width/height (opcional pero recomendado)
            const onPropertyChanged = nodeType.prototype.onPropertyChanged;
            nodeType.prototype.onPropertyChanged = function(property, value) {
                const r = onPropertyChanged ? onPropertyChanged.apply(this, arguments) : undefined;
                if (property === "width" || property === "height") {
                    if (this.widgets) {
                        const getVal = (name, def) => {
                            const w = this.widgets.find(w => w.name === name);
                            return w ? w.value : def;
                        };
                        const videoWidth = getVal("width", 1080);
                        const videoHeight = getVal("height", 1920);
                        const aspectRatio = videoHeight / videoWidth;
                        const wBox = this.size[0] - 30;
                        const boxHeight = wBox * aspectRatio;

                        const requiredNodeHeight = boxHeight + 200;
                        this.size[1] = Math.max(this.size[1] || 0, requiredNodeHeight);
                        this.setDirtyCanvas(true, true);
                    }
                }
                return r;
            };

            // --- 2. RENDERIZADO SEGURO ---
            const onDrawForeground = nodeType.prototype.onDrawForeground;
            nodeType.prototype.onDrawForeground = function (ctx) {
                const r = onDrawForeground ? onDrawForeground.apply(this, arguments) : undefined;

                // Si el nodo está colapsado o aún no tiene widgets, no dibujamos
                if (this.flags.collapsed || !this.widgets) return r;

                // --- OPTIMIZACIÓN: O(1) Widget Lookup ---
                // Solo reconstruimos el mapa si la referencia a la lista de widgets ha cambiado
                // o si la cantidad de widgets es distinta a la procesada previamente.
                if (!this.widgets_map || this._last_widgets_len !== this.widgets.length) {
                    this.widgets_map = new Map();
                    for (const w of this.widgets) {
                        this.widgets_map.set(w.name, w);
                    }
                    this._last_widgets_len = this.widgets.length;
                }

                // Función segura para obtener el valor del widget
                const getVal = (name, def) => {
                    const w = this.widgets_map.get(name);
                    return w ? w.value : def;
                };

                const primaryColorName = getVal("primary_color", "Blanco Puro");
                const highlightColorName = getVal("highlight_color", "Amarillo Neón");
                const outlineColorName = getVal("outline_color", "Negro Absoluto");
                const shadowColorName = getVal("shadow_color", "Negro Absoluto");

                const primaryColor = COLOR_MAP[primaryColorName] || "#FFFFFF";
                const highlightColor = COLOR_MAP[highlightColorName] || "#FFFF00";
                const outlineColor = COLOR_MAP[outlineColorName] || "#000000";
                const shadowColor = COLOR_MAP[shadowColorName] || "#000000";

                const outlineThickness = getVal("outline_thickness", 3);
                const shadowOffset = getVal("shadow_offset", 5);

                const fontName = getVal("font_name", "Bangers");

                // Cargar la fuente dinámicamente si no está cargada (usando API FontFace localmente)
                if (!loadedFonts.has(fontName) && fontName !== "Arial") {
                    loadedFonts.add(fontName);

                    const loadFont = (ext) => {
                        const fontFile = fontName === "Bangers" ? "Bangers-Regular" :
                                         fontName === "Anton" ? "Anton-Regular" :
                                         fontName === "Montserrat" ? "Montserrat-Black" :
                                         fontName === "Oswald" ? "Oswald-Bold" :
                                         fontName === "Permanent Marker" ? "PermanentMarker-Regular" :
                                         fontName === "Comic Neue" ? "ComicNeue-Bold" :
                                         fontName;
                        const font = new FontFace(fontName, `url(/meisoft/fonts/${fontFile}.${ext})`);
                        return font.load().then((loadedFace) => {
                            document.fonts.add(loadedFace);
                        });
                    };

                    loadFont('ttf').catch((e) => {
                        console.warn(`[Meisoft Auto Captions] Failed to load .ttf for ${fontName}, trying .otf...`, e);
                        loadFont('otf').catch((err) => {
                            console.error(`[Meisoft Auto Captions] Failed to load both .ttf and .otf for ${fontName}:`, err);
                        });
                    });
                }

                ctx.save();

                const videoWidth = getVal("width", 1080);
                const videoHeight = getVal("height", 1920);

                const aspectRatio = videoHeight / videoWidth;

                const xBox = 15;
                const wBox = this.size[0] - 30;
                const boxHeight = wBox * aspectRatio;

                const yBox = this.size[1] - boxHeight - 15;

                // Fondo Cinematográfico (Gradiente Radial)
                const cx = xBox + wBox / 2;
                const cy = yBox + boxHeight / 2;
                const radius = Math.max(wBox, boxHeight);
                const gradient = ctx.createRadialGradient(cx, cy, 0, cx, cy, radius);
                gradient.addColorStop(0, "#2a3b4c"); // Centro azulado/gris oscuro
                gradient.addColorStop(1, "#050505"); // Bordes negro absoluto

                ctx.fillStyle = gradient;
                ctx.beginPath();
                ctx.roundRect(xBox, yBox, wBox, boxHeight, 10);
                ctx.fill();

                // Borde sutil para enmarcar
                ctx.strokeStyle = "rgba(255, 255, 255, 0.1)";
                ctx.lineWidth = 1;
                ctx.stroke();

                const fontWidthPercent = getVal("font_width_percent", 80);

                const alignment = getVal("alignment", "Bottom-Center");

                const words = [
                    { text: "LOREM IPSUM ", color: primaryColor, scale: 1.0, glow: false },
                    { text: "DOLOR SIT", color: highlightColor, scale: 1.0, glow: false }
                ];

                // Replicate Python scaling math
                // Target width in real video coordinates
                const videoTargetWidth = videoWidth * (fontWidthPercent / 100.0);

                // base calculated font size for the real video (assumes 18 * 0.55 constant)
                const realCalculatedFontSize = Math.max(12, (videoTargetWidth * 2.0) / (18 * 0.55));

                // Scale factor to translate real video sizes into our UI preview box
                const uiScaleFactor = wBox / videoWidth;

                // However, ASS fontsize is essentially line height.
                // In canvas, px font sizes map somewhat to line height. We need to scale the real font size down to the UI box.
                // Divide by 2 because ASS font size is scaled up by 2 relative to standard pixel size? (According to python target_width * 2.0)
                // Actually the user explicitly told us to NOT divide by 2 here.
                // "Aplica la fórmula base para estimar el tamaño: baseFontSize = (target_width * 2.0) / (18 * 0.55)."
                let finalBaseFontSize = realCalculatedFontSize * uiScaleFactor;

                // Scale outline and shadow relative to UI box
                const scaledOutlineThickness = outlineThickness * uiScaleFactor;
                const scaledShadowOffset = shadowOffset * uiScaleFactor;

                // Apply padding for safety margin (e.g. 10% of box width/height)
                // Actually, platform safe zones use static margins in python (e.g., 20px, 200px, 250px)
                // Let's replicate standard 20px margin scaled
                const marginV = 20 * uiScaleFactor;
                const marginH = 20 * uiScaleFactor;

                const paddedWBox = wBox - (marginH * 2);
                const paddedHBox = boxHeight - (marginV * 2);

                let actualTotalWidth = 0;
                words.forEach(w => {
                    ctx.font = `bold ${Math.round(finalBaseFontSize * w.scale)}px "${fontName}", sans-serif`;
                    actualTotalWidth += ctx.measureText(w.text).width;
                });

                // Parse alignment into vertical and horizontal components
                const [vertAlign, horizAlign] = alignment.split('-');

                let startX = xBox + marginH;
                if (horizAlign === "Center") {
                    startX = xBox + (wBox / 2) - (actualTotalWidth / 2);
                } else if (horizAlign === "Right") {
                    startX = xBox + wBox - marginH - actualTotalWidth;
                }

                let textY = yBox + marginV;
                if (vertAlign === "Mid") {
                    textY = yBox + (boxHeight / 2);
                } else if (vertAlign === "Bottom") {
                    // Check if we have platform safe zone selected
                    const platformSafeZone = getVal("platform_safe_zone", "None");
                    let platformMargin = 0;
                    if (platformSafeZone === "TikTok") platformMargin = 250;
                    else if (platformSafeZone === "IG Reels") platformMargin = 200;
                    else if (platformSafeZone === "YT Shorts") platformMargin = 150;

                    const scaledPlatformMargin = platformMargin * uiScaleFactor;
                    textY = yBox + boxHeight - marginV - scaledPlatformMargin;
                }

                if (vertAlign === "Top") {
                     ctx.textBaseline = "top";
                } else if (vertAlign === "Mid") {
                     ctx.textBaseline = "middle";
                } else if (vertAlign === "Bottom") {
                     ctx.textBaseline = "bottom";
                }

                let currentX = startX;
                ctx.lineJoin = "round";

                words.forEach(w => {
                    const fontSize = Math.round(finalBaseFontSize * w.scale);
                    ctx.font = `bold ${fontSize}px "${fontName}", sans-serif`;

                    // Hard drop shadow
                    ctx.shadowColor = shadowColor;
                    ctx.shadowBlur = 0;
                    ctx.shadowOffsetX = scaledShadowOffset;
                    ctx.shadowOffsetY = scaledShadowOffset;

                    // Stroke
                    if (scaledOutlineThickness > 0) {
                        ctx.lineWidth = scaledOutlineThickness * 2; // multiply by 2 because stroke is centered
                        ctx.strokeStyle = outlineColor;
                        ctx.strokeText(w.text, currentX, textY);
                    }

                    // Fill text
                    ctx.shadowBlur = 0;
                    ctx.shadowOffsetX = 0;
                    ctx.shadowOffsetY = 0;
                    ctx.fillStyle = w.color;
                    ctx.fillText(w.text, currentX, textY);

                    currentX += ctx.measureText(w.text).width;
                });

                ctx.restore();
                return r;
            };
        }
    }
});
