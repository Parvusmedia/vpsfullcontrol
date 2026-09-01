#!/usr/bin/env python3
"""Migrate site contact mail + public email refs to @companydataenrichment.com."""

from __future__ import annotations

import re
import sys
from pathlib import Path

DOCROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('/var/www/vhosts/companydataenrichment.com/httpdocs')
PRIVATE = DOCROOT.parent.parent / 'private' / 'cde'
OLD = 'hello@parvusmedia.com'
NEW = 'hello@companydataenrichment.com'

NEW_SEND_CONTACT = '''/**
 * Site contact notifications — local Postfix (Plesk) by default.
 */
function cde_send_contact_mail(string $to, string $subject, string $body, string $replyTo = ''): array
{
    $cfg = cde_load_mail_config();
    if ($to === '') {
        $to = (string) $cfg['to'];
    }

    $transport = strtolower(trim((string) ($cfg['transport'] ?? 'local')));
    if ($transport === 'smtp') {
        $smtp = cde_smtp_send($cfg, $to, $subject, $body, $replyTo);
        if ($smtp['ok']) {
            return $smtp;
        }
        return [
            'ok' => false,
            'error' => $smtp['error'] ?: 'Mail delivery failed',
        ];
    }

    if (is_readable(__DIR__ . '/_mail.php')) {
        require_once __DIR__ . '/_mail.php';
        $ok = cde_salesnav_send_general_mail($to, $subject, $body, $replyTo);
        return $ok ? ['ok' => true, 'error' => null] : ['ok' => false, 'error' => 'Mail delivery failed'];
    }

    $from = (string) ($cfg['from'] ?? 'hello@companydataenrichment.com');
    $fromName = (string) ($cfg['from_name'] ?? 'CompanyDataEnrichment');
    $encodedSubject = '=?UTF-8?B?' . base64_encode($subject) . '?=';
    $safeBody = str_replace(["\\r\\n", "\\r"], "\\n", $body);
    $headers = [
        'MIME-Version: 1.0',
        'Content-Type: text/plain; charset=UTF-8',
        'Content-Transfer-Encoding: 8bit',
        'From: ' . sprintf('"%s" <%s>', addcslashes($fromName, '"\\\\'), $from),
        'X-Mailer: CompanyDataEnrichment',
    ];
    if ($replyTo !== '' && filter_var($replyTo, FILTER_VALIDATE_EMAIL)) {
        $headers[] = 'Reply-To: <' . $replyTo . '>';
    }
    $ok = @mail($to, $encodedSubject, $safeBody, implode("\\r\\n", $headers));
    return $ok ? ['ok' => true, 'error' => null] : ['ok' => false, 'error' => 'Mail delivery failed'];
}'''


def patch_bootstrap(path: Path) -> bool:
    text = path.read_text()
    orig = text

    text = text.replace("'to' => $env['MAIL_TO'] ?? 'hello@parvusmedia.com',", f"'to' => $env['MAIL_TO'] ?? '{NEW}',")
    text = text.replace(
        "'from' => $env['MAIL_FROM'] ?? ($env['SMTP_USER'] ?? 'hello@parvusmedia.com'),",
        f"'from' => $env['MAIL_FROM'] ?? '{NEW}',",
    )
    if "'transport'" not in text:
        text = text.replace(
            "'secure' => strtolower($env['SMTP_SECURE'] ?? 'tls'), // tls|ssl\n    ];",
            "'secure' => strtolower($env['SMTP_SECURE'] ?? 'tls'), // tls|ssl\n"
            "        'transport' => strtolower(trim($env['MAIL_TRANSPORT'] ?? 'local')),\n    ];",
        )

    pattern = re.compile(
        r"/\*\*\s*\n \* Prefer Zoho SMTP;.*?\nfunction cde_send_contact_mail\(string \$to, string \$subject, string \$body, string \$replyTo = ''\): array\s*\{.*?\n\}",
        re.S,
    )
    if pattern.search(text):
        text = pattern.sub(NEW_SEND_CONTACT, text, count=1)
    elif 'cde_salesnav_send_general_mail' not in text:
        anchor = "function cde_client_ip(): string"
        if anchor in text:
            text = text.replace(
                "function cde_send_contact_mail(string $to, string $subject, string $body, string $replyTo = ''): array\n{\n    $cfg = cde_load_mail_config();\n    if ($to === '') {\n        $to = (string) $cfg['to'];\n    }\n    $smtp = cde_smtp_send($cfg, $to, $subject, $body, $replyTo);\n    if ($smtp['ok']) {\n        return $smtp;\n    }\n    return [\n        'ok' => false,\n        'error' => $smtp['error'] ?: 'Mail delivery failed',\n    ];\n}\n\nfunction cde_client_ip(): string",
                NEW_SEND_CONTACT + "\n\nfunction cde_client_ip(): string",
            )

    if text != orig:
        path.write_text(text)
        print(f'patched {path}')
        return True
    print(f'bootstrap ok {path}')
    return False


def patch_contact(path: Path) -> bool:
    text = path.read_text()
    new_text = text.replace(OLD, NEW)
    if new_text != text:
        path.write_text(new_text)
        print(f'patched {path}')
        return True
    print(f'contact ok {path}')
    return False


def patch_text_files() -> None:
    targets = [
        DOCROOT / 'index.html',
        DOCROOT / 'app.js',
        DOCROOT / 'salesnav' / 'index.html',
        DOCROOT / 'llms.txt',
        DOCROOT / 'llms-full.txt',
    ]
    for path in targets:
        if not path.exists():
            continue
        text = path.read_text()
        if OLD not in text:
            continue
        path.write_text(text.replace(OLD, NEW))
        print(f'patched {path}')


def patch_mail_env(path: Path) -> None:
    lines: dict[str, str] = {}
    if path.exists():
        for raw in path.read_text().splitlines():
            line = raw.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            k, v = line.split('=', 1)
            lines[k.strip()] = v.strip()

    lines['MAIL_TO'] = NEW
    lines['MAIL_FROM'] = NEW
    lines['MAIL_FROM_NAME'] = lines.get('MAIL_FROM_NAME', 'CompanyDataEnrichment')
    lines['MAIL_TRANSPORT'] = 'local'

    ordered = ['MAIL_TO', 'MAIL_FROM', 'MAIL_FROM_NAME', 'MAIL_TRANSPORT']
    out = ['# CompanyDataEnrichment site mail (local Postfix on Plesk)']
    for key in ordered:
        out.append(f'{key}={lines[key]}')
    for key, val in lines.items():
        if key not in ordered and not key.startswith('SMTP_'):
            out.append(f'{key}={val}')

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('\n'.join(out) + '\n')
    path.chmod(0o640)
    print(f'updated {path}')


def main() -> None:
    bootstrap = DOCROOT / 'api' / '_bootstrap.php'
    contact = DOCROOT / 'api' / 'contact.php'
    mail_env = PRIVATE / 'mail.env'

    if bootstrap.exists():
        patch_bootstrap(bootstrap)
    if contact.exists():
        patch_contact(contact)
    patch_text_files()
    patch_mail_env(mail_env)


if __name__ == '__main__':
    main()
