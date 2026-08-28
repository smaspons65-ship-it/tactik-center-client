#!/usr/bin/env bash
#
# Instala el piso de la Doctrina Santiago para TODAS tus sesiones de Claude
# en este computador.
#
#   bash instalar/instalar.sh              instala
#   bash instalar/instalar.sh --mostrar    solo muestra el texto, no instala
#
# Qué hace: copia la sección "The standing floor" de CLAUDE.md a tu archivo
# personal ~/.claude/CLAUDE.md, que Claude lee en cada sesión.
#
# Qué NO hace: borrar nada. Si ya tienes un ~/.claude/CLAUDE.md, guarda una
# copia de seguridad antes de tocarlo y añade el piso al final sin alterar lo
# que ya estaba. Correr esto dos veces no duplica nada: reemplaza su propio
# bloque. Corregir por adición, nunca por sobrescritura — P10.

set -euo pipefail

INICIO="<!-- santiago-floor:inicio - generado por instalar/instalar.sh -->"
FIN="<!-- santiago-floor:fin -->"

RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ORIGEN="$RAIZ/CLAUDE.md"
DESTINO_DIR="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
DESTINO="$DESTINO_DIR/CLAUDE.md"

if [ ! -f "$ORIGEN" ]; then
  echo "Error: no encuentro $ORIGEN" >&2
  echo "Ejecuta esto desde la carpeta del proyecto tactik-center-client." >&2
  exit 1
fi

# El piso vive en un solo lugar: CLAUDE.md. Aquí se extrae, nunca se copia a
# mano, para que las dos versiones no puedan decir cosas distintas.
PISO="$(awk '
  /^## The standing floor$/ { dentro = 1; print; next }
  dentro && /^## / { exit }
  dentro { print }
' "$ORIGEN")"

if [ -z "$PISO" ]; then
  echo "Error: no encontré la sección '## The standing floor' en CLAUDE.md" >&2
  exit 1
fi

# --mostrar imprime el piso y termina. Sirve para pegarlo a mano donde no hay
# sistema de archivos que tocar — por ejemplo, la configuración del navegador.
if [ "${1:-}" = "--mostrar" ]; then
  printf '%s\n' "$PISO"
  exit 0
fi

BLOQUE="$INICIO
$PISO
$FIN"

mkdir -p "$DESTINO_DIR"

if [ ! -f "$DESTINO" ]; then
  printf '%s\n' "$BLOQUE" > "$DESTINO"
  echo "Listo. Creé $DESTINO con el piso de la doctrina."

elif grep -qF "$INICIO" "$DESTINO"; then
  RESPALDO="$DESTINO.respaldo-$(date +%Y%m%d-%H%M%S)"
  cp "$DESTINO" "$RESPALDO"
  TMP="$(mktemp)"
  awk -v inicio="$INICIO" -v fin="$FIN" -v bloque="$BLOQUE" '
    index($0, inicio) { print bloque; saltando = 1; next }
    saltando && index($0, fin) { saltando = 0; next }
    !saltando { print }
  ' "$DESTINO" > "$TMP"
  mv "$TMP" "$DESTINO"
  echo "Listo. Actualicé el piso dentro de $DESTINO."
  echo "Copia de seguridad de la versión anterior: $RESPALDO"

else
  RESPALDO="$DESTINO.respaldo-$(date +%Y%m%d-%H%M%S)"
  cp "$DESTINO" "$RESPALDO"
  printf '\n%s\n' "$BLOQUE" >> "$DESTINO"
  echo "Listo. Añadí el piso al final de $DESTINO, sin tocar lo que ya tenías."
  echo "Copia de seguridad de la versión anterior: $RESPALDO"
fi

echo
echo "A partir de tu próxima sesión de Claude en este computador, el piso"
echo "aplica solo, en cualquier carpeta. Para desinstalarlo, borra el bloque"
echo "entre las marcas santiago-floor en $DESTINO."
