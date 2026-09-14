# Parvus Media web

Production landing for https://parvusmedia.com/

## Deploy

```bash
rsync -avz index.html contact.php .captcha_secret robots.txt nextconvers-vps:/var/www/vhosts/parvusmedia.com/httpdocs/
rsync -avz css/main.css nextconvers-vps:/var/www/vhosts/parvusmedia.com/httpdocs/css/main.css
rsync -avz js/main.js nextconvers-vps:/var/www/vhosts/parvusmedia.com/httpdocs/js/main.js
rsync -avz assets/ nextconvers-vps:/var/www/vhosts/parvusmedia.com/httpdocs/assets/
rsync -avz e/ nextconvers-vps:/var/www/vhosts/parvusmedia.com/httpdocs/e/
rsync -avz privacy/ nextconvers-vps:/var/www/vhosts/parvusmedia.com/httpdocs/privacy/
rsync -avz legal-notice/ nextconvers-vps:/var/www/vhosts/parvusmedia.com/httpdocs/legal-notice/
ssh nextconvers-vps 'chown -R parvusadmin:psacln /var/www/vhosts/parvusmedia.com/httpdocs/{index.html,contact.php,.captcha_secret,robots.txt,css/main.css,js/main.js,assets,e,privacy,legal-notice}'
```

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
