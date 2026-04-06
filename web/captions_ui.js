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

                // Forzamos un tamaño mínimo para asegurar que la preview quepa
                this.size[1] = Math.max(this.size[1] || 0, 340);
                return r;
            };

            // --- 2. RENDERIZADO SEGURO ---
            const onDrawForeground = nodeType.prototype.onDrawForeground;
            nodeType.prototype.onDrawForeground = function (ctx) {
                const r = onDrawForeground ? onDrawForeground.apply(this, arguments) : undefined;

                // Si el nodo está colapsado o aún no tiene widgets, no dibujamos
                if (this.flags.collapsed || !this.widgets) return r;

                // Función segura para obtener el valor del widget
                const getVal = (name, def) => {
                    const w = this.widgets.find(x => x.name === name);
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

                // Cargar la fuente dinámicamente si no está cargada
                if (!loadedFonts.has(fontName) && fontName !== "Arial") {
                    loadedFonts.add(fontName);
                    const link = document.createElement("link");
                    link.rel = "stylesheet";
                    link.href = `https://fonts.googleapis.com/css2?family=${fontName.replace(/ /g, "+")}&display=swap`;
                    document.head.appendChild(link);
                }

                ctx.save();
                const boxHeight = 100;
                const yBox = this.size[1] - boxHeight - 15;
                const xBox = 15;
                const wBox = this.size[0] - 30;

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

                // Apply padding for safety margin (e.g. 10% of box width/height)
                const paddingX = wBox * 0.10;
                const paddingY = boxHeight * 0.10;

                const paddedWBox = wBox - (paddingX * 2);
                const paddedHBox = boxHeight - (paddingY * 2);

                // Calculate base width at a standard font size
                const baseFontSize = 50;
                let baseTotalWidth = 0;
                words.forEach(w => {
                    ctx.font = `bold ${Math.round(baseFontSize * w.scale)}px "${fontName}", sans-serif`;
                    baseTotalWidth += ctx.measureText(w.text).width;
                });

                // Target width based on percentage of padded box width
                const targetWidth = paddedWBox * (fontWidthPercent / 100.0);

                // Scale factor to reach target width
                const scaleFactor = targetWidth / baseTotalWidth;
                const finalBaseFontSize = baseFontSize * scaleFactor;

                let actualTotalWidth = 0;
                words.forEach(w => {
                    ctx.font = `bold ${Math.round(finalBaseFontSize * w.scale)}px "${fontName}", sans-serif`;
                    actualTotalWidth += ctx.measureText(w.text).width;
                });

                // Parse alignment into vertical and horizontal components
                const [vertAlign, horizAlign] = alignment.split('-');

                let startX = xBox + paddingX;
                if (horizAlign === "Center") {
                    startX = xBox + (wBox / 2) - (actualTotalWidth / 2);
                } else if (horizAlign === "Right") {
                    startX = xBox + wBox - paddingX - actualTotalWidth;
                }

                let textY = yBox + paddingY;
                if (vertAlign === "Mid") {
                    textY = yBox + (boxHeight / 2);
                } else if (vertAlign === "Bottom") {
                    textY = yBox + boxHeight - paddingY;
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
                    ctx.shadowOffsetX = shadowOffset;
                    ctx.shadowOffsetY = shadowOffset;

                    // Stroke
                    if (outlineThickness > 0) {
                        ctx.lineWidth = outlineThickness * 2; // multiply by 2 because stroke is centered
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
