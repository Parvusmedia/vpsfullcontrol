# Parvus US Meta — draft campaign

Status: **not yet in Ads Manager**. Make can list/update campaigns on `Parvus_ES`; it cannot create them with the native Facebook Ads CM app. Graph POST needs a system-user token (see credential request below).

## Names to look for

| Object | Name |
|---|---|
| Campaign | `Parvus_US_Leads_Efficiency_v1` |
| Ad set 1 | `AS_Titles_Ops` |
| Ad set 2 | `AS_Stack_Interests` |
| Ad set 3 | `AS_Advantage_Broad` |

## IDs

- Ad account: `act_149543758710373` (Parvus_ES)
- BM: Parvus Media `688106874654286`
- Make connection: `Parvus Ad Campaigns Connection ES` (`9895891`)
- Facebook Page (ads/form): `1229053567123325`
- Privacy: https://parvusmedia.com/privacy/
- Make folder: `Parvus Automation Ops` (`380526`)

## Structure

One campaign, three ad sets, ABO, status **PAUSED**. Same two creatives in every ad set. Instant Form higher-intent. Feed FB+IG only. Targeting expansion OFF on titles and stack. Broad excludes the other two audiences.

Messenger is campaign 2 later. Do not mix.

## Blockers found 2026-08-17

1. Native Make module `facebook-ads-cm` has list/update/watch only. No create.
2. Page `1229053567123325` is **not** in the Pages list of connection `9895891` (pages visible there are Yayosquemolan, MPA, HogarTec, Residenciaenespana). Assign this Page to that Facebook user in BM before creating the Instant Form or ads.
3. Graph create needs a BM **system user** token with `ads_management`. Authorize it here (do not paste the token in chat):  
   https://eu1.make.com/38243/credentials-requests/inbox?requestId=cc1a92ef-9b66-4f5f-b1e4-d0129c5678be

After the token is saved, the campaign can be POSTed PAUSED (`$0`).
