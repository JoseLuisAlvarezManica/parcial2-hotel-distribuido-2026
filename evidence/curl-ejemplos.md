### Verificar el flujo end-to-end
curl -X POST http://localhost:8000/bookings \
  -H "Content-Type: application/json" \
  -d '{"guest": "Test", "room_type": "double", "check_in": "2026-05-01", "check_out": "2026-05-05"}'

# Checar flujo-completo.log para los logs

### Race condition
# Primer paso llenar una de los dos cuartos singles
curl -X POST http://localhost:8000/bookings -H "Content-Type: application/json" \
  -d '{"guest": "C", "room_type": "single", "check_in": "2026-06-01", "check_out": "2026-06-03"}'

# Segundo paso competir por los cuartos

curl -X POST http://localhost:8000/bookings -H "Content-Type: application/json" \
  -d '{"guest": "A", "room_type": "single", "check_in": "2026-06-01", "check_out": "2026-06-03"}' &
curl -X POST http://localhost:8000/bookings -H "Content-Type: application/json" \
  -d '{"guest": "B", "room_type": "single", "check_in": "2026-06-01", "check_out": "2026-06-03"}' &
wait

# terminal

luigi@MSI:~$ curl -X POST http://localhost:8000/bookings -H "Content-Type: application/json" \
  -d '{"guest": "C", "room_type": "single", "check_in": "2026-06-01", "check_out": "2026-06-03"}'
{"booking_id":"26abb74f-35d3-4a1e-9299-150f49300d1d","status":"REQUESTED"}luigi@MSI:~$
luigi@MSI:~$ curl -X POST http://localhost:8000/bookings -H "Content-Type: application/json" \
  -d '{"guest": "A", "room_type": "single", "check_in": "2026-06-01", "check_out": "2026-06-03"}' &
curl -X POST http://localhost:8000/bookings -H "Content-Type: application/json" \
  -d '{"guest": "B", "room_type": "single", "check_in": "2026-06-01", "check_out": "2026-06-03"}' &
wait
[1] 1002
[2] 1003
{"booking_id":"11e9ce32-5b2c-4b18-81c0-6c655726318c","status":"REQUESTED"}{"booking_id":"7623aa48-0bb1-40c2-bd05-ec0365f0f6e1","status":"REQUESTED"}[1]-  Done                    curl -X POST http://localhost:8000/bookings -H "Content-Type: application/json" -d '{"guest": "A", "room_type": "single", "check_in": "2026-06-01", "check_out": "2026-06-03"}'

# Logs
*Se puede ver 2 notificacitions, uno del primer curl y otro donde al competir solo paso una de las reservaciones*

payment-service-1       | 2026-04-10 18:02:17,818 payment-service INFO Recibido booking.confirmed: 26abb74f-35d3-4a1e-9299-150f49300d1d


booking-api-1           | 2026-04-10 18:02:17,808 booking-api.publisher INFO Evento publicado: booking_id=26abb74f-35d3-


availability-service-1  | 2026-04-10 18:02:17,817 availability-service INFO Reserva 26abb74f-35d3-4a1e-9299-150f49300d1d confirmada en habitación 101

booking-api-1           | INFO:     172.18.0.1:39658 - "POST /bookings HTTP/1.1" 202 Accepted
availability-service-1  | 2026-04-10 18:02:17,817 availability-service INFO Publicado booking.confirmed para 26abb74f-35d3-4a1e-9299-150f49300d1d

payment-service-1       | 2026-04-10 18:02:18,110 payment-service INFO Pago COMPLETADO booking=26abb74f-35d3-4a1e-9299-150f49300d1d monto=800
notification-service-1  | 2026-04-10 18:02:18,117 notification-service INFO [NOTIFICATION] booking_id=26abb74f-35d3-4a1e-9299-150f49300d1d event=PAYMENT_COMPLETED guest=C channel=email status=SENT


payment-service-1       | 2026-04-10 18:02:18,116 payment-service INFO Publicado payment.completed para 26abb74f-35d3-4a1e-9299-150f49300d1d

booking-api-1           | 2026-04-10 18:02:37,925 booking-api INFO Nueva reserva 11e9ce32-5b2c-4b18-81c0-6c655726318c para B
availability-service-1  | 2026-04-10 18:02:37,932 availability-service INFO Recibido booking.requested: 7623aa48-0bb1-40c2-bd05-ec0365f0f6e1

payment-service-1       | 2026-04-10 18:02:37,938 payment-service INFO Recibido booking.confirmed: 7623aa48-0bb1-40c2-bd05-ec0365f0f6e1

booking-api-1           | 2026-04-10 18:02:37,925 booking-api INFO Nueva reserva 7623aa48-0bb1-40c2-bd05-ec0365f0f6e1 para A

availability-service-1  | 2026-04-10 18:02:37,937 availability-service INFO Reserva 7623aa48-0bb1-40c2-bd05-ec0365f0f6e1 confirmada en habitación 102
booking-api-1           | 2026-04-10 18:02:37,931 booking-api.publisher INFO Evento publicado: booking_id=11e9ce32-5b2c-4b18-81c0-6c655726318c

availability-service-1  | 2026-04-10 18:02:37,937 availability-service INFO Publicado booking.confirmed para 7623aa48-0bb1-40c2-bd05-ec0365f0f6e1

booking-api-1           | 2026-04-10 18:02:37,931 booking-api.publisher INFO Evento publicado: booking_id=7623aa48-0bb1-40c2-bd05-ec0365f0f6e1
rabbitmq-1              | 2026-04-10 18:02:37.929475+00:00 [info] <0.1010.0> connection <0.1010.0> (172.18.0.8:56566 -> 172.18.0.4:5672): user 'guest' authenticated and granted access to vhost '/'
availability-service-1  | 2026-04-10 18:02:37,937 availability-service INFO Recibido booking.requested: 11e9ce32-5b2c-4b18-81c0-6c655726318c
booking-api-1           | INFO:     172.18.0.1:46524 - "POST /bookings HTTP/1.1" 202 Accepted

availability-service-1  | 2026-04-10 18:02:37,939 availability-service INFO Reserva 11e9ce32-5b2c-4b18-81c0-6c655726318c

availability-service-1  | 2026-04-10 18:02:37,939 availability-service INFO Publicado booking.rejected para 11e9ce32-5b2c-4b18-81c0-6c655726318c

booking-api-1           | INFO:     172.18.0.1:46528 - "POST /bookings HTTP/1.1" 202 Accepted

payment-service-1       | 2026-04-10 18:02:38,384 payment-service INFO Pago COMPLETADO booking=7623aa48-0bb1-40c2-bd05-ec0365f0f6e1 monto=800

notification-service-1  | 2026-04-10 18:02:38,390 notification-service INFO [NOTIFICATION] booking_id=7623aa48-0bb1-40c2-bd05-ec0365f0f6e1 event=PAYMENT_COMPLETED guest=A channel=email status=SENT


### Overlap
# Se eligio suite por que solo tiene un cuarto.

curl -X POST http://localhost:8000/bookings -H "Content-Type: application/json" \
  -d '{"guest": "A", "room_type": "suite", "check_in": "2026-06-01", "check_out": "2026-06-03"}'

curl -X POST http://localhost:8000/bookings -H "Content-Type: application/json" \
  -d '{"guest": "B", "room_type": "suite", "check_in": "2026-06-02", "check_out": "2026-06-04"}'

# Terminal

luigi@MSI:~$ curl -X POST http://localhost:8000/bookings -H "Content-Type: application/json" \
  -d '{"guest": "A", "room_type": "suite", "check_in": "2026-06-01", "check_out": "2026-06-03"}'
{"booking_id":"c29471b6-0e24-4410-8e5f-e68a445e2550","status":"REQUESTED"}luigi@MSI:~$
luigi@MSI:~$ curl -X POST http://localhost:8000/bookings -H "Content-Type: application/json" \
  -d '{"guest": "B", "room_type": "suite", "check_in": "2026-06-02", "check_out": "2026-06-04"}'
{"booking_id":"e7dd1a05-7a9c-49a6-9aa9-9df0e04c7527","status":"REQUESTED"}luigi@MSI:~$

# Logs

booking-api-1           | 2026-04-10 18:11:56,017 booking-api INFO Nueva reserva c29471b6-0e24-4410-8e5f-e68a445e2550 para A
availability-service-1  | 2026-04-10 18:11:56,025 availability-service INFO Recibido booking.requested: c29471b6-0e24-4410-8e5f-e68a445e2550

payment-service-1       | 2026-04-10 18:11:56,036 payment-service INFO Recibido booking.confirmed: c29471b6-0e24-4410-8e5f-e68a445e2550
availability-service-1  | 2026-04-10 18:11:56,035 availability-service INFO Reserva c29471b6-0e24-4410-8e5f-e68a445e2550 confirmada en habitación 301
booking-api-1           | 2026-04-10 18:11:56,024 booking-api.publisher INFO Evento publicado: booking_id=c29471b6-0e24-4410-8e5f-e68a445e2550


booking-api-1           | INFO:     172.18.0.1:57906 - "POST /bookings HTTP/1.1" 202 Accepted
availability-service-1  | 2026-04-10 18:11:56,035 availability-service INFO Publicado booking.confirmed para c29471b6-0e24-4410-8e5f-e68a445e2550



payment-service-1       | 2026-04-10 18:11:56,485 payment-service INFO Pago COMPLETADO booking=c29471b6-0e24-4410-8e5f-e68a445e2550 monto=3200
notification-service-1  | 2026-04-10 18:11:56,491 notification-service INFO [NOTIFICATION] booking_id=c29471b6-0e24-4410-8e5f-e68a445e2550 event=PAYMENT_COMPLETED guest=A channel=email status=SENT


payment-service-1       | 2026-04-10 18:11:56,491 payment-service INFO Publicado payment.completed para c29471b6-0e24-4410-8e5f-e68a445e2550

availability-service-1  | 2026-04-10 18:12:03,341 availability-service INFO Recibido booking.requested: e7dd1a05-7a9c-49a6-9aa9-9df0e04c7527
booking-api-1           | 2026-04-10 18:12:03,335 booking-api INFO Nueva reserva e7dd1a05-7a9c-49a6-9aa9-9df0e04c7527 para B

booking-api-1           | 2026-04-10 18:12:03,341 booking-api.publisher INFO Evento publicado: booking_id=e7dd1a05-7a9c-49a6-9aa9-9df0e04c7527
booking-api-1           | INFO:     172.18.0.1:57908 - "POST /bookings HTTP/1.1" 202 Accepted.rejected para e7dd1a05-7a9


