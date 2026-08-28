# Cinco tensiones abiertas

*Lo que el razonamiento todavía no resuelve, formulado como preguntas con
criterio de cierre.*

El análisis que acompaña a este documento separa las capas del texto. Este separa
otra cosa: **qué queda por pensar**. Cada tensión va con lo que la resolvería, y
con lo que pasa si se deja abierta.

Están en orden de carga. La primera sostiene la legitimidad ética del producto.
La segunda sostiene su utilidad. Las otras tres son precisión.

---

## 1. La tensión de agencia

> Si el humano es predeciblemente influido, ¿qué significa que conserve la
> responsabilidad?

**El problema.** Tu §2.4 demuestra que el juicio humano es sistemáticamente
desviado por fluidez y aplomo, y que el LLM amplifica el efecto. Tu §2.6
responde que la responsabilidad permanece humana. Pero eso no resuelve el §2.4:
le asigna la responsabilidad a la parte que acabas de mostrar comprometida.

Responsabilidad sin capacidad restituida es una formalidad —y es la formalidad
estándar de la industria, porque traslada el riesgo al usuario sin costo para el
proveedor. Si TACTIK termina ahí, es indistinguible de un disclaimer bien
escrito.

**Lo que salvaría el argumento.** Que la arquitectura *devuelva* la capacidad:
que etiquetar el estatus de una afirmación reduzca de forma medible el peso que
esa afirmación ejerce sobre el juicio de quien la recibe. No que la haga más
exacta —que la haga pesar lo que debe pesar.

**Lo que lo cerraría.** Es empírico y es barato de probar, y no necesita el
producto completo:

- Mismo contenido, dos presentaciones: una con estatus etiquetado (evidencia /
  deducción / hipótesis / desconocido), otra sin etiquetar.
- Sujetos distintos, decisión con consecuencia declarada de antemano.
- Se mide **desplazamiento de posición**, no satisfacción ni percepción de
  utilidad. Cuánto se movió cada quien respecto de su posición inicial.
- La predicción de tu doctrina es específica y falsable: el etiquetado debe
  reducir el desplazamiento causado por afirmaciones de baja base, **sin**
  reducir el causado por afirmaciones bien respaldadas. Si reduce ambos por
  igual, no construiste gobernanza epistémica: construiste un freno.

**Si se deja abierta.** El §2.6 sigue siendo hipótesis presentada como
principio. Es defendible ante un cliente y no lo es ante un evaluador serio, ni
ante ti mismo dentro de dos años.

---

## 2. La regla de conversión que falta

> ¿Cuánto *debe* moverte una afirmación bien etiquetada?

**El problema.** Decantar clasifica. No pondera. Tu §2.3 te dice que algo es
deducción y no evidencia; no te dice cuánto menos debe pesar por serlo. Y la
influencia no es solo el riesgo: también es el objetivo. Un asesor que nunca te
mueve no sirve.

Sin regla de conversión, el usuario termina con una pila mejor ordenada y el
mismo problema de juicio que tenía al empezar. Peor: puede sentir que ya lo
resolvió, porque la pila *parece* resuelta.

**Lo interesante es que ya tienes la regla.** La duda asimétrica —destruir un
juicio construido sobre muchas señales independientes debe costar más evidencia
que construirlo— es exactamente una regla de tipo de cambio. Está en tus
principios Santiago. No está en el documento de filosofía. **El documento no
carga su propia regla más útil.**

**Lo que lo cerraría.** Escribir la matriz. Para cada capa del §2.3, en qué
condiciones puede mover una decisión y cuánto:

- ¿Puede una hipótesis plausible, sola, justificar una acción reversible? (Tu
  §3.5 sugiere que sí: *«un piloto reversible puede justificarse aunque el
  resultado final sea desconocido»*.)
- ¿Puede justificar una irreversible? (Casi seguro que no, y conviene decirlo.)
- ¿Cuántas deducciones respaldadas equivalen a una evidencia? ¿O no equivalen
  nunca, y la pregunta está mal planteada?
- ¿Qué hace falta para *bajar* algo de evidencia a deducción? Por tu propia
  regla, más de lo que hizo falta para subirlo.

Es una tarde de trabajo y convierte una taxonomía en un método operable.

**Si se deja abierta.** El producto clasifica y no decide, y el usuario tiene que
poner la parte difícil —que es justo lo que el §1 dice que el producto existe
para mejorar.

---

## 3. Quién gana el conflicto

> Si el sistema señala una contradicción y el humano quiere avanzar igual,
> ¿qué pasa?

**El problema.** El §3.5 dice que un contenido puede «corregirse, estrecharse o
bloquearse». *Bloquearse* es una palabra grande y el documento la suelta sin
desarrollarla. Es la pregunta que hace todo comprador institucional en el minuto
tres de la primera reunión, y no está contestada.

Las tres respuestas posibles llevan a productos distintos:

| Respuesta | Consecuencia |
|---|---|
| **Bloquea** | Contradice el §2.6 —la responsabilidad ya no es del humano si no puede ejercerla. Y se desactiva en cuanto estorba. |
| **Advierte y sigue** | No es gobernanza, es una nota al pie. Se aprende a ignorar en dos semanas. |
| **Registra el override y cede** | Preserva la agencia, deja rastro, y crea el activo. |

**Mi lectura, para que la discutas.** La tercera, sin dudarlo. Y no por
compromiso: **la entrada de override es el dato más valioso que el sistema
genera.** Es el único lugar donde queda registrado el juicio humano operando
*contra* la recomendación, con el motivo escrito antes de conocer el resultado.
Eso es exactamente lo que tu §8 necesita para aprender —y ninguna otra cosa del
producto lo produce.

Un override registrado y luego contrastado con el outcome es la unidad mínima de
evidencia sobre si tu arquitectura sirve. Bloquear la destruye. Advertir no la
captura.

**Lo que lo cerraría.** Una decisión tuya, escrita, con el formato de la entrada
de override: qué se señaló, qué decidió el humano, qué razón dio, y —después—
qué pasó.

---

## 4. La fricción, que no se menciona

> ¿Qué le cuesta al usuario, y en qué momento lo paga?

**El problema.** El documento no tiene una sola línea sobre esto. Y los sistemas
de gobernanza no fracasan por estar equivocados: fracasan porque se los saltan.

Objective Lock tiene la peor forma de adopción que existe: **exige trabajo antes
de que haya valor**, en el momento en que el usuario está más ocupado, más
apurado y más seguro de que ya sabe lo que quiere. El valor aparece después, y
solo si algo sale mal. Es la estructura de incentivos de un seguro, vendida con
el lenguaje de una herramienta.

Y hay un agravante: el usuario que más necesita sellar el objetivo —el que va
entrando a la negociación convencido— es exactamente el que menos va a hacerlo.

**Lo que lo cerraría.** Tres preguntas contestadas por escrito:

- ¿Cuántos minutos cuesta sellar un objetivo? Si no lo has cronometrado con
  alguien que no seas tú, no lo sabes.
- ¿Qué recibe el usuario **en ese mismo momento**, antes de saber si sirvió? Sin
  una respuesta a esto, la adopción depende de disciplina, y la disciplina no
  escala.
- ¿Quién en la organización paga el costo y quién recibe el beneficio? Si no son
  la misma persona —y casi nunca lo son— eso determina a quién le vendes.

**Si se deja abierta.** Es la causa de muerte más probable del producto, y sería
por una razón que no tiene nada que ver con si la doctrina es correcta.

---

## 5. Convergencia

> ¿Las interpretaciones convergen con más evidencia, o no?

**El problema.** El §2.2 dice: una sola realidad, múltiples interpretaciones. Lo
enuncia y lo abandona. Pero tiene una consecuencia que decide qué es tu registro:

- **Si convergen** — el registro puede resolver contradicciones, comparar ex ante
  con ex post significa aprender, y tu §8 tiene sentido.
- **Si no convergen** — el registro solo acumula lecturas paralelas, y el
  «aprendizaje longitudinal» es un archivo ordenado.

Tu §8 presupone convergencia. Eres realista en la práctica y pluralista en la
redacción del §2.2.

**Lo que lo cerraría.** Una frase en el §2.2 que diga cuál de las dos cosas
crees, y una regla en el registro que la implemente: cuándo una contradicción se
da por resuelta, con qué evidencia, y quién lo declara.

**Si se deja abierta.** Menor que las otras cuatro, pero es una grieta que un
lector filosóficamente entrenado encuentra en dos minutos y usa para dudar del
resto.

---

## Una observación sobre el conjunto

Cuatro de las cinco tensiones son **empíricas y baratas**: un experimento de
etiquetado, una matriz escrita en una tarde, una decisión de diseño, tres
preguntas cronometradas. Ninguna requiere construir el producto completo, y
ninguna requiere más doctrina.

Eso es coherente con lo que tu §8 ya dice: *el siguiente desafío no es agregar
más conceptos*. Las tensiones abiertas no se cierran pensando mejor. Se cierran
midiendo.

La quinta —convergencia— sí es conceptual, y es la más pequeña.
