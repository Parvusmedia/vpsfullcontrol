/**
 * Digitanimal-Campaigns — JSON para el panel (una sola vez).
 * 1. Extensiones → Apps Script → pegar este archivo → Guardar
 * 2. Implementar → Nueva implementación → Aplicación web
 *    - Ejecutar como: Yo
 *    - Quién tiene acceso: Cualquier usuario (la URL actúa como secreto)
 * 3. Copiar URL de la web app → secreto DIGITANIMAL_SHEETS_JSON_URL en Cursor
 */
const SPREADSHEET_ID = "1fVVnw2jfny74kz15VGA6nmSHXpdjBQBfMa5cO1vbIHM";

function sheetToObjects_(sheetName) {
  const sh = SpreadsheetApp.openById(SPREADSHEET_ID).getSheetByName(sheetName);
  if (!sh) return [];
  const values = sh.getDataRange().getValues();
  if (values.length < 2) return [];
  const headers = values[0].map(function (h) {
    return String(h || "").trim();
  });
  return values.slice(1).map(function (row) {
    const o = {};
    headers.forEach(function (h, i) {
      if (h) o[h] = row[i];
    });
    return o;
  });
}

function doGet() {
  const payload = {
    updatedAt: new Date().toISOString(),
    cumplimiento: sheetToObjects_("cumplimiento"),
    presupuesto_activacion: sheetToObjects_("presupuesto_activacion"),
  };
  return ContentService.createTextOutput(JSON.stringify(payload)).setMimeType(
    ContentService.MimeType.JSON
  );
}
