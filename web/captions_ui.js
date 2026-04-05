import { app } from "../../scripts/app.js";

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

                    const colorWidgets = ["font_color", "highlight_color", "stroke_color", "shadow_color"];

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
                                ctx.fillStyle = this.value || "#FFFFFF";

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

                const fontColor = getVal("font_color", "#FFFFFF");
                const highlightColor = getVal("highlight_color", "#FFFF00");
                const strokeColor = getVal("stroke_color", "#000000");
                const shadowColor = getVal("shadow_color", "#000000");
                const fontName = getVal("font_name", "Arial");

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
                    { text: "MIRA ", color: fontColor, scale: 1.0, glow: false },
                    { text: "ESTE ", color: highlightColor, scale: 1.25, glow: true },
                    { text: "DETALLE", color: fontColor, scale: 1.0, glow: false }
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

                    ctx.shadowColor = shadowColor;
                    ctx.shadowBlur = w.glow ? 10 : 4;
                    ctx.shadowOffsetX = 2;
                    ctx.shadowOffsetY = 2;

                    ctx.lineWidth = 5;
                    ctx.strokeStyle = strokeColor;
                    ctx.strokeText(w.text, currentX, textY);

                    ctx.shadowBlur = 0;
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
