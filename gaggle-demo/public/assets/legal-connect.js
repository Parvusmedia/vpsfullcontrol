/** Texto legal compartido: onboarding /conectar y página /terminos-conexion */
(function () {
  const LEGAL_HTML = `
<h2 class="h6 mt-4">1. Responsables y roles</h2>
<p class="small"><strong>Responsable del tratamiento</strong> de los datos que introduces en Ngaged (identificación, email corporativo y gestión de la invitación): <strong>Parvus Media S.L.U.</strong> (CIF B86670296), Calle Puerto Rico 4, 28220 Majadahonda (Madrid), España. Contacto privacidad: <a href="mailto:dpo@parvusmedia.com">dpo@parvusmedia.com</a>.</p>
<p class="small"><strong>Ngaged</strong> es la herramienta de <em>employee advocacy</em> que utiliza tu organización para proponerte campañas en LinkedIn (por ejemplo, repostear contenido corporativo). Tu empresa decide qué campañas recibes; Parvus Media opera la plataforma técnica en su nombre.</p>
<p class="small"><strong>Encargado del tratamiento / infraestructura de publicación:</strong> la conexión OAuth con LinkedIn y la publicación o amplificación técnica en la red pueden apoyarse en un <strong>proveedor externo especializado en gestión y publicación en redes sociales</strong>, que actúa bajo instrucciones de Parvus Media y únicamente para prestar el servicio. Ese proveedor trata tokens de acceso y datos de perfil/cuenta necesarios para conectar y operar LinkedIn, con obligaciones contractuales de confidencialidad y seguridad.</p>

<h2 class="h6 mt-4">2. Qué aceptas al vincular LinkedIn</h2>
<p class="small">Al marcar la casilla y pulsar «Acepto y continuar», declaras que:</p>
<ul class="small">
  <li>Has leído y aceptas estas condiciones y la <a href="https://parvusmedia.com/privacy/" target="_blank" rel="noopener">Política de privacidad de Parvus Media</a>.</li>
  <li>Autorizas a Ngaged (operado por Parvus Media) a iniciar el flujo de autorización de <strong>LinkedIn</strong> en tu nombre, para vincular tu perfil o cuenta autorizada y ejecutar las acciones que apruebes (p. ej. reposts) en el marco de las campañas de tu organización.</li>
  <li>Comprendes que <strong>LinkedIn</strong> aplica sus propias condiciones y políticas; al conectar, también quedas sujeto a los <a href="https://www.linkedin.com/legal/user-agreement" target="_blank" rel="noopener">Términos de usuario de LinkedIn</a> y a la <a href="https://www.linkedin.com/legal/privacy-policy" target="_blank" rel="noopener">Política de privacidad de LinkedIn</a>.</li>
  <li>Actúas como empleado o colaborador autorizado por tu organización y la información que facilitas es veraz.</li>
</ul>

<h2 class="h6 mt-4">3. Datos de LinkedIn y finalidades</h2>
<p class="small">Tras tu autorización OAuth, el sistema puede tratar, entre otros, identificadores de cuenta, nombre visible, imagen de perfil, tokens de acceso, metadatos de publicaciones y métricas necesarias para:</p>
<ul class="small">
  <li>mantener la conexión con LinkedIn;</li>
  <li>mostrarte campañas pendientes y registrar tu respuesta (repostear / ignorar);</li>
  <li>ejecutar reposts o acciones que apruebes;</li>
  <li>generar estadísticas agregadas para el administrador de tu organización (alcance, adopción).</li>
</ul>

<h2 class="h6 mt-4">4. Uso permitido y restricciones (LinkedIn)</h2>
<p class="small">Los datos obtenidos de LinkedIn a través de Ngaged se usan <strong>únicamente</strong> para las funciones de advocacy y gestión de campañas descritas. En particular, <strong>no</strong> se utilizarán para:</p>
<ul class="small">
  <li>crear o enriquecer bases de leads, recruiting, prospección comercial o publicidad fuera del servicio;</li>
  <li>combinar datos de LinkedIn con terceros para perfilar personas ajenas al servicio;</li>
  <li>vender, ceder o exportar datos de miembros de LinkedIn fuera de la plataforma, salvo obligación legal;</li>
  <li>mostrar un feed público externo de contenido de LinkedIn no autorizado.</li>
</ul>
<p class="small">Los datos se muestran solo a usuarios autorizados (tú, administradores de tu organización y personal técnico con necesidad de conocerlos).</p>

<h2 class="h6 mt-4">5. Conservación y seguridad</h2>
<p class="small">Conservamos los datos el tiempo necesario para prestar el servicio, cumplir obligaciones legales y resolver incidencias. Los tokens y datos de LinkedIn se almacenan con medidas técnicas y organizativas razonables (cifrado en tránsito, control de accesos). Puedes solicitar desvinculación a tu administrador o escribir a <a href="mailto:dpo@parvusmedia.com">dpo@parvusmedia.com</a>.</p>

<h2 class="h6 mt-4">6. Tus derechos</h2>
<p class="small">Puedes ejercer derechos de acceso, rectificación, supresión, oposición, limitación y portabilidad, cuando correspondan, contactando con <a href="mailto:dpo@parvusmedia.com">dpo@parvusmedia.com</a>. También puedes revocar la autorización en LinkedIn en cualquier momento. Si consideras que el tratamiento no cumple la normativa, puedes reclamar ante la <a href="https://www.aepd.es" target="_blank" rel="noopener">AEPD</a>.</p>

<h2 class="h6 mt-4">7. Limitación de responsabilidad</h2>
<p class="small">Ngaged se ofrece «tal cual» en el marco acordado con tu organización. Parvus Media no garantiza resultados concretos en LinkedIn ni la disponibilidad continua de APIs de terceros. En la medida permitida por la ley, Parvus Media no será responsable de daños indirectos derivados del uso de la integración.</p>

<h2 class="h6 mt-4">8. Cambios</h2>
<p class="small">Podemos actualizar estas condiciones. Si cambia la versión, deberás aceptarla de nuevo antes de seguir usando la vinculación.</p>

<h2 class="h6 mt-4">9. Legislación</h2>
<p class="small">Estas condiciones se rigen por la legislación española. Salvo fuero imperativo, los tribunales de Madrid serán competentes.</p>
`;

  window.NGAGED_CONNECT_LEGAL_HTML = LEGAL_HTML;

  document.addEventListener('DOMContentLoaded', function () {
    const el = document.getElementById('legal-body');
    if (el) el.innerHTML = LEGAL_HTML;
  });
})();
