import { app } from "../../scripts/app.js";

app.registerExtension({
    name: "Meisoft.AutoCaptionsUI",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "MeisoftAutoCaptions") {

            const onNodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function () {
                const r = onNodeCreated ? onNodeCreated.apply(this, arguments) : undefined;

                const colorWidgets = ["font_color", "highlight_color", "stroke_color", "shadow_color"];

                for (const w of this.widgets) {
                    if (colorWidgets.includes(w.name)) {
                        const origDraw = w.draw;
                        w.draw = function(ctx, node, width, y, widget_height) {
                            origDraw.apply(this, arguments);
                            const swatchWidth = 30; // Un poco más grande
                            const margin = 5;
                            ctx.save();
                            // Dibujar sombra del swatch
                            ctx.shadowColor = "rgba(0,0,0,0.5)";
                            ctx.shadowBlur = 4;
                            ctx.fillStyle = this.value || "#FFFFFF";
                            // Bordes redondeados en el swatch
                            ctx.beginPath();
                            ctx.roundRect(width - swatchWidth - margin, y + margin, swatchWidth, widget_height - (margin * 2), 4);
                            ctx.fill();
                            ctx.strokeStyle = "rgba(255,255,255,0.2)";
                            ctx.stroke();
                            ctx.restore();
                        };
                    }
                }
                this.size[1] += 80; // Un poco más de aire abajo
                return r;
            };

            const onDrawForeground = nodeType.prototype.onDrawForeground;
            nodeType.prototype.onDrawForeground = function (ctx) {
                const r = onDrawForeground ? onDrawForeground.apply(this, arguments) : undefined;
                if (this.flags.collapsed) return r;

                const fontColor = this.widgets.find(w => w.name === "font_color")?.value || "#FFFFFF";
                const highlightColor = this.widgets.find(w => w.name === "highlight_color")?.value || "#FFFF00";
                const strokeColor = this.widgets.find(w => w.name === "stroke_color")?.value || "#000000";
                const shadowColor = this.widgets.find(w => w.name === "shadow_color")?.value || "#000000";
                const fontName = this.widgets.find(w => w.name === "font_name")?.value || "Arial";

                ctx.save();
                const boxHeight = 60;
                const yBox = this.size[1] - boxHeight - 15;
                const xBox = 15;
                const wBox = this.size[0] - 30;

                // Fondo Elegante (Degradado oscuro)
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

                // Configuración de palabras
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

                    // Sombra real (Shadow)
                    ctx.shadowColor = shadowColor;
                    ctx.shadowBlur = w.glow ? 10 : 4;
                    ctx.shadowOffsetX = 2;
                    ctx.shadowOffsetY = 2;

                    // Borde (Stroke)
                    ctx.lineWidth = 5;
                    ctx.strokeStyle = strokeColor;
                    ctx.strokeText(w.text, currentX, textY);

                    // Relleno (Fill)
                    ctx.shadowBlur = 0; // Quitamos sombra para el relleno limpio
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