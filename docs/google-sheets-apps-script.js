/**
 * Google Sheets Web App para registrar resultados del mini-cotizador.
 *
 * Pasos:
 * 1. Crea un Google Sheet.
 * 2. Extensions -> Apps Script.
 * 3. Pega este archivo.
 * 4. Cambia DATA_SHEET_NAME si quieres.
 * 5. Deploy -> New deployment -> Web app.
 * 6. Execute as: Me. Who has access: Anyone with the link.
 * 7. Copia la Web App URL y usala como COTIZADOR_GOOGLE_SHEETS_WEBHOOK_URL.
 */

const DATA_SHEET_NAME = "cotizador_jaiar_labs";
const SUMMARY_SHEET_NAME = "resumen";

const DATA_HEADERS = [
  "timestamp",
  "email_id",
  "sender",
  "classification",
  "action",
  "quote_total_clp",
  "contract_total_clp",
  "missing_fields",
  "reason",
  "response",
];

const SUMMARY_HEADERS = ["metric", "value"];

function doPost(e) {
  const payload = JSON.parse(e.postData.contents);
  const dataSheet = getSheet_(DATA_SHEET_NAME, DATA_HEADERS);
  dataSheet.appendRow([
    new Date(),
    payload.email_id || "",
    payload.sender || "",
    payload.classification || "",
    payload.action || "",
    payload.quote_total_clp || "",
    payload.contract_total_clp || "",
    payload.missing_fields || "",
    payload.reason || "",
    payload.response || "",
  ]);

  updateSummary_(dataSheet);

  return ContentService
    .createTextOutput(JSON.stringify({ ok: true }))
    .setMimeType(ContentService.MimeType.JSON);
}

function getSheet_(sheetName, headers) {
  const spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
  let sheet = spreadsheet.getSheetByName(sheetName);
  if (!sheet) {
    sheet = spreadsheet.insertSheet(sheetName);
  }

  if (sheet.getLastRow() === 0) {
    sheet.appendRow(headers);
  }

  return sheet;
}

function updateSummary_(dataSheet) {
  const summarySheet = getSheet_(SUMMARY_SHEET_NAME, SUMMARY_HEADERS);
  const rows = getDataRows_(dataSheet);
  const totalEmails = rows.length;
  const quoteRows = rows.filter((row) => row[4] === "reply_with_quote");
  const incompleteRows = rows.filter((row) => row[4] === "reply_request_missing_quote_data");
  const filteredRows = rows.filter((row) =>
    ["archive_supplier_offer_and_notify_admin", "forward_to_operations_tracking_queue", "archive_no_quote"].includes(row[4])
  );
  const quoteAmount = quoteRows.reduce((sum, row) => sum + toNumber_(row[5]), 0);
  const lastProcessedAt = totalEmails > 0 ? rows[totalEmails - 1][0] : "";

  summarySheet.clearContents();
  summarySheet.appendRow(SUMMARY_HEADERS);
  summarySheet.appendRow(["Total emails procesados", totalEmails]);
  summarySheet.appendRow(["Cotizaciones generadas", quoteRows.length]);
  summarySheet.appendRow(["Monto total cotizado CLP", quoteAmount]);
  summarySheet.appendRow(["Solicitudes incompletas", incompleteRows.length]);
  summarySheet.appendRow(["Emails filtrados", filteredRows.length]);
  summarySheet.appendRow(["Fecha del ultimo procesamiento", lastProcessedAt]);
}

function getDataRows_(sheet) {
  const lastRow = sheet.getLastRow();
  if (lastRow <= 1) {
    return [];
  }
  return sheet.getRange(2, 1, lastRow - 1, DATA_HEADERS.length).getValues();
}

function toNumber_(value) {
  if (value === "" || value === null || value === undefined) {
    return 0;
  }
  return Number(value) || 0;
}
