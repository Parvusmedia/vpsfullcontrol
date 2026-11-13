/** Política de privacidad Ngaged (responsable: Parvus Media S.L.U.) */
(function () {
  const PRIVACY_HTML = `
<h2 class="h6 mt-4">1. Responsable del tratamiento</h2>
<p class="small"><strong>Ngaged</strong> es un servicio de employee advocacy operado por:</p>
<ul class="small">
  <li><strong>Parvus Media S.L.U.</strong></li>
  <li>CIF: <strong>B86670296</strong></li>
  <li>Domicilio: Calle Puerto Rico 4, 28220 Majadahonda (Madrid), España</li>
  <li>Correo general: <a href="mailto:hello@parvusmedia.com">hello@parvusmedia.com</a></li>
  <li>Contacto privacidad / DPO: <a href="mailto:dpo@parvusmedia.com">dpo@parvusmedia.com</a></li>
</ul>
<p class="small">Tu organización (empleador o cliente) utiliza Ngaged para proponerte campañas en LinkedIn. Parvus Media trata los datos personales necesarios para prestar la plataforma en nombre de esa organización y conforme a sus instrucciones operativas.</p>

<h2 class="h6 mt-4">2. Ámbito</h2>
<p class="small">Esta política se aplica al tratamiento de datos personales en el contexto de <strong>Ngaged</strong>: invitaciones de vinculación, panel de administración, emails de campaña, conexión con LinkedIn y métricas de adopción. No sustituye las políticas de LinkedIn ni de otros servicios que autorices por separado.</p>

<h2 class="h6 mt-4">3. Datos que tratamos</h2>
<p class="small">Según el uso del servicio, podemos tratar:</p>
<ul class="small">
  <li><strong>Identificación y contacto:</strong> nombre, email corporativo, identificadores internos de miembro.</li>
  <li><strong>Cuenta LinkedIn vinculada:</strong> identificadores de cuenta, nombre visible, URL o imagen de perfil, tokens de acceso y metadatos necesarios para mantener la conexión.</li>
  <li><strong>Actividad en campañas:</strong> envíos, respuestas (repostear / ignorar), fechas, métricas agregadas de adopción.</li>
  <li><strong>Técnicos y seguridad:</strong> dirección IP (p. ej. hash para registro de aceptación legal), logs, cookies o almacenamiento local estrictamente necesarios para el funcionamiento.</li>
  <li><strong>Contenido de campañas:</strong> URLs, textos sugeridos y metadatos de publicaciones corporativas que tu organización comparte contigo.</li>
</ul>
<p class="small">No solicitamos categorías especiales de datos (salud, ideología, etc.) para prestar Ngaged.</p>

<h2 class="h6 mt-4">4. Finalidades y bases legales</h2>
<ul class="small">
  <li><strong>Prestación del servicio</strong> (invitaciones, vinculación, campañas, reposts autorizados): ejecución de la relación con tu organización e interés legítimo en operar la herramienta.</li>
  <li><strong>Conexión LinkedIn:</strong> consentimiento al aceptar condiciones y completar OAuth, o vinculación asistida por tu administrador.</li>
  <li><strong>Estadísticas para administradores:</strong> interés legítimo en medir adopción y alcance de campañas (preferiblemente agregadas).</li>
  <li><strong>Seguridad y cumplimiento:</strong> interés legítimo y obligaciones legales.</li>
</ul>

<h2 class="h6 mt-4">5. LinkedIn y proveedores de publicación</h2>
<p class="small">La conexión con LinkedIn requiere tu autorización en la plataforma de LinkedIn. Los datos obtenidos se usan <strong>solo</strong> para advocacy y gestión de campañas dentro de Ngaged, sin crear bases de leads ajenas al servicio ni vender datos de miembros de LinkedIn.</p>
<p class="small">La publicación o amplificación técnica puede apoyarse en un <strong>proveedor externo de infraestructura de redes sociales</strong> que actúa como encargado del tratamiento bajo contrato con Parvus Media, con acceso limitado a lo necesario para conectar cuentas y ejecutar acciones autorizadas.</p>

<h2 class="h6 mt-4">6. Destinatarios y transferencias</h2>
<p class="small">Podemos comunicar datos a:</p>
<ul class="small">
  <li>proveedores de hosting, email, seguridad y publicación en redes, solo para operar Ngaged;</li>
  <li>administradores autorizados de tu organización en el panel Ngaged;</li>
  <li>autoridades cuando exista obligación legal.</li>
</ul>
<p class="small">No vendemos datos personales. Si hubiera transferencias internacionales, se aplicarán garantías adecuadas cuando la ley lo exija.</p>

<h2 class="h6 mt-4">7. Plazos de conservación</h2>
<p class="small">Conservamos los datos mientras dure la relación con tu organización y el tiempo necesario para cumplir obligaciones legales, resolver reclamaciones y mantener la seguridad. Los tokens de LinkedIn se mantienen mientras la cuenta siga vinculada o hasta revocación. Puedes solicitar desvinculación a tu administrador Ngaged o escribir a <a href="mailto:dpo@parvusmedia.com">dpo@parvusmedia.com</a>.</p>

<h2 class="h6 mt-4">8. Tus derechos</h2>
<p class="small">Puedes ejercer acceso, rectificación, supresión, oposición, limitación y portabilidad, cuando correspondan, contactando con <a href="mailto:dpo@parvusmedia.com">dpo@parvusmedia.com</a> e identificándote razonablemente. También puedes revocar consentimientos en LinkedIn. Si consideras que el tratamiento no cumple la normativa, puedes reclamar ante la <a href="https://www.aepd.es" target="_blank" rel="noopener">Agencia Española de Protección de Datos (AEPD)</a>.</p>

<h2 class="h6 mt-4">9. Seguridad</h2>
<p class="small">Aplicamos medidas técnicas y organizativas razonables (cifrado en tránsito, control de accesos, registro de actividad). Ningún sistema es completamente infalible.</p>

<h2 class="h6 mt-4">10. Menores</h2>
<p class="small">Ngaged está dirigido a entornos profesionales y no está pensado para menores de edad.</p>

<h2 class="h6 mt-4">11. Cambios</h2>
<p class="small">Podemos actualizar esta política. La versión vigente es la publicada en esta URL con la fecha indicada al inicio. Si los cambios son relevantes para la vinculación LinkedIn, podremos solicitar una nueva aceptación.</p>

<h2 class="h6 mt-4">12. Documentos relacionados</h2>
<p class="small"><a href="/terminos-conexion">Condiciones de vinculación LinkedIn (Ngaged)</a></p>
`;

  window.NGAGED_PRIVACY_HTML = PRIVACY_HTML;

  document.addEventListener('DOMContentLoaded', function () {
    const el = document.getElementById('privacy-body');
    if (el) el.innerHTML = PRIVACY_HTML;
  });
})();
