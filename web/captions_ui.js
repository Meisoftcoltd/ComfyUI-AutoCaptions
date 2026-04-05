import { app } from "../../scripts/app.js";

app.registerExtension({
    name: "Meisoft.AutoCaptionsUI",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "MeisoftAutoCaptions") {

            // 1. Sobrescribir la creación del nodo para ajustar el tamaño y widgets
            const onNodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function () {
                const r = onNodeCreated ? onNodeCreated.apply(this, arguments) : undefined;

                // Lista de los widgets de color que queremos tunear
                const colorWidgets = ["font_color", "highlight_color", "stroke_color", "shadow_color"];

                for (const w of this.widgets) {
                    if (colorWidgets.includes(w.name)) {
                        const origDraw = w.draw;
                        // Dibujamos un "cuadrado de color" (Swatch) dentro del campo de texto
                        w.draw = function(ctx, node, width, y, widget_height) {
                            origDraw.apply(this, arguments); // Dibuja el texto original

                            const swatchWidth = 25;
                            const margin = 4;
                            ctx.save();
                            ctx.fillStyle = this.value || "#FFFFFF"; // Lee el hex actual
                            ctx.fillRect(width - swatchWidth - margin, y + margin, swatchWidth, widget_height - (margin * 2));
                            ctx.strokeStyle = "#111111";
                            ctx.lineWidth = 2;
                            ctx.strokeRect(width - swatchWidth - margin, y + margin, swatchWidth, widget_height - (margin * 2));
                            ctx.restore();
                        };
                    }
                }

                // Hacemos el nodo un poco más alto por defecto para que quepa la previsualización
                this.size[1] += 70;
                return r;
            };

            // 2. Sobrescribir el dibujado frontal (Foreground) para la previsualización
            const onDrawForeground = nodeType.prototype.onDrawForeground;
            nodeType.prototype.onDrawForeground = function (ctx) {
                const r = onDrawForeground ? onDrawForeground.apply(this, arguments) : undefined;

                // Extraemos los valores actuales
                const fontColor = this.widgets.find(w => w.name === "font_color")?.value || "#FFFFFF";
                const highlightColor = this.widgets.find(w => w.name === "highlight_color")?.value || "#FFFF00";
                const strokeColor = this.widgets.find(w => w.name === "stroke_color")?.value || "#000000";
                const fontName = this.widgets.find(w => w.name === "font_name")?.value || "Bangers";

                ctx.save();

                // Caja de preview
                const boxHeight = 50;
                const yBox = this.size[1] - boxHeight - 10;

                ctx.fillStyle = "#1e1e1e";
                ctx.beginPath();
                ctx.roundRect(10, yBox, this.size[0] - 20, boxHeight, 8);
                ctx.fill();
                ctx.strokeStyle = "#333333";
                ctx.stroke();

                // Setup de tipografía
                ctx.font = `bold 22px "${fontName}", sans-serif`;
                ctx.textBaseline = "middle";
                ctx.lineJoin = "round";
                ctx.lineWidth = 5;

                // Las 3 palabras de prueba
                const word1 = "MIRA ";
                const word2 = "ESTE ";
                const word3 = "DETALLE";

                // Calculamos el ancho total para centrar la frase
                const w1 = ctx.measureText(word1).width;
                const w2 = ctx.measureText(word2).width;
                const w3 = ctx.measureText(word3).width;
                const totalWidth = w1 + w2 + w3;

                // Coordenadas de inicio
                let currentX = (this.size[0] / 2) - (totalWidth / 2);
                const textY = yBox + (boxHeight / 2);
                ctx.textAlign = "left"; // Alineación izquierda para dibujar secuencialmente

                // Función auxiliar para dibujar con borde y relleno
                const drawWord = (text, fillColor) => {
                    ctx.strokeStyle = strokeColor;
                    ctx.strokeText(text, currentX, textY);
                    ctx.fillStyle = fillColor;
                    ctx.fillText(text, currentX, textY);
                    currentX += ctx.measureText(text).width;
                };

                // Dibujamos la frase multicolor
                drawWord(word1, fontColor);
                drawWord(word2, highlightColor); // <- ¡Esta palabra destaca!
                drawWord(word3, fontColor);

                ctx.restore();
                return r;
            };
        }
    }
});