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

                // Retrasamos el parcheo 100ms para asegurar que ComfyUI inyectó los widgets
                setTimeout(() => {
                    if (!this.widgets) return; // Seguridad extra

                    const colorWidgets = ["primary_color", "highlight_color", "outline_color", "shadow_color"];

                    for (const w of this.widgets) {
                        if (colorWidgets.includes(w.name) && !w._meisoft_patched) {
                            w._meisoft_patched = true; // Evitar doble parcheo
                            const origDraw = w.draw;

                            w.draw = function(ctx, node, width, y, widget_height) {
                                if (origDraw) origDraw.apply(this, arguments);

                                const swatchWidth = 30;
                                const margin = 5;
                                ctx.save();
                                ctx.shadowColor = "rgba(0,0,0,0.5)";
                                ctx.shadowBlur = 4;
                                ctx.fillStyle = COLOR_MAP[this.value] || "#FFFFFF";

                                ctx.beginPath();
                                ctx.roundRect(width - swatchWidth - margin, y + margin, swatchWidth, widget_height - (margin * 2), 4);
                                ctx.fill();
                                ctx.strokeStyle = "rgba(255,255,255,0.2)";
                                ctx.stroke();
                                ctx.restore();
                            };
                        }
                    }
                }, 100);

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
                const boxHeight = 60;
                const yBox = this.size[1] - boxHeight - 15;
                const xBox = 15;
                const wBox = this.size[0] - 30;

                const gradient = ctx.createLinearGradient(xBox, yBox, xBox, yBox + boxHeight);
                gradient.addColorStop(0, "#1a1a1a");
                gradient.addColorStop(1, "#0a0a0a");
                ctx.fillStyle = gradient;
                ctx.beginPath();
                ctx.roundRect(xBox, yBox, wBox, boxHeight, 10);
                ctx.fill();
                ctx.strokeStyle = "#444";
                ctx.lineWidth = 1;
                ctx.stroke();

                const words = [
                    { text: "MIRA ", color: primaryColor, scale: 1.0, glow: false },
                    { text: "ESTE ", color: primaryColor, scale: 1.0, glow: false },
                    { text: "NUEVO ", color: primaryColor, scale: 1.0, glow: false },
                    { text: "EFECTO", color: highlightColor, scale: 1.25, glow: true }
                ];

                let totalWidth = 0;
                words.forEach(w => {
                    ctx.font = `bold ${Math.round(22 * w.scale)}px "${fontName}", sans-serif`;
                    totalWidth += ctx.measureText(w.text).width;
                });

                let currentX = (this.size[0] / 2) - (totalWidth / 2);
                const textY = yBox + (boxHeight / 2);
                ctx.textBaseline = "middle";
                ctx.lineJoin = "round";

                words.forEach(w => {
                    const fontSize = Math.round(22 * w.scale);
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
