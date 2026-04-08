# Evidencia esperada

Sube aquí los siguientes archivos. Sin esta evidencia se pierden hasta 10 puntos.

## Obligatorios

### 1. Capturas del Management UI de RabbitMQ
(`http://localhost:15672`, usuario: guest, password: guest)

- `rabbitmq-exchanges.png` — captura de la pestaña Exchanges mostrando el exchange `hotel`
- `rabbitmq-queues.png` — captura de la pestaña Queues mostrando las queues que tu sistema creó (availability.requests, payment.requests, notifications)
- `rabbitmq-bindings.png` — captura de los bindings de la queue `notifications` (debe mostrar los dos routing keys: `payment.completed` y `payment.failed`)

### 2. Logs del flujo end-to-end exitoso
- `flujo-completo.log` — salida de `docker compose logs` filtrada al hacer un `POST /bookings` exitoso, mostrando los 4 servicios procesando en cadena

### 3. Ejemplo de curl
- `curl-ejemplos.md` — los comandos curl que usaste para probar, con sus respuestas

### 4. Reporte del quiz teórico
- `quiz-report.json` — el JSON que generaste con el quiz LLM (te lo pasa el profesor en Moodle)

## Opcionales (suman si están)

- `tests-output.txt` — salida de pytest si agregaste tests
- `concurrency-test.log` — evidencia de que arreglaste la race condition (B5): dos curl simultáneos y solo uno pasa
- `notas.md` — cualquier nota adicional sobre tu proceso

## Cómo capturar logs

```bash
# Levanta todo
docker compose up --build -d

# En otra terminal, sigue los logs
docker compose logs -f > evidence/flujo-completo.log

# En otra más, dispara el flujo
curl -X POST http://localhost:8000/bookings \
  -H "Content-Type: application/json" \
  -d '{"guest": "Test", "room_type": "double", "check_in": "2026-05-01", "check_out": "2026-05-05"}'
```
