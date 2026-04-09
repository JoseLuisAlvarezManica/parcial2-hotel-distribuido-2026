"""booking-api – punto de entrada HTTP para reservas de hotel."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException

from .config import settings  # noqa: F401
from .rabbitmq import publish_booking
from .redis_client import get_redis
from .schemas import BookingCreated, BookingIn, BookingStatus

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger("booking-api")

app = FastAPI(title="HotelBook – Booking API")


@app.post("/bookings", response_model=BookingCreated, status_code=202)
async def create_booking(body: BookingIn):
    """Crea una solicitud de reserva y la publica al broker."""
    if body.check_out <= body.check_in:
        raise HTTPException(
            status_code=400, detail="check_out debe ser posterior a check_in"
        )

    booking_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    logger.info("Nueva reserva %s para %s", booking_id, body.guest)

    r = get_redis()
    await r.hset(
        f"booking:{booking_id}",
        mapping={"status": "REQUESTED", "last_update": now},
    )

    payload = {
        "booking_id": booking_id,
        "guest": body.guest,
        "room_type": body.room_type,
        "check_in": body.check_in.isoformat(),
        "check_out": body.check_out.isoformat(),
    }

    # BUG: maneja el fallo del publish. Si RabbitMQ está caído, el cliente
    # recibe un 202 OK aunque el evento nunca salió. Debes envolver esto en
    # try/except, loggear el error, y devolver 503 al cliente.
    try:
        await publish_booking(payload)
    except Exception as e:
        logger.error("Error publicando la reserva: %s. Error: %s", booking_id, e)
        raise HTTPException(status_code=503, detail="Error al publicar la reserva.")


    await r.aclose()
    return BookingCreated(booking_id=booking_id, status="REQUESTED")


@app.get("/bookings/{booking_id}", response_model=BookingStatus)
async def get_booking(booking_id: str):
    r = get_redis()
    data = await r.hgetall(f"booking:{booking_id}")
    await r.aclose()

    if not data:
        raise HTTPException(status_code=404, detail="Reserva no encontrada")

    return BookingStatus(
        booking_id=booking_id,
        status=data.get("status", "UNKNOWN"),
        last_update=data.get("last_update", ""),
        reason=data.get("reason"),
    )


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}
