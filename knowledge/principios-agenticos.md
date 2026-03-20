# Principios Fundacionales para Sistemas Agenticos

Compilado de: Advanced Context Engineering (HumanLayer), 12-Factor Agents
(HumanLayer), AI That Works (BoundaryML). Aplicado a sistemas multi-agente
en produccion.

---

## 1. El Contexto Es El Unico Lever

Los LLMs son funciones stateless. Reciben un context window y producen el
siguiente paso. No hay magia, no hay "inteligencia" oculta. La calidad del
output depende 100% de la calidad del input.

Prioridad del contexto:
1. **Correctitud** — informacion incorrecta es el peor fallo
2. **Completitud** — informacion faltante es el segundo peor
3. **Tamaño** — ruido degrada el rendimiento
4. **Trayectoria** — coherencia direccional importa

Regla practica: mantener el uso del context window entre 40-60%. Mas alla
de eso, la calidad se degrada. Geoff Huntley: "solo tienes ~170K de context
window para trabajar... mientras mas lo uses, peores los resultados."

---

## 2. Own Your Prompts

No delegues el control de tus prompts a un framework. Los prompts son el
codigo fuente de tu sistema agentico. Si no puedes ver, editar y versionar
cada prompt que se envia al LLM, no tienes control sobre tu sistema.

Esto significa:
- Instrucciones explicitas por agente, no generadas automaticamente
- System prompts versionados en tu repo, no escondidos en abstracciones
- Poder inspeccionar exactamente que ve el LLM en cada llamada

---

## 3. Own Your Context Window

Gestiona deliberadamente que informacion ve el LLM en cada llamada.

Lo que consume contexto innecesariamente:
- Historial de sesiones anteriores no relacionadas
- Busquedas de archivos y globbing exploratorio
- Articulos completos cuando los snippets son suficientes
- Outputs JSON grandes de tool calls
- Instrucciones para capacidades que no se usan en esta tarea

Tecnicas de gestion:
- **Limitar historial**: `num_history_runs=3` maximo, `0` para routers
- **Skills lazy-loaded**: el agente ve resumen de 1 linea, carga completo solo si es relevante
- **Busquedas acotadas**: `fixed_max_results=3`, queries compuestas
- **Desactivar lo innecesario**: `add_history_to_context=False` en agentes que no lo necesitan

---

## 4. Own Your Control Flow

El routing y la orquestacion deben estar en tu codigo, no en las decisiones
del LLM.

**Malo**: modo `coordinate` donde el leader decide a quien delegar, cuantas
veces, y cuando parar. Resultado: loops de 7 iteraciones, 625 segundos.

**Bueno**: modo `route` (1 delegacion, sin loop) o `workflow` (secuencia
determinista de pasos). El LLM solo decide QUE hacer dentro de su paso,
no COMO fluye el sistema.

Cuando usar cada modo:
- **Route**: preguntas simples que van a un especialista
- **Workflow**: pipelines repetibles (research → script → review)
- **Coordinate**: solo cuando genuinamente necesitas que el leader sintetice
  multiples outputs (raro, costoso, propenso a loops)
- **Broadcast**: cuando necesitas multiples perspectivas en paralelo

---

## 5. Tools Son Structured Outputs

Una tool call no es "el agente usando una herramienta". Es el LLM generando
un JSON estructurado que tu codigo ejecuta deterministicamente.

Implicaciones:
- El LLM no "ejecuta" nada. Tu codigo lo hace.
- Si el LLM genera un tool call mal formado, es un problema de prompt, no de herramienta.
- Puedes validar, filtrar y transformar tool calls antes de ejecutarlos.
- Puedes simular tool calls en tests sin llamar al LLM.

---

## 6. Agentes Pequeños y Enfocados

Un agente debe hacer UNA cosa bien. Si necesitas describir su rol en mas
de una oracion, probablemente son dos agentes.

**Malo**: "Eres un investigador que busca noticias, analiza tendencias,
escribe scripts, genera imagenes y publica en redes sociales."

**Bueno**: Trend Scout busca. Scriptwriter escribe. Creative Director evalua.
Cada uno con sus propias tools, instrucciones y modelo optimizado para su tarea.

Beneficios:
- Instrucciones mas cortas = menos tokens = mejor adherencia
- Modelo optimizado por tarea (rapido para routing, creativo para escritura)
- Fallos aislados (si el Scriptwriter falla, el Trend Scout no se ve afectado)
- Testeable individualmente con evals

---

## 7. Research → Plan → Act

Para cualquier tarea compleja, la secuencia es:

**Phase 1 — Research**: Entender el espacio del problema. Output es un
documento estructurado de hallazgos. La primera investigacion puede estar
equivocada; re-ejecutar con mas steering si es necesario.

**Phase 2 — Plan**: Producir un plan preciso con pasos, archivos a tocar,
y criterios de verificacion por fase. Un plan construido con research
resuelve problemas en el lugar correcto usando patrones consistentes.

**Phase 3 — Act**: Ejecutar el plan fase por fase. Despues de cada fase
verificada, compactar el estado actual.

**La jerarquia de leverage humano**:
- Mala investigacion → miles de lineas de codigo malas
- Mal plan → cientos de lineas de codigo malas
- Mal codigo → daño localizado

Conclusion: el review humano es mas valioso en el PLAN que en el output.
Leer 200 lineas de un plan bien escrito entrega mas valor que leer 2000
lineas de codigo generado.

---

## 8. Compaction Intencional

Antes de que el contexto se llene, pausa y compacta:

1. Escribe el estado actual a un archivo estructurado (progress.md, research.md)
2. Incluye: objetivo final, enfoque, pasos completados, fallo actual
3. Reinicia con ese archivo como contexto fresco

Esto aplica tanto a agentes de codigo como a agentes de contenido.
El Scriptwriter que genera 3 variantes de storyboard es un ejemplo:
en vez de iterar 7 veces, produce todo en una sola pasada y compacta
el resultado en 3 archivos JSON.

Señales de que necesitas compactar:
- El agente empieza a repetir informacion que ya dijo
- Las respuestas se vuelven mas largas y menos enfocadas
- El agente "olvida" instrucciones del system prompt

---

## 9. Errores Son Informacion, No Excepciones

Cuando un tool call falla, no reintentar ciegamente ni crashear.
Compactar el error de vuelta al contexto como informacion estructurada:

- Que se intento
- Que fallo
- Que dijo el error
- Que intentar diferente

El agente debe adaptar su estrategia basado en el error, no repetir
la misma accion esperando un resultado diferente.

---

## 10. Contactar Humanos Via Tool Calls

La interaccion humana es solo otro tool call. No es un caso especial.

Cuando escalar:
- Elegir entre 2+ enfoques validos con tradeoffs diferentes
- Acciones con efectos externos (enviar emails, crear eventos con invitados)
- Eliminar o sobreescribir datos existentes
- Fallar 2 veces en la misma subtarea

Cuando NO escalar:
- Elegir queries de busqueda (elige la mejor)
- Decisiones de formato (sigue el schema)
- Si incluir una fuente (incluyela)

---

## 11. Launch / Pause / Resume

Los agentes deben ser interrumpibles y resumibles. Si un pipeline falla
a mitad de camino, debe poder continuar desde donde quedo, no reiniciar
desde cero.

Implementacion practica:
- IDs deterministas (scene-00, scene-01) en vez de UUIDs aleatorios
- Verificar si el asset ya existe antes de regenerarlo
- Guardar progreso despues de cada paso completado
- Descriptor/manifest que registra que se completo y que falta

---

## 12. Stateless Reducer

Los agentes deben ser funciones puras sobre su contexto. Dado el mismo
contexto, deben producir el mismo resultado (dentro de la variabilidad
del LLM).

Esto significa:
- No depender de estado global mutable
- No asumir que otro agente ya hizo algo
- Cada agente recibe todo lo que necesita en su input
- El output de un agente es el input del siguiente (pipeline)

---

## 13. Pre-fetch Context (Factor Honorario)

Antes de que el agent loop comience, pre-cargar todo el contexto que
podria necesitar. No descubrirlo durante la ejecucion.

Ejemplos:
- Cargar el knowledge base al inicio, no cuando el agente lo pida
- Inyectar user profile y memories antes de la primera llamada
- Pasar el brief completo al Scriptwriter, no dejarlo que lo busque

---

## 14. Backpressure

Si un agente genera mas trabajo del que el siguiente paso puede procesar,
hay un problema de diseño.

Señales de falta de backpressure:
- Un agente loopea 7 veces cuando 1 vez bastaba
- Se generan 20 resultados de busqueda cuando 3 son suficientes
- El output es tan largo que el usuario no puede revisarlo en tiempo razonable
- El leader re-delega porque "no quedo satisfecho" con la respuesta

Soluciones:
- Limites explicitos en instrucciones ("max 3 tool calls")
- Workflows deterministas sobre coordinacion abierta
- Route mode sobre coordinate mode
- Structured output con schema fijo (el agente no puede divagar)

---

## 15. Specs Son El Nuevo Codigo

Sean Grove: "Descartar los prompts y quedarse solo con el codigo generado
es como compilar un JAR y hacer check-in del binario mientras tiras el
codigo fuente."

En sistemas agenticos, los artefactos de valor son:
1. Las instrucciones y skills (el "codigo fuente" del agente)
2. Los planes y briefs (la especificacion de que construir)
3. Los schemas de output (el contrato entre agentes)

El codigo/contenido generado es el binario. Es reemplazable.
Las specs no lo son.

---

## 16. Mental Alignment

Con agentes generando contenido a alta velocidad, una proporcion cada vez
mayor de tu sistema sera desconocida para ti en cualquier momento dado.

El flujo Research → Plan → Act resuelve esto: los planes y briefs reemplazan
al codigo como el artefacto principal de alineacion. Leer el plan te dice
QUE y POR QUE. El output generado es solo el COMO.

Si pierdes la alineacion mental con tu sistema, pierdes la capacidad de
dirigirlo. Los specs, planes y briefs son tu mapa.

---

## Limitaciones Honestas

- Hay problemas grandes y dificiles que no puedes resolver con prompts en 7 horas
- Race conditions y bugs de concurrencia pueden consumir semanas
- Necesitas al menos una persona experta en el dominio
- No existe el "magic prompt" -- el engagement profundo es obligatorio
- Los agentes multi-step consumen ~4x mas tokens que chat, y multi-agente ~15x
- Para viabilidad economica, el valor de la tarea debe justificar el costo

---

## Aplicacion Practica

Estos principios no son instrucciones para agentes. Son decisiones de
arquitectura que tu tomas como diseñador del sistema:

| Principio | Donde se implementa |
|---|---|
| Own context, Own control flow | Codigo Python (route mode, workflow, limites) |
| Small focused agents | Diseño de agentes (1 rol, 1 modelo, 1 set de tools) |
| Research → Plan → Act | Workflow steps |
| Compaction, Error handling | Skill lazy-loaded (agent-ops) |
| Human escalation | Tool calls + Creative Director pattern |
| Launch/Pause/Resume | Logica de resume en pipelines |
| Specs son codigo | Skills, schemas Pydantic, briefs en archivos |
