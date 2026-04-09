"""availability-service – consumer que valida disponibilidad y crea reservas."""

import json
import logging
import os
from datetime import date

import pika

from .db import SessionLocal, init_db
from .models import Booking, Room

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger("availability-service")

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")


def find_available_room(room_type: str, check_in: date, check_out: date) -> Room | None:
    """Busca una habitación del tipo solicitado libre en el rango dado.

    Devuelve la primera habitación disponible o None si ninguna lo está.
    """
    with SessionLocal() as session:
        candidates = session.query(Room).filter(Room.room_type == room_type).all()
        for room in candidates:
            # BUG: la lógica de overlap está incompleta. Solo compara check_in
            # de las reservas existentes contra el check_in nuevo. Si una
            # reserva existe del 1 al 10 y entra una nueva del 5 al 15,
            # esta función dice "está libre" cuando NO lo está.
            #
            # Lo correcto: dos rangos [a1, a2] y [b1, b2] se solapan cuando
            # a1 < b2 AND a2 > b1. Reescribe el filtro de abajo aplicando
            # esa regla en SQL.
            #
            # BUG: además falta with_for_update() para prevenir race condition.
            # Si dos consumers leen al mismo tiempo, ambos pueden ver la
            # habitación libre y ambos insertan una reserva. El patrón correcto
            # es bloquear las filas relevantes dentro de la transacción.
            conflicts = (
                session.query(Booking)
                .filter(
                    Booking.room_id == room.id,
                    Booking.status == "CONFIRMED",
                    Booking.check_in == check_in,  # ← incompleto
                )
                .all()
            )
            if not conflicts:
                return room
        return None


def process_booking(payload: dict) -> tuple[bool, str, int | None]:
    booking_id = payload["booking_id"]
    room_type = payload["room_type"]
    check_in = date.fromisoformat(payload["check_in"])
    check_out = date.fromisoformat(payload["check_out"])

    with SessionLocal() as session:
        room = find_available_room(room_type, check_in, check_out)
        if room is None:
            logger.info("Reserva %s rechazada: sin habitaciones %s", booking_id, room_type)
            return False, f"No hay habitaciones {room_type} disponibles", None

        booking = Booking(
            booking_id=booking_id,
            room_id=room.id,
            guest=payload["guest"],
            check_in=check_in,
            check_out=check_out,
            status="CONFIRMED",
        )
        session.add(booking)
        session.commit()
        logger.info("Reserva %s confirmada en habitación %s", booking_id, room.room_number)
        return True, "", room.id


def callback(ch, method, properties, body):
    payload = json.loads(body)
    booking_id = payload["booking_id"]
    logger.info("Recibido booking.requested: %s", booking_id)

    try:
        success, reason, room_id = process_booking(payload)
        if success:
            event = {**payload, "event": "BOOKING_CONFIRMED", "room_id": room_id}
            routing_key = "booking.confirmed"
        else:
            event = {**payload, "event": "BOOKING_REJECTED", "reason": reason}
            routing_key = "booking.rejected"
        
        # Prueba para comprobar la lógica de reintento en caso de errores
        #raise Exception

        ch.basic_publish(
            exchange="hotel",
            routing_key=routing_key,
            body=json.dumps(event).encode(),
            properties=pika.BasicProperties(content_type="application/json"),
        )
        logger.info("Publicado %s para %s", routing_key, booking_id)
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as exc:
        logger.error("Error procesando %s: %s", booking_id, exc)
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
    


def main() -> None:
    init_db()
    params = pika.URLParameters(RABBITMQ_URL)
    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    channel.exchange_declare(exchange="hotel", exchange_type="topic")
    result = channel.queue_declare(queue="availability.requests", durable=False)
    channel.queue_bind(exchange="hotel", queue=result.method.queue, routing_key="booking.requested")

    # BUG: ack incorrecto. Con auto_ack=True, RabbitMQ marca el mensaje como
    # entregado ANTES de que el callback corra. Si crashea a la mitad, el
    # mensaje se pierde. Cambia a auto_ack=False y haz ch.basic_ack(delivery_tag=...)
    # manualmente al final del callback (o basic_nack en caso de error).
    channel.basic_consume(
        queue=result.method.queue,
        on_message_callback=callback,
        auto_ack=False,
    )
    logger.info("availability-service esperando booking.requested...")
    channel.start_consuming()


if __name__ == "__main__":
    main()
