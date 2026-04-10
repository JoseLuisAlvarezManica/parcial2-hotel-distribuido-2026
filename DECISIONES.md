# Decisiones técnicas

> Documenten brevemente las decisiones que tomaron resolviendo el examen. No copien del enunciado: expliquen con sus palabras qué hicieron y por qué. La intención es que al revisar pueda entender el razonamiento, no que repitan el problema.

---

## Bugs arreglados (Tier 1)

### B1 — Routing key
José Álvarez
**Qué encontré:**
En el servicio booking-api, bajo el documento rabbitmq.py, el routing key era `booking.created`; en cambio, en availability-service, dentro del main.py, este era `booking.requested`.

**Cómo lo arreglé:**
La manera más sencilla de arreglarlo es que las llaves coincidan, por lo cual decidí que `booking.requested` era la que más lógica tenía dentro del contexto de ambas.

**Por qué esto era un problema:**
Dentro de un exchange en RabbitMQ, las routing keys determinan cuándo un mensaje es recibido por un subscriber. La routing key del mensaje de un productor debe coincidir con la de un consumidor; si no coinciden, el subscriber nunca lo recibiría.

---

### B2 — Manejo de error en publish
José Álvarez
**Qué encontré:**
Dentro del POST para el endpoint `/bookings` en `booking-api` no existía una lógica que respaldara la operación en caso de errores. Esto tiene relevancia en una función que publica asincrónamente a RabbitMQ.

**Cómo lo arreglé:**
Se encapsuló en un `try` la función `publish_booking`, permitiendo que, en caso de error, se pueda crear una excepción en la cual se registre el problema para un desarrollador y se indique al usuario que un servicio no está disponible (503).

**Por qué esto era un problema:**
Porque al no tener una lógica para manejar los posibles errores, siempre se indicaba que la operación era exitosa para el usuario, y no se avisaba ni alertaba a un desarrollador que el servicio de RabbitMQ no estaba disponible y que era necesario tomar acción para corregirlo.

---

### B3 — Ack manual
José Álvarez
**Qué encontré:**
Que el consumer para la routing key `booking.requested` mandaba automáticamente una confirmación al recibir un mensaje.

**Cómo lo arreglé:**
Le indiqué al consumer que no mandara automáticamente las confirmaciones, revisé el callback relacionado y detecté que la confirmación manual tenía que realizarse después de la publicación en el callback. A su vez, se incluyó en caso de error un `nack` para que RabbitMQ vuelva a enviar el mensaje y se repita el proceso. Para probarlo temporalmente puse un raise exception al inicio del callback y vi que se repitiera el mensaje de error del servicio.

**Por qué esto era un problema:**
Al mandar la confirmación de manera automática no se protegía el programa de posibles errores. Imagina que una reserva no es enviada al servicio de pagos o no es rechazada correctamente; esto implicaría que el mensaje se pierde y la petición termina incompleta dentro del sistema.

---

### B6 — Credenciales en env vars
José Álvarez
**Qué encontré:**  
La ruta para conectarse a la base de datos estaba expuesta, demostrando las credenciales necesarias (usuario, contraseña, nombre de la base de datos y el host) para que un agente malicioso pueda acceder a ella.

**Cómo lo arreglé:**  
Basándome en cómo se implementó la creación de la URL en `availability-service`, la recreé en `payment-service`, considerando que este último utiliza `asyncpg` en lugar de `psycopg2`.

**Por qué esto era un problema:**  
Aunque puede existir un valor predeterminado en caso de pruebas (pues en `availability-service` existen si no se obtienen del env), al desplegar la aplicación, tener el enlace expuesto dentro del código representa un peligro, ya que se está revelando información sensible y, en este caso, se está exponiendo la base de datos a cambios y ataques directos a través de un punto de acceso confirmado.

---

## notification-service completado

**Qué TODOs había:**
TODO 1: Configurar adecuadamente el consumidor de RabbitMQ
TODO 2: Crear la lógica de negocio dentro del callback
TODO 3: Iniciar el consumer adecuadamente

**Cómo los implementé:**
TODO 1 y 3: Primero copié de payment service la lógica del main, consideré qué era necesario y qué estaba de más. Con lo que quedó, lo adapté según las especificaciones que requería el notification service (exchange = hotel, queue = notifications) y dupliqué el bind de la queue asignándoles sus routing keys respectivas (payment.completed y payment.failed).

TODO 2: Basándome en el callback de payment service, creé una función en la cual se decodificaban del JSON los parámetros relevantes a la notificación y se guardaban en variables. Seguido, se creó el log de la notificación con el formato adecuado y la confirmación del ack. Se decidió, por precaución, envolver lo anterior en un try/except donde se indicara en el except que hubo un error al notificar y se creara un nack.

**Decisiones de diseño que tomé:**
En el TODO 2, como mencioné, decidí agregar adicionalmente un try/except para poder indicar si hubo algún error y descartar el mensaje sin reencolarlo. Esto último fue un dilema, dado que la sencillez de la tarea me hizo cuestionarme si debía no reencolar los mensajes en caso de un nack, pues algo tendría que haber salido muy mal para que esta tarea sencilla fracasara.

---

## Bugs arreglados (Tier 2)

### B4 — Overlap de fechas

### B5 — Race condition con `with_for_update()`

### B7 — Idempotencia
José Álvarez
**Qué encontré:**  
Siendo sincero, no sé si lo habría notado sin la documentación. Pero similar a la situación del ACK manual anterior, si el proceso de registro de pago falla antes de finalizar se crea un problema: al reiniciar el proceso se vuelve a intentar cobrar al individuo al no tener una comprobación antes del cobro.

**Cómo lo arreglé:**  
Se creó en el archivo `db.py` la tabla `processed_events`, la cual solo guarda una llave primaria (el booking ID que se maneja en payment). En el archivo `main.py` se editó la función `process_event`, a la cual se le agregó una comprobación que busca si ya existe en la base de datos un `processed_event` con el ID del booking. En caso de encontrarlo, consulta la tabla `Payment` para identificar el estado de la operación y retornar si el pago se realizó con éxito (se asume que RabbitMQ no envió el mensaje a `payment.completed` o `payment.failed`). En caso de no encontrarlo, procede a registrar el evento y el pago en la base de datos.

**Por qué esto era un problema:**  
Si el flujo falla antes de poder realizar el ACK, el evento se registra en la base de datos pero el proceso se interrumpe. Esto causa varios problemas: es muy probable que no se haya enviado el mensaje correspondiente a RabbitMQ, y además se cobraría más de una vez al individuo, generando registros duplicados en la tabla `Payment`.
---

## Bonus que implementé (si aplica)

---

## Cosas que decidí NO hacer

(Ej: "no agregué tests porque preferí enfocarme en el flujo end-to-end", "no implementé saga porque no me dio tiempo", etc.)

---

## Si tuviera más tiempo, lo siguiente que mejoraría sería:
