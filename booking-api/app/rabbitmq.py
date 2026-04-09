"""Publicador de eventos al exchange 'hotel'."""

from __future__ import annotations

import json
import logging

import aio_pika

from .config import settings

logger = logging.getLogger("booking-api.publisher")


async def publish_booking(payload: dict) -> None:
    """Publica un evento booking.requested al exchange topic 'hotel'."""
    connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    async with connection:
        channel = await connection.channel()
        exchange = await channel.declare_exchange(
            "hotel", aio_pika.ExchangeType.TOPIC
        )
        message = aio_pika.Message(
            body=json.dumps(payload).encode(),
            content_type="application/json",
        )
        # BUG: revisa el routing key. El availability-service espera otro nombre.
        await exchange.publish(message, routing_key="booking.requested")
        logger.info("Evento publicado: booking_id=%s", payload.get("booking_id"))
