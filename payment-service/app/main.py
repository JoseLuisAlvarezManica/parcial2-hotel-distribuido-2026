"""payment-service – consumer async que simula el cobro de una reserva."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import random

import aio_pika

from .db import Payment, Processed_events, SessionLocal, init_db
from sqlalchemy import select

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger("payment-service")

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")

PRICE_BY_TYPE = {"single": 800, "double": 1500, "suite": 3200}


async def charge_payment(payload: dict) -> tuple[bool, str]:
    """Simula un cobro: tarda un momento y falla aleatoriamente el 20%."""
    await asyncio.sleep(random.uniform(0.2, 0.6))
    if random.random() < 0.2:
        return False, "Tarjeta rechazada por el banco simulado"
    return True, ""


async def process_event(payload: dict) -> tuple[bool, str]:
    booking_id = payload["booking_id"]
    room_type = payload["room_type"]
    amount = PRICE_BY_TYPE.get(room_type, 1000)

    # BUG: falta idempotencia. Si RabbitMQ reentrega este mismo evento (porque
    # el consumer crasheó después de cobrar pero antes de hacer ack), vamos a
    # cobrar dos veces. Necesitas chequear si el booking_id ya fue procesado
    # antes de cobrar. Una opción simple: una tabla processed_events(event_id PK)
    # y tratar de insertarlo al inicio; si ya existe, saltar el cobro.
    
    #Comprobar que no exista dentro de la bd el evento de pago
    async with SessionLocal() as session:
        command = select(Processed_events).where(Processed_events.event_id == booking_id)
        payment = (await session.execute(command)).scalar_one_or_none()
    
        if payment:
            query = select(Payment.status).where(Payment.booking_id == booking_id)
            is_success = (await session.execute(query)).scalar_one_or_none()
            logger.info("Evento ya procesado, procesando el duplicado booking=%s", booking_id)
            return is_success == "COMPLETED", "duplicado procesado"
        
    success, reason = await charge_payment(payload)

    async with SessionLocal() as session:
        #Registrar pago como evento procesado
        session.add(Processed_events(
                        event_id=booking_id
                    )
        )

        session.add(
                    Payment(
                        booking_id=booking_id,
                        amount=amount,
                        status="COMPLETED" if success else "FAILED",
                    )
                )
        
        await session.commit()


    if success:
        logger.info("Pago COMPLETADO booking=%s monto=%d", booking_id, amount)
    else:
        logger.warning("Pago FALLIDO booking=%s motivo=%s", booking_id, reason)

    return success, reason



async def callback(message: aio_pika.IncomingMessage) -> None:
    async with message.process():
        payload = json.loads(message.body)
        booking_id = payload.get("booking_id")
        logger.info("Recibido booking.confirmed: %s", booking_id)


        success, reason = await process_event(payload)

        connection = await aio_pika.connect_robust(RABBITMQ_URL)
        async with connection:
            channel = await connection.channel()
            exchange = await channel.declare_exchange("hotel", aio_pika.ExchangeType.TOPIC)
            event = {
                **payload,
                "event": "PAYMENT_COMPLETED" if success else "PAYMENT_FAILED",
                "reason": reason,
            }
            routing_key = "payment.completed" if success else "payment.failed"
            await exchange.publish(
                aio_pika.Message(body=json.dumps(event).encode(), content_type="application/json"),
                routing_key=routing_key,
            )
            logger.info("Publicado %s para %s", routing_key, booking_id)


async def main() -> None:
    await init_db()
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    channel = await connection.channel()
    exchange = await channel.declare_exchange("hotel", aio_pika.ExchangeType.TOPIC)
    queue = await channel.declare_queue("payment.requests", durable=False)
    await queue.bind(exchange, routing_key="booking.confirmed")
    logger.info("payment-service esperando booking.confirmed...")
    await queue.consume(callback)
    await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
