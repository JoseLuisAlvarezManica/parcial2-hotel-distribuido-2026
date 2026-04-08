# Rúbrica de evaluación

**Total: 100 puntos**

---

## Código — 60 pts

### Tier 1 — Imprescindible (40 pts)

| Criterio | Puntos |
|---|---|
| B1 — routing key correcto en `booking-api` | 5 |
| B2 — manejo de error en publicación, devuelve 503 | 5 |
| B3 — `auto_ack=False` con ack manual en `availability-service` | 5 |
| B6 — credenciales en env vars en `payment-service` | 5 |
| `notification-service` completado (TODOs resueltos) | 12 |
| `notification-service` agregado a `docker-compose.yml` | 4 |
| Flujo end-to-end funciona (`POST /bookings` → notificación) | 4 |

### Tier 2 — Intermedio (15 pts)

| Criterio | Puntos |
|---|---|
| B4 — overlap de fechas correcto | 5 |
| B5 — `with_for_update()` resuelve race condition | 5 |
| B7 — idempotencia en `payment-service` | 5 |

### Tier 3 — Bonus (5 pts)

| Criterio | Puntos |
|---|---|
| Saga compensatoria (release de habitación si pago falla) | 3 |
| Tests, observabilidad o mejoras significativas | 2 |

---

## Commits + Evidencia — 20 pts

| Criterio | Puntos |
|---|---|
| Commits atómicos con mensajes claros (no `fix`, no `wip`) | 6 |
| Branch workflow razonable | 2 |
| `evidence/` completo (capturas RabbitMQ, logs, ejemplos curl) | 8 |
| `DECISIONES.md` justificando los cambios | 2 |
| `PROMPTS.md` lleno honestamente | 2 |

---

## Quiz teórico LLM — 20 pts

- El score del quiz se mapea linealmente a 20 puntos
- **Requisito**: `quiz-report.json` presente en `evidence/`
- Sin reporte → 0 pts en esta sección

---

## Penalizaciones

| Falta | Castigo |
|---|---|
| Sin commits (todo aplastado en uno solo) | -10 |
| Sin evidencia | -10 |
| `PROMPTS.md` vacío y se detecta uso de IA | -5 |
| No hace fork (sube ZIP por otro lado) | -10 |
| Copia evidente de otro alumno | suspende |

---

## Calibración

El examen está calibrado así:

- **Alumno con esfuerzo razonable**: ~65/100 alcanzando solo Tier 1 + buena evidencia + quiz aprobado
- **Alumno promedio**: ~80/100 alcanzando Tier 1 + parte de Tier 2 + quiz bien
- **Alumno fuerte**: ~95/100 alcanzando todo, incluyendo bonus
