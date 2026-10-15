# Guía rápida — formularios de leads en Meta (Digitanimal)

Al crear o duplicar un formulario, sigue estas reglas en **todos** los países.

**Empieza duplicando** el último formulario ya validado de ese país (o el patrón acordado con operaciones). No crees un formulario vacío salvo campaña nueva con campos distintos.

**Nombre del formulario:** termina siempre con el país: `_ES`, `_PT`, `_FR`, `_IT`, `_GR`, `_RO`, `_HR` o `_UK`. No preguntes el país dentro del formulario. El idioma que elijas en Meta **no** indica el mercado (p. ej. Italia puede estar en español latino).

**Texto visible:** idioma del ganadero. **Nombre interno del campo** (cuando Meta lo permita): inglés, minúsculas, sin tildes.

## Campos estándar


| Pregunta           | Cómo añadirla en Meta                                                      | Nombre del campo |
| ------------------ | -------------------------------------------------------------------------- | ---------------- |
| Email              | Tipo **Email** (no pregunta personalizada)                                 | `email`          |
| Teléfono           | Tipo **Phone number** (no “Número de teléfono” personalizado)              | `phone_number`   |
| Nombre y apellidos | Tipo **Full name** (también en Francia; no nombre y apellido por separado) | `full_name`      |
| Provincia / región | Tipo **Province** (no texto libre tipo “localización”)                     | `province`       |
| Tipo de ganado     | Personalizada, **opciones**                                                | `livestock_type` |
| N.º de animales    | Personalizada, **opciones** (tramos, no cifra libre)                       | `animal_count`   |


Opciones de **tipo de ganado** (texto traducido; claves internas si puedes fijarlas): bovino → `cattle`, ovino → `sheep`, caprino → `goats`, equino → `horses`, otros → `other`.

Opciones de **n.º de animales** (mismos tramos en todos los mercados): hasta 20 → `up_to_20`, 21–50 → `21_50`, 51–100 → `51_100`, más de 100 → `more_than_100`.

Solo en campañas concretas: `farm_size_ha`, `main_need` (regionales Italia), `devices_needed` (vallado), `self_employed_or_sme` (Kit Digital). Báscula puede usar otra escala de animales; indícalo al publicar.

## Antes de activar el anuncio

- [ ] Nombre del formulario con sufijo de país correcto.
- [ ] Contacto y provincia con los **tipos predefinidos** de la tabla (no duplicar email o teléfono con otra pregunta).
- [ ] Ganado y animales con nombres `livestock_type` y `animal_count`.
- [ ] Un **lead de prueba** y aviso al equipo con nombre e ID del formulario.
- [ ] Si sustituyes un formulario viejo, **archiva** el anterior cuando el nuevo esté en campaña.