# Parvus Media web

Production landing for https://parvusmedia.com/

Source of truth in this repo: `parvusmedia-web/`. Live files also live on Parvus VPS at `/opt/apps/parvusmedia-web` and deploy to Plesk on `nextconvers-vps`.

## ChatGPT Ads

- Homepage band: `/#chatgpt-ads`
- Service page: https://parvusmedia.com/chatgpt-ads/

## Deploy

From this directory, hop through `parvus-vps` (rsync runs there):

```bash
./deploy.sh
```

Manual equivalent:

```bash
rsync -avz index.html contact.php robots.txt nextconvers-vps:/var/www/vhosts/parvusmedia.com/httpdocs/
rsync -avz css/main.css nextconvers-vps:/var/www/vhosts/parvusmedia.com/httpdocs/css/main.css
rsync -avz js/main.js nextconvers-vps:/var/www/vhosts/parvusmedia.com/httpdocs/js/main.js
rsync -avz chatgpt-ads/ nextconvers-vps:/var/www/vhosts/parvusmedia.com/httpdocs/chatgpt-ads/
rsync -avz assets/ nextconvers-vps:/var/www/vhosts/parvusmedia.com/httpdocs/assets/
rsync -avz e/ nextconvers-vps:/var/www/vhosts/parvusmedia.com/httpdocs/e/
rsync -avz privacy/ nextconvers-vps:/var/www/vhosts/parvusmedia.com/httpdocs/privacy/
rsync -avz legal-notice/ nextconvers-vps:/var/www/vhosts/parvusmedia.com/httpdocs/legal-notice/
ssh nextconvers-vps 'chown -R parvusadmin:psacln /var/www/vhosts/parvusmedia.com/httpdocs/{index.html,contact.php,robots.txt,css/main.css,js/main.js,chatgpt-ads,assets,e,privacy,legal-notice}'
```

Do not deploy `.captcha_secret` from git (it is gitignored). Leave the live file in place.

Mail from the contact form goes through Zoho SMTP (`private/cde/mail.env` on Plesk). PHP `mail()` is rejected by Zoho because SPF only allows `zoho.com` and `mailgun.org`.

OpenAI Ads pixel is in the page `<head>` (`debug: true` while the campaign is being verified). Conversion API events are posted from `/oai-event.php` using `private/parvusmedia-web/openai-ads.env` (never commit the API key).

| View | Event |
|------|--------|
| `https://parvusmedia.com/` (home landing) | `contents_viewed` |
| `https://parvusmedia.com/#chatgpt-ads` and `/chatgpt-ads/` | `contents_viewed` |
| `https://parvusmedia.com/#contact` | `appointment_scheduled` |

The browser pixel `measure` call and the server event share the same `event_id` so OpenAI can deduplicate.

### Email example short links (`/e/…`)

| Short URL | Asset |
|-----------|--------|
| https://parvusmedia.com/e/signals/ | custom_signals.jpg (weather) |
| https://parvusmedia.com/e/signals-travel/ | custom_signals_travel.jpg |
| https://parvusmedia.com/e/automation/ | custom_signals_automation.jpg |
| https://parvusmedia.com/e/dco/ | custom_dco.jpg |
| https://parvusmedia.com/e/leads/ | custom_leads.jpg |
| https://parvusmedia.com/e/whatsapp/ | custom_leads_whatsapp.jpg |
| https://parvusmedia.com/e/social/ | custom_social.jpg |
| https://parvusmedia.com/e/insights/ | custom_insights.jpg |

`/v2` redirects to `/`.
