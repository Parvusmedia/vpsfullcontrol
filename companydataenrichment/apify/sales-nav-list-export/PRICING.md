# Pricing: fijo (seat Unipile) + uso (lead con perfil Harvest)

Modelo para el Actor y para **CompanyDataEnrichment** — export SN con **perfil completo (Harvest)**, **sin email**.

## Costes de proveedor

| Proveedor | Modelo | Orden de magnitud |
|-----------|--------|-------------------|
| **Unipile** | Fijo por cuenta conectada (pico mes) | €49/mes hasta 10 seats |
| **Harvest** | Por perfil/empresa consultados | Variable según plan HarvestAPI |
| **Email** | — | **No incluido en este actor** |

## Modelo comercial

```
Total ≈ SeatFee (fijo) + (leads × precio/lead enriquecido)
```

Un solo precio por lead — **ya incluye** lista SN + perfil Harvest completo. No hay tier Basic/Mail en Apify.

### 1. Fijo — seat LinkedIn (Unipile)

| Escenario | SeatFee sugerido |
|-----------|------------------|
| Pool compartido (&lt;10 seats / org) | **€19–29/mes** por cuenta |
| Seat dedicado | **€59–79/mes** |
| BYO Unipile (solo Actor) | €0 fijo en tu checkout |

### 2. Variable — por lead exportado (perfil completo)

Equivalente al tier **Enriched** de CDE (Basic + Harvest), no al add-on Mail:

| Referencia CDE | €/lead |
|----------------|--------|
| Basic + Enriched (~1 + 0,4 créditos) | ~**€0,07** retail |
| Pack volumen | ~**€0,03–0,05** |

**Precio público recomendado (Actor / CDE Enriched):**

| Concepto | Precio/lead |
|----------|-------------|
| Lead con perfil completo (Harvest) | **€0,06–0,08** |
| Solo en CDE web, add-on Mail | +€0,05/email *(fuera del actor)* |

Calibración: cubrir **Unipile amortizado + coste Harvest por perfil + margen Apify/compute**.

### 3. Ejemplos

**SMB** — seat €25/mes, 500 leads/mes con perfil completo:

- Fijo: €25  
- Variable: 500 × €0,07 = €35  
- **Total: €60/mes**

**Power** — seat €29, 3.000 leads:

- Fijo: €29  
- Variable: 3.000 × €0,04 ≈ €120  
- **Total: ~€149/mes**

## Apify Store (PPE)

Sin rental mensual. Simular fijo + uso:

| Evento | Rol | Precio orientativo |
|--------|-----|-------------------|
| `export-run` | Arranque + seat amortizado | **$3–6** / run |
| `lead-enriched` | 1 lead con perfil Harvest | **$0,05–0,08** / lead |

No crear evento `email-found` — este actor no lo usa.

## CDE vs Actor

| | CDE panel | Actor Apify |
|--|-----------|-------------|
| Export SN | Unipile | Unipile |
| Perfil completo | Harvest (tier Enriched) | Harvest (siempre) |
| Email | Tier Mail opcional | **No** |
| Cobro | Stripe seat + créditos | PPE o tu API |

## Resumen

1. **Un precio por lead enriquecido** — no cobrar Basic barato y Harvest aparte en Store.  
2. **Email fuera de scope** del actor Apify.  
3. **Seat fijo** cubre Unipile; **variable** cubre Harvest + margen.  
4. En CDE podéis seguir con tiers Basic / Enriched / Mail en web; el actor = siempre Enriched.
