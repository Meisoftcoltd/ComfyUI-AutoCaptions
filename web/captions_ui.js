import { app } from "../../scripts/app.js";

const COLOR_MAP = {
    "Blanco Puro": "#FFFFFF",
    "Amarillo Neón": "#FFFF00",
    "Verde Lima": "#00FF00",
    "Cian Eléctrico": "#00FFFF",
    "Rojo Intenso": "#FF0000",
    "Rosa Hot": "#FF00FF",
    "Naranja Vibrante": "#FFA500",
    "Negro Absoluto": "#000000",
    "Azul Océano": "#0000FF",
    "Morado Profundo": "#800080",
    "Oro Brillante": "#FFD700",
    "Plata": "#C0C0C0"
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
                        // El nombre de la fuente es exactamente el nombre del archivo gracias a nuestro auto-renombrador
                        const fontUrl = `/meisoft/fonts/${encodeURIComponent(fontName)}.${ext}`;
                        const font = new FontFace(fontName, `url("${fontUrl}")`);
                        return font.load().then((loadedFace) => {
                            document.fonts.add(loadedFace);
                            this.setDirtyCanvas(true, true); // Forzar repintado cuando cargue la fuente
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

                // --- GENERADOR DINÁMICO DE TEXTO ---
                const maxWords = getVal("max_words_per_line", 4);
                const textCasing = getVal("text_casing", "Normal");

                // Diccionario base de prueba
                const dummySentence = "lorem ipsum dolor sit amet consectetur adipiscing elit".split(" ");
                // Cortar al número de palabras que eligió el usuario
                const activeWords = dummySentence.slice(0, Math.min(maxWords, dummySentence.length));

                const words = activeWords.map((word, index) => {
                    let formattedWord = word;

                    // Aplicar Casing
                    if (textCasing === "Mayúsculas") {
                        formattedWord = word.toUpperCase();
                    } else if (textCasing === "Capitalizado") {
                        formattedWord = word.charAt(0).toUpperCase() + word.slice(1).toLowerCase();
                    }

                    // Espacio final salvo para la última palabra
                    const space = index < activeWords.length - 1 ? " " : "";

                    // Efecto Karaoke: La última palabra usa el highlightColor, el resto el primaryColor
                    const isLast = index === activeWords.length - 1;

                    return {
                        text: formattedWord + space,
                        color: isLast ? highlightColor : primaryColor,
                        scale: 1.0,
                        glow: false
                    };
                });
                // -----------------------------------

                // --- EXTRAER ESTILOS BOLD E ITALIC ---
                const isBold = getVal("bold", false);
                const isItalic = getVal("italic", false);
                const fontStyleStr = `${isItalic ? "italic " : ""}${isBold ? "bold " : ""}`.trim();

                // Función auxiliar para construir el string del font del Canvas
                const getFontString = (size) => `${fontStyleStr ? fontStyleStr + " " : ""}${size}px "${fontName}", sans-serif`;

                // Replicate Python scaling math
                const videoTargetWidth = videoWidth * (fontWidthPercent / 100.0);
                const realCalculatedFontSize = Math.max(12, videoTargetWidth / (18 * 0.55));
                const uiScaleFactor = wBox / videoWidth;
                let finalBaseFontSize = realCalculatedFontSize * uiScaleFactor;

                const scaledOutlineThickness = outlineThickness * uiScaleFactor;
                const scaledShadowOffset = shadowOffset * uiScaleFactor;

                const marginV = 20 * uiScaleFactor;
                const marginH = 20 * uiScaleFactor;
                const paddedWBox = wBox - (marginH * 2);

                // --- LÓGICA DE AUTO-WRAP (MULTILÍNEA) ---

                // 1. Evitar que una sola palabra gigante rompa la caja
                let maxWordWidth = 0;
                words.forEach(w => {
                    ctx.font = getFontString(Math.round(finalBaseFontSize * w.scale));
                    maxWordWidth = Math.max(maxWordWidth, ctx.measureText(w.text.trim()).width);
                });

                if (maxWordWidth > paddedWBox) {
                    finalBaseFontSize = finalBaseFontSize * (paddedWBox / maxWordWidth);
                }

                // 2. Agrupar palabras en líneas inteligentemente
                let lines = [];
                let currentLine = [];
                let currentLineWidth = 0;

                words.forEach(w => {
                    ctx.font = getFontString(Math.round(finalBaseFontSize * w.scale));
                    const wWidth = ctx.measureText(w.text).width;

                    if (currentLine.length > 0 && currentLineWidth + wWidth > paddedWBox) {
                        lines.push({ words: currentLine, width: currentLineWidth });
                        currentLine = [w];
                        currentLineWidth = wWidth;
                    } else {
                        currentLine.push(w);
                        currentLineWidth += wWidth;
                    }
                });
                if (currentLine.length > 0) {
                    lines.push({ words: currentLine, width: currentLineWidth });
                }

                // 3. Cálculos verticales del bloque de texto entero
                const lineHeight = finalBaseFontSize * 1.2;
                const totalTextHeight = lines.length * lineHeight;

                // Extraer alineación
                const [vertAlign, horizAlign] = alignment.split('-');

                // Determinar el Y inicial para empujar el bloque entero
                let startY = yBox + marginV;
                if (vertAlign === "Mid") {
                    startY = yBox + (boxHeight / 2) - (totalTextHeight / 2);
                } else if (vertAlign === "Bottom") {
                    const platformSafeZone = getVal("platform_safe_zone", "None");
                    let platformMargin = 0;

                    // Zonas dinámicas basadas en el % del height real del video
                    if (platformSafeZone === "TikTok") platformMargin = videoHeight * 0.27;
                    else if (platformSafeZone === "Facebook") platformMargin = videoHeight * 0.18;
                    else if (platformSafeZone === "IG Reels") platformMargin = videoHeight * 0.15;
                    else if (platformSafeZone === "YT Shorts") platformMargin = videoHeight * 0.12;

                    const scaledPlatformMargin = platformMargin * uiScaleFactor;
                    // startY es el "techo" del bloque para que termine justo en el margen inferior
                    startY = yBox + boxHeight - marginV - scaledPlatformMargin - totalTextHeight;
                }

                ctx.textBaseline = "top";
                ctx.lineJoin = "round";

                // --- 4. DIBUJAR CADA LÍNEA ---
                lines.forEach((line, lineIndex) => {
                    const textY = startY + (lineIndex * lineHeight);

                    // Alineación horizontal por línea
                    let startX = xBox + marginH;
                    if (horizAlign === "Center") {
                        startX = xBox + (wBox / 2) - (line.width / 2);
                    } else if (horizAlign === "Right") {
                        startX = xBox + wBox - marginH - line.width;
                    }

                    let currentX = startX;

                    line.words.forEach(w => {
                        const fontSize = Math.round(finalBaseFontSize * w.scale);
                        ctx.font = getFontString(fontSize);

                        // Sombra dura
                        ctx.shadowColor = shadowColor;
                        ctx.shadowBlur = 0;
                        ctx.shadowOffsetX = scaledShadowOffset;
                        ctx.shadowOffsetY = scaledShadowOffset;

                        // Borde
                        if (scaledOutlineThickness > 0) {
                            ctx.lineWidth = scaledOutlineThickness * 2;
                            ctx.strokeStyle = outlineColor;
                            ctx.strokeText(w.text, currentX, textY);
                        }

                        // Relleno
                        ctx.shadowBlur = 0;
                        ctx.shadowOffsetX = 0;
                        ctx.shadowOffsetY = 0;
                        ctx.fillStyle = w.color;
                        ctx.fillText(w.text, currentX, textY);

                        currentX += ctx.measureText(w.text).width;
                    });
                });

                ctx.restore();
                return r;
            };
        }
    }
});
