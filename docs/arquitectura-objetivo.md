# Arquitectura objetivo

Este es el estado al que debes llegar. Los 4 servicios funcionando, mensajería bien configurada, idempotencia donde aplique, y race conditions resueltas.

```mermaid
flowchart LR
    Client([Cliente HTTP])
    BAPI[booking-api<br/>FastAPI]
    AVAIL[availability-service<br/>pika sync<br/>+ with_for_update<br/>+ overlap correcto<br/>+ ack manual]
    PAY[payment-service<br/>aio-pika<br/>+ idempotente<br/>+ env vars]
    NOTIF[notification-service<br/>pika sync<br/>+ ack manual]

    Redis[(Redis)]
    PG[(Postgres)]
    RMQ{{RabbitMQ<br/>exchange: hotel}}

    Client -- POST /bookings --> BAPI
    BAPI -- HSET booking:id --> Redis
    BAPI -- booking.requested --> RMQ
    RMQ -- booking.requested --> AVAIL
    AVAIL -- query+lock+insert --> PG
    AVAIL -- booking.confirmed --> RMQ
    AVAIL -- booking.rejected --> RMQ
    RMQ -- booking.confirmed --> PAY
    PAY -- INSERT --> PG
    PAY -- payment.completed --> RMQ
    PAY -- payment.failed --> RMQ
    RMQ -- payment.completed --> NOTIF
    RMQ -- payment.failed --> NOTIF
```

## Eventos del sistema final

| Routing key | Publicado por | Consumido por |
|---|---|---|
| `booking.requested` | booking-api | availability-service |
| `booking.confirmed` | availability-service | payment-service |
| `booking.rejected` | availability-service | (notification-service opcional) |
| `payment.completed` | payment-service | notification-service |
| `payment.failed` | payment-service | notification-service |

## Bonus (Tier 3): saga compensatoria

Si implementas la saga, agrega también:

- `booking.cancelled` publicado por payment-service cuando el cobro falla
- availability-service consume `booking.cancelled` y libera la habitación
