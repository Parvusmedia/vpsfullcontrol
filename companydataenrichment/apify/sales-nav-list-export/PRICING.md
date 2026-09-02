# Pricing: fijo (seat Unipile) + uso (por lead)

Modelo recomendado para **CompanyDataEnrichment** y, si aplica, para el Actor en Apify Store.

## Coste base (Unipile)

Unipile **no cobra por request** — cobra por **cuenta conectada** (pico del mes):

| Cuentas vinculadas (pico) | Coste Unipile |
|---------------------------|---------------|
| 1–10 | **€49/mes** (flat) |
| 11–50 | €5/cuenta/mes (sobre el mínimo) |

Implicación: hasta que no tengas ~10 clientes compartiendo la misma org Unipile, el coste fijo real por “seat” es alto si solo hay 1–2 cuentas (pagas €49 igual).

## Modelo comercial propuesto

```
Total mensual ≈ SeatFee + (leads exportados × precio/lead) + add-ons
```

### 1. Fijo — “SN seat” (cubre Unipile + conexión + panel)

| Escenario | SeatFee sugerido | Por qué |
|-----------|------------------|---------|
| **Pool compartido** (varios clientes en 1 org Unipile, &lt;10 seats) | **€19–29/mes** por cuenta LinkedIn conectada | €49/10 ≈ €4,9/cuenta + margen + soporte |
| **Seat dedicado** (1 org Unipile por cliente enterprise) | **€59–79/mes** | Cubre mínimo €49 Unipile + margen |
| **Sin seat** (BYO Unipile — solo Actor Apify) | **€0 fijo** | El usuario paga Unipile directamente |

El seat incluye: conexión LinkedIn/SN vía hosted auth, reconexión, estado en panel, **sin** incluir leads exportados.

### 2. Variable — por lead exportado

Alineado con créditos CDE actuales (1 crédito ≈ 1 lead basic):

| Pack CDE (referencia) | €/lead efectivo |
|-----------------------|-----------------|
| €20 → 240 créditos | ~€0,083 |
| €29 → 600 créditos | ~€0,048 |
| €49 → 1.800 créditos | ~€0,027 |
| €99 → 4.800 créditos | ~€0,021 |

**Precio público recomendado (simple):**

| Tier | Precio/lead |
|------|-------------|
| Basic export | **€0,05** (o 1 crédito) |
| + Enriched | **+€0,02** (+40% → coherente con `_credits.php`) |
| + Email (cuando exista) | **+€0,05** por email encontrado |

### 3. Ejemplos

**Cliente SMB** — seat pool €25/mes, 800 leads/mes basic:

- Fijo: €25  
- Variable: 800 × €0,05 = €40  
- **Total: €65/mes**  
- Tu coste Unipile (si es 1 de 8 seats en pool): ~€6,1 amortizado + margen amplio

**Cliente solo** — 1 cuenta en org vacía, 200 leads/mes:

- Fijo mínimo: **€59** (cubre €49 Unipile)  
- Variable: 200 × €0,05 = €10  
- **Total: €69/mes**

**Power user** — €29 seat, 5.000 leads con pack volumen:

- Fijo: €29  
- Variable: 5.000 × €0,027 ≈ €135 (pack €99 + recargas)  
- **Total: ~€164/mes**

## Dónde cobrar: CDE (Stripe) vs Apify Store

### Recomendado: **CDE + Stripe** (fijo + uso)

| Componente | Cómo cobrar |
|------------|-------------|
| Seat mensual | Stripe Subscription (`price_..._seat_monthly`) |
| Leads | Créditos prepago (ya implementado) o metered billing Stripe |

Ventajas: control total, fijo mensual real, mismo flujo que el panel actual.

### Apify Store: simular fijo + uso con **Pay-Per-Event (PPE)**

Apify **retira el modelo rental** (cuota fija mensual en Store). El equivalente es:

| Evento PPE | Rol | Precio orientativo |
|------------|-----|-------------------|
| `export-run` | Sustituye el “fijo” **por ejecución** | **$2–5** / run |
| `lead-exported` | Uso | **$0,03–0,05** / lead |

Fórmula para calibrar `export-run`:

```
export-run ≈ (SeatFee_mensual / runs_mes_esperados) × 1.2
```

Ejemplo: seat €29/mes, ~6 exports/mes → $5/run + $0.04/lead.

**Actor managed** (tú pones Unipile): ambos eventos.  
**BYO Unipile**: solo `lead-exported` (o precio más bajo en `export-run`).

Implementación en código (cuando publiques):

```js
const charging = Actor.getChargingManager();
if (charging.getPricingInfo().isPayPerEvent) {
  await Actor.charge({ eventName: 'export-run' });
}
// por cada lead:
await dataset.pushData(row);
if (charging.getPricingInfo().isPayPerEvent) {
  await Actor.charge({ eventName: 'lead-exported' });
}
```

## Resumen ejecutivo

1. **No publiques solo pay-per-lead** si tú pagas Unipile — pierdes en clientes de bajo volumen.  
2. **Fijo = seat LinkedIn**; **variable = leads** (créditos).  
3. **CDE** es el lugar natural para el fijo mensual; **Apify PPE** solo si quieres canal Store/API sin tu checkout.  
4. Hasta llenar el pool de 10 cuentas Unipile, prioriza **subir SeatFee** o **agrupar clientes** en una org.

## Próximo paso en producto

- [ ] Stripe: producto `SN Seat` recurrente (€25–29 pool / €69 dedicado)  
- [ ] Panel: bloquear export si seat inactivo o sin créditos  
- [ ] Actor Apify: eventos PPE `export-run` + `lead-exported` (opcional)  
- [ ] Página pricing pública con tabla fijo + uso
