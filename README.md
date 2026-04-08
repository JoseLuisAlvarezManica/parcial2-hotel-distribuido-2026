# HotelBook — Sistema Distribuido de Reservas

> **Examen Parcial 2 — Sistemas Distribuidos**
> Primavera 2026

## Bienvenida

¡Bienvenido al equipo de **HotelBook**! Acabas de incorporarte como **desarrollador junior**. Tu equipo anterior dejó el sistema con varios bugs, mensajería mal configurada, una race condition, falta de idempotencia y un servicio sin terminar.

Tu trabajo durante las próximas ~36 horas: **diagnosticar, arreglar y completar** el sistema, y entregar evidencia de que funciona end-to-end.

Antes de empezar, **lee `INSTRUCCIONES.md`**. Ahí está la lista completa de tareas, divididas en tiers, con pistas claras sobre dónde buscar.

## Arquitectura actual (rota)

```
                            ┌─────────────────┐
              ┌────────────►│  Postgres       │
              │             │  hotel_db       │
              │             └─────────────────┘
              │
┌─────────────┴─┐    booking.requested    ┌────────────────────┐
│  booking-api  │────────────────────────►│ availability-svc   │
│  (FastAPI)    │      RabbitMQ topic     │  (pika sync)       │
└───────────────┘       exchange          └─────────┬──────────┘
       │                                            │ booking.confirmed
       │                                            │ booking.rejected
       │                                            ▼
       │                                  ┌────────────────────┐
       │                                  │  payment-service   │
       │                                  │   (aio-pika)       │
       │                                  └─────────┬──────────┘
       │                                            │ payment.completed
       │                                            │ payment.failed
       │                                            ▼
       │                                  ┌────────────────────┐
       │                                  │ notification-svc   │
       │                                  │   (NO EXISTE AÚN)  │
       │                                  └────────────────────┘
       │
       ▼
   Redis (estado de la reserva)
```

Ver diagramas Mermaid en `docs/arquitectura-actual.md` y `docs/arquitectura-objetivo.md`.

## Stack

- **Python 3.12**
- **FastAPI** + **aio-pika** (booking-api)
- **pika** sync (availability-service)
- **aio-pika** (payment-service)
- **pika** (notification-service skeleton)
- **PostgreSQL 16** + SQLAlchemy
- **Redis 7**
- **RabbitMQ 3** (con management plugin)
- **Docker Compose**

## Cómo correrlo

```bash
# 1. Copia las variables de entorno
cp .env.example .env

# 2. Levanta todo
docker compose up --build

# 3. (En otra terminal) prueba el endpoint
curl -X POST http://localhost:8000/bookings \
  -H "Content-Type: application/json" \
  -d '{
    "guest": "Ana López",
    "room_type": "double",
    "check_in": "2026-05-01",
    "check_out": "2026-05-05"
  }'
```

UI de RabbitMQ en `http://localhost:15672` (usuario: `guest`, password: `guest`).

## ¿Por dónde empiezo?

1. Lee este archivo (ya lo estás haciendo, ¡bien!)
2. **Lee `INSTRUCCIONES.md` completo**
3. Levanta el sistema con `docker compose up --build`
4. Haz un POST de prueba con curl y observa qué pasa (o qué NO pasa)
5. Atacar **Tier 1** primero — son bugs fáciles con pistas claras
6. Pasar a **Tier 2** cuando todo lo de Tier 1 funcione
7. Si te queda tiempo, **Tier 3** para puntos bonus
8. Llenar `evidence/`, `PROMPTS.md`, `DECISIONES.md`
9. Hacer el quiz teórico (te paso el link en Moodle) y guardar el reporte JSON
10. Push final + sube link de tu fork a Moodle

## Reglas

- **Hacer fork público** del repositorio del examen
- **Commits frecuentes y descriptivos** (no `wip`, no `fix`, no `cambios`)
- Si usas IA (Claude/ChatGPT/Copilot): **debes declararlo en `PROMPTS.md`**. No hacerlo y que se detecte = penalización
- **No copiar** entre compañeros (los commits dejan rastro)
- Entrega: **link de tu fork público en Moodle antes del jueves 23:59**

## Calificación

Ver `RUBRICA.md`. Resumen:

- **60 pts** — Código (Tier 1: 40, Tier 2: 15, Tier 3 bonus: 5)
- **20 pts** — Commits + evidencia
- **20 pts** — Quiz LLM teórico

¡Mucho éxito! El examen está calibrado para que con esfuerzo razonable saques una buena nota.
