# Arquitectura actual (rota)

Este es el estado en el que recibes el proyecto. Hay 3 servicios coordinados por mensajería pero el flujo está roto.

```mermaid
flowchart LR
    Client([Cliente HTTP])
    BAPI[booking-api<br/>FastAPI]
    AVAIL[availability-service<br/>pika sync]
    PAY[payment-service<br/>aio-pika]
    NOTIF[notification-service<br/>NO EXISTE EN docker-compose]

    Redis[(Redis)]
    PG[(Postgres)]
    RMQ{{RabbitMQ<br/>exchange: hotel}}

    Client -- POST /bookings --> BAPI
    BAPI -- HSET booking:id --> Redis
    BAPI -. routing key INCORRECTO .-> RMQ
    RMQ -. booking.requested .-> AVAIL
    AVAIL -- query/insert --> PG
    AVAIL -- booking.confirmed --> RMQ
    AVAIL -- booking.rejected --> RMQ
    RMQ -- booking.confirmed --> PAY
    PAY -- INSERT --> PG
    PAY -- payment.completed --> RMQ
    PAY -- payment.failed --> RMQ
    RMQ -. ??? .-> NOTIF
```

## Problemas conocidos en este estado

1. **booking-api publica al routing key equivocado** → availability-service nunca recibe nada
2. **booking-api devuelve 200 aunque el publish falle** → cliente recibe respuesta engañosa
3. **availability-service usa auto_ack=True** → pierde mensajes si crashea
4. **availability-service tiene la lógica de overlap incompleta** → reservas solapadas pasan
5. **availability-service no usa with_for_update()** → race condition con reservas concurrentes
6. **payment-service tiene credenciales hardcodeadas** → mal de seguridad y configuración
7. **payment-service no es idempotente** → si RabbitMQ reentrega, cobra dos veces
8. **notification-service no existe en docker-compose y su código está sin terminar**
