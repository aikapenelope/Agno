# Workflows de Produccion en Agno: Guia Completa

Guia para construir workflows complejos, robustos y de grado de produccion
en Agno. Basada en la documentacion oficial, el cookbook (60+ ejemplos),
y patrones del investment-team y dash repos.

---

## Los 6 Tipos de Step

Agno tiene 6 tipos de step, no solo `Step`. Cada uno resuelve un patron
de orquestacion diferente.

### 1. Step (basico)

Ejecuta un agente, team, o funcion Python.

```python
from agno.workflow.step import Step

# Con agente
step = Step(name="research", agent=my_agent)

# Con funcion
def process(step_input: StepInput) -> StepOutput:
    return StepOutput(content="resultado")

step = Step(name="process", executor=process)

# Con team
step = Step(name="team_work", team=my_team)
```

Configuracion completa:

| Parametro | Default | Que hace |
|---|---|---|
| `max_retries` | 3 | Reintentos en caso de fallo |
| `skip_on_failure` | False | Continuar si falla |
| `requires_confirmation` | False | Pausar para aprobacion humana |
| `on_reject` | skip | skip, cancel, o else_branch |
| `requires_user_input` | False | Pausar para recoger input del usuario |
| `on_error` | skip | fail, skip, o pause |

### 2. Steps (secuencia)

Ejecuta steps en orden, encadenando outputs.

```python
from agno.workflow.steps import Steps

pipeline = Steps(
    name="my_pipeline",
    steps=[step1, step2, step3],
)
```

Cada step recibe el output del anterior via `step_input.previous_step_content`
y todos los outputs anteriores via `step_input.previous_step_outputs["step_name"]`.

### 3. Parallel (ejecucion concurrente)

Ejecuta steps en paralelo usando ThreadPoolExecutor. Agrega resultados.

```python
from agno.workflow.parallel import Parallel

parallel = Parallel(
    step_a,
    step_b,
    step_c,
    name="concurrent_research",
)
```

Cada step paralelo recibe una copia aislada del session_state (deep copy)
para evitar race conditions. Los resultados se agregan en un markdown
con indicadores de exito/fallo por step.

Si cualquier step tiene `stop=True`, el Parallel tambien tiene `stop=True`.

### 4. Loop (iteracion)

Repite steps hasta que una condicion se cumpla o se alcance max_iterations.

```python
from agno.workflow.loop import Loop

loop = Loop(
    steps=[refine_step],
    max_iterations=5,
    end_condition="all_success == true",  # CEL expression
    forward_iteration_output=True,        # iteracion N+1 recibe output de N
)
```

Variables disponibles en CEL:

| Variable | Descripcion |
|---|---|
| `current_iteration` | Numero de iteracion (1-indexed) |
| `max_iterations` | Maximo configurado |
| `all_success` | Boolean — todos los steps exitosos |
| `last_step_content` | Contenido del ultimo step |
| `step_outputs` | Map de step_name → content |

Tambien acepta callable:

```python
def should_stop(context):
    return context["all_success"] and context["current_iteration"] >= 3

loop = Loop(steps=[step1], max_iterations=10, end_condition=should_stop)
```

`forward_iteration_output`:
- `False` (default): cada iteracion recibe el input original
- `True`: iteracion N+1 recibe el output de iteracion N (acumulacion)

### 5. Condition (if/else)

Ejecuta un branch u otro basado en una condicion.

```python
from agno.workflow.condition import Condition

# Con callable
def is_urgent(step_input) -> bool:
    return "urgent" in step_input.input

condition = Condition(
    steps=[urgent_flow],
    evaluator=is_urgent,
    else_steps=[normal_flow],
)

# Con CEL expression
condition = Condition(
    steps=[premium_flow],
    evaluator="'premium' in input",
    else_steps=[basic_flow],
)
```

Variables CEL disponibles: `input`, `previous_step_content`,
`previous_step_outputs`, `additional_data`, `session_state`.

### 6. Router (seleccion dinamica)

Selecciona que step(s) ejecutar de un conjunto de opciones.

```python
from agno.workflow.router import Router

# Con callable
def select_route(step_input, choices):
    if "image" in step_input.input:
        return "vision_step"
    return ["text_step", "summary_step"]

router = Router(
    choices=[vision_step, text_step, summary_step],
    selector=select_route,
    allow_multiple_selections=True,
)

# Con CEL
router = Router(
    choices=[step_a, step_b],
    selector="'data' in input ? 'step_a' : 'step_b'",
)

# Con seleccion humana (HITL)
router = Router(
    choices=[step_a, step_b, step_c],
    requires_user_input=True,
    user_input_message="Selecciona la ruta:",
    allow_multiple_selections=False,
)
```

---

## Flujo de Datos Entre Steps

### StepInput (lo que recibe cada step)

```python
step_input.input                    # input original del workflow
step_input.previous_step_content    # output del step inmediatamente anterior
step_input.previous_step_outputs    # {"step_name": content} de TODOS los steps anteriores
step_input.additional_data          # datos extra pasados al workflow
step_input.session_state            # estado de sesion mutable
```

### StepOutput (lo que produce cada step)

```python
StepOutput(
    content="resultado",     # string o BaseModel
    success=True,            # exito o fallo
    stop=False,              # terminar workflow temprano
    error=None,              # mensaje de error
)
```

### Session State (estado compartido)

El session_state es un dict mutable que fluye por todo el workflow.
En steps secuenciales, los cambios se acumulan. En paralelo, cada step
recibe una deep copy y los resultados se mergean al final.

```python
def my_step(step_input: StepInput, session_state: dict) -> StepOutput:
    # Leer estado
    count = session_state.get("processed_count", 0)
    # Modificar estado
    session_state["processed_count"] = count + 1
    return StepOutput(content="done")
```

### Funciones Custom: Inyeccion de Parametros

Agno inspecciona la firma de tu funcion y inyecta automaticamente:

```python
# Todas estas firmas son validas:
def step(step_input: StepInput) -> StepOutput: ...
def step(step_input: StepInput, run_context: RunContext) -> StepOutput: ...
def step(step_input: StepInput, session_state: dict) -> StepOutput: ...
def step(step_input: StepInput, run_context: RunContext, session_state: dict) -> StepOutput: ...
```

---

## Human-in-the-Loop (HITL)

### Pausar para Confirmacion

```python
step = Step(
    name="deploy",
    executor=deploy_fn,
    requires_confirmation=True,
    confirmation_message="Aprobar deployment?",
    on_reject=OnReject.skip,  # o OnReject.cancel
)
```

### Pausar para Input del Usuario

```python
step = Step(
    name="configure",
    executor=configure_fn,
    requires_user_input=True,
    user_input_message="Proporciona configuracion:",
    user_input_schema=[
        {"name": "threshold", "type": "int", "required": True}
    ],
)
```

### Resumir un Workflow Pausado

```python
# Confirmacion
result = workflow.run(requirements_resolution=[{"approved": True}])

# Input del usuario
result = workflow.run(requirements_resolution=[{"user_input": {"threshold": 42}}])

# Seleccion de ruta
result = workflow.run(requirements_resolution=[{"selected_routes": ["route_a"]}])

# Reintentar error
result = workflow.run(requirements_resolution=[{"retry": True}])
```

### Soporte HITL por Tipo de Step

| Step Type | Confirmacion | User Input | Seleccion de Ruta | Error Pause |
|---|---|---|---|---|
| Step | Si | Si | No | Si (on_error=pause) |
| Router | Si | Si (seleccion) | Si | No |
| Loop | Si (antes de iterar) | No | No | No |
| Condition | Si (elegir branch) | No | No | No |
| Steps | Si (antes del pipeline) | No | No | No |
| Parallel | No | No | No | No |

Parallel no soporta HITL porque no puede pausar todos los threads para
una sola decision humana.

---

## Patrones de Produccion

### Patron 1: Fan-Out / Fan-In (Investigacion Paralela)

```python
workflow = Workflow(
    steps=[
        Step(name="plan", agent=planner),
        Parallel(
            Step(name="search_web", agent=web_researcher),
            Step(name="search_data", agent=data_researcher),
            Step(name="search_sources", agent=source_researcher),
            name="parallel_research",
        ),
        Step(name="synthesize", agent=synthesizer),
    ],
)
```

### Patron 2: Conditional Parallel (busqueda selectiva)

```python
workflow = Workflow(
    steps=[
        Parallel(
            Condition(
                evaluator=lambda si: "tech" in si.input.lower(),
                steps=[Step(name="hn", agent=hn_agent)],
            ),
            Condition(
                evaluator=lambda si: "data" in si.input.lower(),
                steps=[Step(name="stats", agent=stats_agent)],
            ),
            Condition(
                evaluator=lambda si: "social" in si.input.lower(),
                steps=[Step(name="reddit", agent=reddit_agent)],
            ),
            name="selective_research",
        ),
        Step(name="write", agent=writer),
    ],
)
```

### Patron 3: Iterative Refinement (loop con feedback)

```python
workflow = Workflow(
    steps=[
        Step(name="draft", agent=writer),
        Loop(
            steps=[
                Step(name="review", agent=reviewer),
                Step(name="revise", agent=writer),
            ],
            end_condition="'APPROVED' in last_step_content",
            max_iterations=3,
            forward_iteration_output=True,
        ),
    ],
)
```

### Patron 4: Router con HITL (seleccion humana)

```python
workflow = Workflow(
    steps=[
        Step(name="generate_options", agent=generator),
        Router(
            choices=[option_a, option_b, option_c],
            requires_user_input=True,
            user_input_message="Elige la mejor opcion:",
        ),
        Step(name="execute", agent=executor),
    ],
)
```

### Patron 5: Pipeline con QA Gate

```python
workflow = Workflow(
    steps=[
        Step(name="research", agent=researcher),
        Step(name="write", agent=writer),
        Step(
            name="qa_review",
            agent=qa_agent,
            requires_confirmation=True,
            confirmation_message="El articulo pasa QA?",
            on_reject=OnReject.cancel,
        ),
        Step(name="publish", agent=publisher),
    ],
)
```

### Patron 6: Nested Complex (el mas avanzado)

```python
workflow = Workflow(
    steps=[
        Steps(name="phase1", steps=[plan_step, research_step]),
        Parallel(
            Loop(
                steps=[draft_step, review_step],
                max_iterations=3,
                end_condition=lambda ctx: "APPROVED" in ctx.get("last_step_content", ""),
            ),
            Step(name="generate_visuals", agent=visual_agent),
            name="parallel_creation",
        ),
        Condition(
            evaluator="'APPROVED' in previous_step_content",
            steps=[
                Router(
                    choices=[publish_blog, publish_social, publish_email],
                    selector=select_channels,
                )
            ],
            else_steps=[Step(name="fallback", agent=fallback_agent)],
        ),
    ],
)
```

---

## Errores Comunes y Como Evitarlos

### 1. Usar coordinate mode en vez de workflow
**Problema**: El leader del team decide cuantas veces delegar, causando loops.
**Solucion**: Usar workflow con steps deterministas. El LLM decide QUE hacer
dentro de cada step, no COMO fluye el sistema.

### 2. No limitar iteraciones en Loop
**Problema**: Loop infinito si la end_condition nunca se cumple.
**Solucion**: Siempre poner `max_iterations`. 3-5 es suficiente para la
mayoria de casos.

### 3. No manejar fallos en Parallel
**Problema**: Un step paralelo falla y el workflow se detiene.
**Solucion**: Usar `skip_on_failure=True` en steps paralelos no criticos.

### 4. Context pollution en steps largos
**Problema**: Cada step agrega su output al contexto, llenandolo.
**Solucion**: Usar funciones intermedias que compacten el output antes
de pasarlo al siguiente step.

### 5. No usar session_state para datos compartidos
**Problema**: Pasar datos entre steps via el content string, parseando texto.
**Solucion**: Usar session_state como dict tipado para datos estructurados.

---

## Checklist de Produccion

Antes de deployar un workflow, verificar:

- [ ] Cada step tiene `max_retries` configurado
- [ ] Steps no criticos tienen `skip_on_failure=True`
- [ ] Loops tienen `max_iterations` razonable (3-5)
- [ ] Parallel steps no dependen del orden de ejecucion
- [ ] HITL esta en los puntos de decision criticos
- [ ] Session state se usa para datos compartidos (no parsing de strings)
- [ ] Cada step tiene un nombre unico y descriptivo
- [ ] El workflow tiene `db` configurado para persistencia
- [ ] Los agentes dentro de steps tienen modelos apropiados (rapido para routing, calidad para generacion)
- [ ] El workflow esta registrado en AgentOS para monitoreo
