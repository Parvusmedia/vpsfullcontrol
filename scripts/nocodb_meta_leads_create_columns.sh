#!/usr/bin/env bash
# Create unified meta_leads columns on NocoDB (Digitanimal mirror).
# Table: meta_leads (id mieilgjtcw04jjr), base p62l2gyhjqj4vo1, view vwxg2zcslydyr6vd
set -euo pipefail

TABLE_ID="${NOCODB_TABLE_ID:-mieilgjtcw04jjr}"
BASE_URL="${NOCODB_BASE_URL:-https://mpa.parvusmedia.com}"

if [[ -z "${NOCODB_API_TOKEN:-}" ]]; then
  echo "NOCODB_API_TOKEN required" >&2
  exit 1
fi

add_col() {
  local name="$1" uidt="$2"
  local payload
  payload=$(printf '{"column_name":"%s","title":"%s","uidt":"%s"}' "$name" "$name" "$uidt")
  code=$(curl -sS -o /tmp/noco_col.json -w "%{http_code}" -X POST \
    -H "xc-token: $NOCODB_API_TOKEN" -H "Content-Type: application/json" \
    "$BASE_URL/api/v1/db/meta/tables/$TABLE_ID/columns" \
    -d "$payload")
  if [[ "$code" != "200" ]]; then
    echo "FAIL $name HTTP $code $(head -c 200 /tmp/noco_col.json)" >&2
    return 1
  fi
  echo "OK $name ($uidt)"
}

# leadgen_id, meta_payload_json may already exist
cols=(
  "form_id:SingleLineText"
  "page_id:SingleLineText"
  "platform:SingleLineText"
  "is_organic:Checkbox"
  "date_created:DateTime"
  "lead_source:SingleLineText"
  "campaign_id:SingleLineText"
  "campaign_name:SingleLineText"
  "adset_id:SingleLineText"
  "adset_name:SingleLineText"
  "ad_id:SingleLineText"
  "ad_name:SingleLineText"
  "adgroup_id:SingleLineText"
  "email:SingleLineText"
  "phone:SingleLineText"
  "full_name:SingleLineText"
  "province:SingleLineText"
  "herd_count:SingleLineText"
  "livestock_type:SingleLineText"
  "home_listing:SingleLineText"
  "partner_name:SingleLineText"
  "retailer_item_id:SingleLineText"
  "make_scenario_id:SingleLineText"
)

for pair in "${cols[@]}"; do
  name="${pair%%:*}"
  uidt="${pair##*:}"
  add_col "$name" "$uidt" || true
done

echo "--- final columns ---"
curl -sS -H "xc-token: $NOCODB_API_TOKEN" \
  "$BASE_URL/api/v1/db/meta/tables/$TABLE_ID?includeColumns=true" \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print('\n'.join(c['column_name'] for c in d.get('columns',[]) if not c['column_name'].startswith('nc_') and c['column_name'] not in ('id','created_at','updated_at','created_by','updated_by')))"
