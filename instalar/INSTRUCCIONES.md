# Cómo dejar la doctrina siempre encendida

Sin jerga. Tres situaciones, en orden de menos a más trabajo.

Antes de nada, una aclaración que evita confusiones: **una skill no se activa
sola siempre.** Se activa cuando lo que estás pidiendo se parece a para lo que
sirve. Lo que sí está siempre encendido es un archivo llamado `CLAUDE.md`, que
Claude lee al empezar cada sesión. Por eso hay dos cosas y no una: el *piso*
(cinco reglas baratas, siempre) y la *skill* `/santiago` (la postura completa,
cuando hay algo en juego).

---

## 1. Dentro de este proyecto — ya está listo

No tienes que hacer nada. El archivo `CLAUDE.md` está guardado en el
repositorio. Cada vez que abras Claude en esta carpeta —desde el navegador o
desde tu computador, da igual— el piso se carga solo, y `/santiago`,
`/doctrine-review` y `/sealed-run` están disponibles.

Esto también vale para cualquier persona a quien le pases el repositorio. Es
deliberado: quien te revise trabaja con tus mismas reglas.

---

## 2. En tu computador, para todas tus carpetas — un comando

Abre la aplicación de Claude o la terminal en la carpeta de este proyecto, y
escribe exactamente esto:

```
bash instalar/instalar.sh
```

Eso es todo. Te va a responder algo como *«Listo. Creé …»*.

**Qué hace:** copia las cinco reglas del piso a tu archivo personal
`~/.claude/CLAUDE.md`, que Claude lee en todas tus sesiones de este computador,
estés en la carpeta que estés.

**Qué NO hace, para tu tranquilidad:**

- No borra nada. Si ya tenías notas ahí, las conserva y añade el piso al final.
- Antes de tocar cualquier cosa guarda una copia de seguridad, con la fecha en
  el nombre.
- Si lo corres dos veces no se duplica: reemplaza su propio bloque.
- Para deshacerlo, borra las líneas entre `santiago-floor:inicio` y
  `santiago-floor:fin` en ese archivo. Nada más.

**Para que las skills también funcionen fuera de este proyecto**, escribe estas
dos líneas en Claude, una y luego la otra:

```
/plugin marketplace add smaspons65-ship-it/tactik-center-client
/plugin install santiago-doctrine@tactik
```

Después de eso tendrás `/santiago-doctrine:santiago` en cualquier carpeta. Ojo:
el plugin trae las skills, no el piso — el piso lo instala el comando de arriba.

---

## 3. En el navegador, en conversaciones normales — pegar un texto

Aquí no hay archivos que tocar, así que hay que pegar el piso a mano una vez.

**Paso 1.** Escribe esto en Claude para que te muestre el texto:

```
bash instalar/instalar.sh --mostrar
```

Copia todo lo que aparezca.

**Paso 2.** En claude.ai, entra a la configuración de tu cuenta y busca el
apartado de instrucciones personales — el que le dice a Claude cómo quieres que
te responda siempre. Pega ahí el texto y guarda.

> No puedo verificar desde aquí cómo se llama exactamente ese apartado ni dónde
> está en el menú, porque no tengo acceso a tu cuenta y las etiquetas de la
> interfaz cambian. Búscalo por el sentido: es la sección de preferencias o
> instrucciones personalizadas, no la de un proyecto concreto. Si no lo
> encuentras, dime qué opciones ves y te digo cuál es.

---

## Lo que esto no resuelve

**Claude Code en el navegador, en otros repositorios.** Cada sesión web arranca
en una máquina nueva y temporal, así que lo que instales en el computador no
llega ahí. Para otro repositorio tuyo, la vía que sí funciona es ponerle su
propio `CLAUDE.md` — puedes copiar el de este proyecto, o pedírmelo y lo hago.

*Nota: que las sesiones web no conserven la configuración personal entre una y
otra es lo que observo en el funcionamiento de este entorno, no algo que haya
podido confirmar en la documentación. Si algún día ves que sí se conserva, esta
sección sobra.*

**Que la skill se active en el momento justo.** Eso lo decide su descripción, y
solo se calibra usándola. Si notas que `/santiago` aparece en preguntas triviales
o que no aparece cuando la necesitas, dímelo y ajusto la descripción. Siempre
puedes forzarla escribiendo `/santiago` tú mismo.
