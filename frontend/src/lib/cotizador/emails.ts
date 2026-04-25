import type { Email } from "./types";

// Los 5 emails reales del brief.
export const SAMPLE_EMAILS: Email[] = [
  {
    id: "EM-001",
    from: "psepulveda@ferreteriaeltornillo.cl",
    subject: "Cotización flete Santiago → La Serena",
    body: "Hola! Necesito cotizar un flete desde Santiago a La Serena. Son 4 pallets estándar, peso total 1.200 kg. Saldría mañana. Muchas gracias.",
    received_at: "2026-04-22T09:14:00-04:00",
  },
  {
    id: "EM-002",
    from: "rdiaz@distvinossur.cl",
    subject: "Cajas de vino al sur",
    body: "Buenos días, ¿cuánto me cobran por mandar unas cajas de vino al sur? Son harto, como 200 cajas. Urgente por favor.",
    received_at: "2026-04-22T10:02:00-04:00",
  },
  {
    id: "EM-003",
    from: "mgonzalez@supermercaderiascentral.cl",
    subject: "Cotización contrato semanal refrigerado",
    body: "Hola chicos, ¿pueden cotizarme 2 viajes semanales fijos? Ruta Valparaíso → La Serena, 8 pallets refrigerados cada viaje, saliendo martes y viernes 6am. Necesito precio mensual que incluya seguro de carga. Empezaríamos en mayo. Si tienen tarifa preferencial por contrato a 6 meses mejor.",
    received_at: "2026-04-22T11:30:00-04:00",
  },
  {
    id: "EM-004",
    from: "ventas@gpsrastreocl.com",
    subject: "Plataforma de rastreo GPS — descuento exclusivo",
    body: "Estimados Transportes La Serena, les escribimos para ofrecerles nuestra nueva plataforma de rastreo GPS con descuento exclusivo este mes. Tenemos 3 planes desde $45.000 CLP mensuales que incluyen alertas en tiempo real y reportes automáticos. ¿Cuándo podríamos agendar una reunión para mostrarles? Quedamos atentos. Saludos cordiales.",
    received_at: "2026-04-22T12:45:00-04:00",
  },
  {
    id: "EM-005",
    from: "bodega@ferreteriaeltornillo.cl",
    subject: "Seguimiento guía 4782",
    body: "Hola chicos! Mi pedido con guía de despacho 4782 ya debería haber llegado ayer a Coquimbo pero no tengo noticias. ¿Pueden consultar dónde está el camión? Urgente, el cliente final me está llamando. Gracias.",
    received_at: "2026-04-22T14:20:00-04:00",
  },
];
