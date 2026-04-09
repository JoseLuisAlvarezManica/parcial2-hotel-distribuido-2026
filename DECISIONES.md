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

**Cómo los implementé:**

**Decisiones de diseño que tomé:**

---

## Bugs arreglados (Tier 2)

### B4 — Overlap de fechas

### B5 — Race condition con `with_for_update()`

### B7 — Idempotencia

---

## Bonus que implementé (si aplica)

---

## Cosas que decidí NO hacer

(Ej: "no agregué tests porque preferí enfocarme en el flujo end-to-end", "no implementé saga porque no me dio tiempo", etc.)

---

## Si tuviera más tiempo, lo siguiente que mejoraría sería:
