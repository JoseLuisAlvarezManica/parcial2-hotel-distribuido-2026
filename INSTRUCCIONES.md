# Instrucciones del examen

## Contexto

Son los nuevos desarrolladores junior del equipo HotelBook. El sistema actual tiene **7 bugs sembrados** y un **servicio sin terminar**. Su trabajo: arreglarlos y completarlo. Tienen hasta el jueves 2026-04-09 a las 23:59.

Cada bug está marcado en el código fuente con un comentario `# BUG:` que les dice qué está mal. **No tienen que adivinar** — tienen que entender por qué está mal y arreglarlo correctamente.

## Trabajo en parejas

Este examen se hace **en parejas (2 personas)**. Lo primero que deben hacer al arrancar es llenar `INTEGRANTES.md` con:

- Nombres completos, matrículas y correos de ambos
- Cómo se van a dividir el trabajo (por servicio, por tier, etc.)
- A medida que avancen, qué hizo cada quien (tabla por bug / archivo)

Ambos integrantes **deben** hacer commits con su propia identidad de Git. Si todos los commits los hace una sola persona, pierden los puntos asignados a `INTEGRANTES.md` y se aplica penalización por colaboración no balanceada.

---

## Tier 1 — Imprescindible (45 pts)

Estos son los arreglos básicos. Con esfuerzo razonable, deben tomarles ~4 horas en total entre los dos.

### B1 — Routing key incorrecto en `booking-api` (5 pts)
**Archivo:** `booking-api/app/rabbitmq.py`

El `booking-api` publica el evento al exchange `hotel`, pero con un routing key equivocado. Por eso el `availability-service` nunca lo recibe.

> Pista: busca `# BUG:` en `booking-api/app/rabbitmq.py`. Compara con el `routing_key` que el `availability-service` está bindeando.

**Cómo verificar el arreglo:**
```bash
docker compose logs availability-service | grep "Recibido"
```
Debes ver el evento llegando al consumer.

---

### B2 — `booking-api` devuelve 200 aunque el publish falle (5 pts)
**Archivo:** `booking-api/app/main.py`

Si RabbitMQ está caído o falla el publish, el endpoint igual devuelve `200 OK` y el cliente cree que su reserva fue aceptada. Eso es mentira.

> Pista: el código actual no tiene `try/except` alrededor del `await publish_booking(...)`. Cualquier error rompe el response, pero peor, ciertos errores se silencian.

**Lo que debes hacer:**
- Envolver la llamada en `try/except`
- Si falla, devolver `503 Service Unavailable` con un mensaje claro
- Loggear el error

**Cómo verificar el arreglo:**
Apaga RabbitMQ (`docker compose stop rabbitmq`) y haz un POST. Debes ver `503`, no `200`.

---

### B3 — `availability-service` usa `auto_ack=True` (5 pts)
**Archivo:** `availability-service/app/main.py`

El consumer está usando `auto_ack=True`. Esto significa que RabbitMQ marca el mensaje como entregado **antes** de que tu callback termine. Si el servicio crashea a la mitad del procesamiento, **el mensaje se pierde** para siempre.

> Pista: cambia a `auto_ack=False` y haz `ch.basic_ack(delivery_tag=method.delivery_tag)` solo cuando el procesamiento termine bien. Si hay error, considera hacer `basic_nack` con `requeue=True`.

**Cómo verificar el arreglo:**
- Lee el código y confirma que el ack es manual
- Bonus: simula un crash a propósito (raise temporal) y verifica que el mensaje se reintenta

---

### B6 — Credenciales hardcodeadas en `payment-service` (5 pts)
**Archivo:** `payment-service/app/db.py`

Las credenciales y URL de Postgres están hardcodeadas en el código. Esto es un problema de seguridad y de configuración: no puedes cambiarlas sin reconstruir la imagen.

> Pista: mira cómo `availability-service/app/db.py` lee `os.getenv(...)` para construir la `DATABASE_URL`. Haz lo mismo aquí. Las variables ya están declaradas en `.env.example`.

**Cómo verificar el arreglo:**
```bash


```
No debe quedar ninguna referencia.

---

### Completar `notification-service` (12 pts)
**Archivo:** `notification-service/app/main.py`

El servicio existe como **skeleton**: la conexión a RabbitMQ ya está, los imports están, pero falta:

- `# TODO 1:` declarar el exchange `hotel` y bindear una queue para `payment.completed` y `payment.failed`
- `# TODO 2:` implementar el callback que loggee de forma estructurada el "envío" de la notificación (no se envía email real, solo se loggea con `logger.info`)
- `# TODO 3:` iniciar el consumer con `channel.basic_consume(...)` y `channel.start_consuming()`

> Pista: copia el patrón de `availability-service/app/main.py`, pero adaptado a los routing keys de pago. Recuerda hacer ack manual.

**Formato del log que debes producir** (es lo que se evalúa):
```
[NOTIFICATION] booking_id=<id> event=PAYMENT_COMPLETED guest=<name> channel=email status=SENT
```

---

### Agregar `notification-service` a `docker-compose.yml` (4 pts)
**Archivo:** `docker-compose.yml`

El servicio existe pero NO está declarado en el `docker-compose.yml`. Agrégalo:
- Build desde `./notification-service`
- `env_file: .env`
- `depends_on` con healthcheck de `rabbitmq`

> Pista: copia la sección de `availability-service` en el mismo `docker-compose.yml` y modifícala.

---

### Verificar el flujo end-to-end (8 pts)

Una vez arreglados los bugs anteriores, este comando debe funcionar y producir efectos en cadena:

```bash
curl -X POST http://localhost:8000/bookings \
  -H "Content-Type: application/json" \
  -d '{"guest": "Test", "room_type": "double", "check_in": "2026-05-01", "check_out": "2026-05-05"}'
```

Y `docker compose logs` debe mostrar:
1. `booking-api` publicando `booking.requested`
2. `availability-service` recibiendo, validando y publicando `booking.confirmed`
3. `payment-service` recibiendo, "cobrando" y publicando `payment.completed` (o `payment.failed`)
4. `notification-service` recibiendo el evento de pago y loggeando la notificación

**Sube capturas y logs a `evidence/`** mostrando este flujo completo funcionando.

---

## Tier 2 — Intermedio (20 pts)

Estos requieren entender más a fondo la mensajería y la persistencia.

### B4 — Lógica de overlap incompleta en `availability-service` (7 pts)
**Archivo:** `availability-service/app/main.py` función `is_room_available`

La función actual solo compara el `check_in` de la nueva reserva contra el `check_in` de las reservas existentes. Eso significa que si ya hay una reserva del 1 al 10 de mayo, una nueva reserva del 5 al 15 de mayo **no es detectada como conflicto**.

> Pista: dos rangos `[a1, a2]` y `[b1, b2]` se solapan cuando `a1 < b2 AND a2 > b1`. Aplícalo en SQL.

**Cómo verificar:**
- Crea una reserva del 1 al 10
- Crea otra del 5 al 15 — debe ser rechazada con `ROOM_NOT_AVAILABLE`

---

### B5 — Race condition por falta de `with_for_update()` (7 pts)
**Archivo:** `availability-service/app/main.py`

El consumer hace dos cosas en secuencia: (1) consulta si la habitación está disponible, (2) inserta la reserva. **Sin un lock**, dos consumers concurrentes pueden ver la habitación libre al mismo tiempo y ambos insertar.

> Pista: viste este patrón en clase con `inventory-service` del proyecto de orders. Necesitas un `with_for_update()` al hacer la query de las reservas existentes para esa habitación, **dentro de la misma transacción**.

**Cómo verificar:**
Lanza dos POST simultáneos para la misma habitación y rango de fechas. Solo uno debe pasar.

```bash
curl -X POST http://localhost:8000/bookings -H "Content-Type: application/json" \
  -d '{"guest": "A", "room_type": "single", "check_in": "2026-06-01", "check_out": "2026-06-03"}' &
curl -X POST http://localhost:8000/bookings -H "Content-Type: application/json" \
  -d '{"guest": "B", "room_type": "single", "check_in": "2026-06-01", "check_out": "2026-06-03"}' &
wait
```

---

### B7 — `payment-service` no es idempotente (6 pts)
**Archivo:** `payment-service/app/main.py`

Si RabbitMQ redeliveres el mismo `booking.confirmed` (porque el consumer crasheó después de cobrar pero antes de hacer ack), el `payment-service` cobra **dos veces**.

> Pista: agrega una tabla `processed_events(event_id PRIMARY KEY)` y antes de procesar, intenta insertar el `event_id`. Si ya existe, saltas el procesamiento (pero igual haces ack).

---

### Llenar `DECISIONES.md`

Documenta brevemente:
- Qué bugs encontraste y cómo los arreglaste
- Por qué tomaste cada decisión (no copies del enunciado, explica con tus palabras)
- Qué cosas decidiste **no** hacer y por qué

---

## Tier 3 — Bonus (5 pts)

Solo si te queda tiempo. Son extras de calidad.

### Saga compensatoria (3 pts)
Cuando `payment.failed` ocurre, la habitación queda bloqueada para siempre. Implementa:
- En `payment-service`: si el pago falla, publicar `booking.cancelled`
- En `availability-service`: agregar binding para `booking.cancelled` y borrar/marcar como cancelada la reserva correspondiente

### Tests, observabilidad, mejoras (2 pts)
Cualquier combinación de:
- Tests con `pytest` para alguna función pura (ej. `is_room_available`)
- Logs estructurados (JSON)
- Healthchecks para todos los servicios en `docker-compose.yml`
- Mejoras al README explicando tus cambios

---

## Lista de verificación final

Antes del push final:

- [X] `INTEGRANTES.md` lleno con nombres, matrículas y división de trabajo
- [ ] Tier 1 completo
- [ ] Flujo end-to-end probado y documentado en `evidence/`
- [ ] Capturas de RabbitMQ Management UI mostrando los exchanges/queues correctos
- [ ] `PROMPTS.md` lleno (declaración de uso de IA)
- [ ] `DECISIONES.md` lleno
- [ ] Commits descriptivos de **ambos** integrantes en el historial
- [ ] Link del fork público subido a Moodle

## Cómo pedir ayuda

- **Dudas técnicas / pistas adicionales**: durante horas hábiles pueden mandar un mensaje pidiendo aclaración. No se les resolverá el bug, pero sí se puede confirmar si van por buen camino.
- **Problemas de Docker**: si Docker no levanta, primero verifiquen que tienen RAM suficiente y que ningún puerto (5432, 6379, 5672, 15672, 8000) está en uso.
- **Si se traban más de 1 hora en un solo bug**: pasen al siguiente y vuelvan. No vale la pena bloquear todo el examen por un solo punto.

¡Mucho éxito!
