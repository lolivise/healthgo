# Data export and programmatic access for consumer body-fat smart scales (as of 2026-10-23)

Context for the report writer: the buyer already pulls Garmin Connect daily with `python-garminconnect` 0.3.x into SQLite, uses an iPhone, and lives in Australia. A scale whose weight AND body fat land in Garmin Connect with no extra moving parts is worth a lot to him, because his existing `get_body_composition` call would pick it up with zero new code.

Research budget note: about 20 tool calls covered 10 ecosystems, so coverage is uneven. Garmin, Withings, Fitbit/Google, Renpho, Eufy, openScale and SmartScaleConnect are well sourced. Hume, Omron, Xiaomi→Garmin, InBody home and Tanita outside Japan are thin; see each Gaps section.

## 1. Official APIs: auth, fields, deprecations

### Takeaway
Only **Withings** (public OAuth2 REST API) and **Tanita Health Planet** (OAuth REST, Japan-centric) offer an official consumer-facing API for scale data. **Garmin** has no official consumer API, but the unofficial `python-garminconnect` library he already uses reads and writes body composition. **Fitbit's Web API is switched off on 2026-10-30**, a week from now, and is replaced by the Google Health API. Renpho, Eufy, Hume, Xiaomi, Omron and InBody home have no public developer API I could find.

### Cited Findings
**Garmin (Index S2), via the unofficial python-garminconnect**
- The library exposes `get_body_composition(startdate, enddate=None)`, `get_weigh_ins(startdate, enddate)`, `get_daily_weigh_ins(cdate)`, `add_body_composition(timestamp, weight, percent_fat=None, percent_hydration=None, visceral_fat_mass=None, …)` (uploaded as a FIT file), `add_weigh_in(weight, unitKey='kg', timestamp='')` and `delete_weigh_in(weight_pk, cdate)` — [cyberjunky/python-garminconnect README](https://github.com/cyberjunky/python-garminconnect)
- Since 0.3.0 the library has dropped `garth`. Old `oauth1_token.json`/`oauth2_token.json` sessions cannot be converted, and tokens now live in `garmin_tokens.json` — [python-garminconnect README](https://github.com/cyberjunky/python-garminconnect)
- The README does not document the full return schema (boneMass, muscleMass, metabolicAge, visceralFatRating, physiqueRating and so on); it points to `docs/API_ENDPOINTS.md` — [python-garminconnect README](https://github.com/cyberjunky/python-garminconnect)
- "Garmin has no official write API", and third-party Withings→Garmin tools warn that they "can break when Garmin changes its private endpoints" — [search summary of Withings→Garmin projects, e.g. hugoh/Withings2Garmin](https://github.com/hugoh/Withings2Garmin)
- The Index S2 measures weight, BMI, body fat %, body water %, bone mass and muscle mass — [TechRadar review](https://www.techradar.com/reviews/garmin-index-s2); [Tom's Guide review](https://tomsguide.com/wellness/fitness/garmin-index-s2-review)

**Withings (public API)**
- Endpoint: `POST https://wbsapi.withings.net/measure` with `action=getmeas`, plus `startdate`/`enddate` (Unix) or `lastupdate` for incremental sync. Values decode as `value × 10^unit` — [Withings API reference for AI agents (llms.md)](https://developer.withings.com/llms.md)
- Scale meastype codes: 1 weight (kg), 5 fat-free mass (kg), 6 fat ratio (%), 8 fat mass (kg), 76 muscle mass (kg), 77 hydration (kg), 88 bone mass (kg). Also 91 pulse wave velocity, 140 vascular age, 4 height — [Withings llms.md](https://developer.withings.com/llms.md); 6/76/77 corroborated by [Wearipedia Withings Body+ notebook](https://wearipedia.readthedocs.io/en/stable/notebooks/withings_body_plus.html)
- The "Available Health Data" page lists scale biomarkers: weight, fat mass, fat-free mass, muscle mass, bone mass, water mass, segmental fat-free/fat/muscle mass, intracellular water and extracellular water. Under cardio it also lists visceral fat, BMR, standing HR, PWV and vascular age, plus a nerve health score. **Some biomarkers "Require the Advanced Biomarkers plan."** The page does not say which ones in extractable text — [Withings: All available health data](http://developer.withings.com/developer-guide/v3/data-api/all-available-health-data/)
- OAuth2 scopes are `user.info`, `user.metrics`, `user.activity` and `user.sleepevents`. Access tokens last 3 h and refresh tokens 1 year. **Refresh tokens rotate**: the old one dies 8 h after a new one is issued, so the new one must be saved every time. Auth codes expire in 30 s — [Withings llms.md](https://developer.withings.com/llms.md)
- Rate guidance: don't poll more than once per 10 minutes per user. Error 601 means the rate limit was hit. No numeric quota is published there — [Withings llms.md](https://developer.withings.com/llms.md)
- Webhooks: `POST /notify action=subscribe` with `appli=1` (body metrics), and Withings POSTs `userid/startdate/enddate` to your callback — [Withings llms.md](https://developer.withings.com/llms.md)
- The Public API is described as "designed for individuals and partners without a formal contract" — [Withings developer portal](https://developer.withings.com/api-reference/)

**Fitbit Aria → Fitbit Web API → Google Health API**
- Legacy Fitbit Web API support ended **2026-09-30**, and the API is **turned off 2026-10-30** — [Google Health API: API specifications / migration](https://developers.google.com/health/migration/api-specifications)
- The Google Health API has `weight` (value in `weightGrams`) and `body-fat` data types. The weight scope maps to `googlehealth.health_metrics_and_measurements.readonly`/`.writeonly`. Base pattern: `https://health.googleapis.com/v4/users/me/...` — [Google Health API specs](https://developers.google.com/health/migration/api-specifications)
- Existing Fitbit tokens don't transfer, so every user must re-consent via Google OAuth after linking Google Health in the Google Health app — [Momentum migration guide](https://www.themomentum.ai/blog/fitbit-web-api-deprecation-google-health-migration); [Google Health newsletter Aug 2026](https://developers.google.com/health/newsletters)
- SmartScaleConnect: "Fitbit: **Aria scales no longer work**". It cites Google's notice that Fitbit data disappears unless exported by 2026-02-02 — [AlexxIT/SmartScaleConnect README](https://github.com/AlexxIT/SmartScaleConnect)

**Tanita (Health Planet, Japan)**
- Health Planet is Tanita's official OAuth REST API. You register an app at healthplanet.jp for client credentials. The `innerscan` scope/endpoint returns weight, body fat %, muscle mass, visceral fat, BMR, bone mass and similar fields — [higedamc/hakari](https://github.com/higedamc/hakari); [tanita-api-ruby-client](https://github.com/koshilife/tanita-api-ruby-client); [Zenn article (JP)](https://zenn.dev/kou_pg_0131/articles/tanita-health-planet-api)
- "Some Tanita body composition scales intended for use outside of Japan are not guaranteed to work with the HealthPlanet app" — [HealthPlanet App Store listing](https://apps.apple.com/us/app/healthplanet/id692700901)

**Eufy**
- No official API. There is an unofficial `robbalmbra/eufy-api` repo — [GitHub](https://github.com/robbalmbra/eufy-api)

**Omron**
- MyDataHelps notes it "only connects with the US Omron API", and the article covers blood pressure only — [MyDataHelps](https://support.mydatahelps.org/hc/en-us/articles/33130159207315-Omron-Blood-Pressure-Readings-Data-Export)

### Inferences
- For this buyer the zero-new-code path is Garmin Index S2: weigh-ins land in Garmin Connect, and his existing `get_body_composition` already pulls them. Its risk is the same as his whole pipeline's: an unofficial API that can break on Garmin auth changes.
- Withings is the only mainstream Western brand with a documented, supported API. It would mean a second OAuth integration: rotating refresh tokens to persist, a callback URL if he wants webhooks (or just poll with `lastupdate`). Advanced metrics (segmental, ECW/ICW, possibly visceral fat) may sit behind a paid API plan.
- **Do not buy a Fitbit Aria in Oct 2026.** The API it depends on dies on 2026-10-30, and SmartScaleConnect already reports Aria as non-working.
- Tanita Health Planet is realistically for Japanese-market scales. An Australian-market Tanita is not a reliable API path.

### Gaps
- No numeric Withings quota (the old public figure of 120 req/min could not be confirmed in current docs), and no clear list of which biomarkers need the "Advanced Biomarkers" plan or what it costs for an individual developer.
- Whether visceral fat (meastype 170) and segmental/ECW/ICW come back from Getmeas on a free Public API app: not confirmed.
- I could not confirm whether the Google Health API's `body-fat` type is populated for legacy Aria data, or what its scope is.
- I found no public developer API for Renpho, Eufy, Hume, Xiaomi, Omron Connect (outside the US BP integration) or InBody home. Absence of evidence, not proof.
- I did not check Garmin's official Health API (partner/enterprise program); it is not available to individual consumers in any source I saw.

## 2. Official syncs to Garmin Connect / Apple Health / Health Connect, and third-party bridges (does body fat survive?)

### Takeaway
**No non-Garmin scale brand has an official integration that writes body fat into Garmin Connect.** That includes Withings and Renpho: every Withings→Garmin and Renpho→Garmin path found is third-party. Chained-app routes through Apple Health or Fitbit typically carry **weight only**. Mature bridges exist that write the full body composition into Garmin via the same unofficial FIT-upload route: withings-sync, SmartScaleConnect, RenphoGarminSync, and the paid ScaleLink.

### Cited Findings
**Withings → Garmin**
- No official Withings–Garmin integration turned up in 2026 searches. All results were third-party tools — [search results incl. hugoh/Withings2Garmin](https://github.com/hugoh/Withings2Garmin), [kilooo/grrminsync](https://github.com/kilooo/grrminsync), [ploa33/sync-withings2garmin](https://github.com/ploa33/sync-withings2garmin), [Emenowicz/withings-garmin-sync](https://github.com/Emenowicz/withings-garmin-sync)
- `jaroslawhartman/withings-sync` syncs Withings → Garmin Connect and TrainerRoad (also raw JSON/FIT output and optional blood pressure). It **migrated from the deprecated garth to python-garminconnect**, needs one fresh login, and stores tokens in `~/.garmin_session.json`. It warns that SSO 401/403 errors appear if run too often (e.g. every 10 min) and recommends about 8–10 runs/day. The repo has 389 commits, 37 open issues and 3 open PRs. Its README does not explicitly list fat %/muscle/bone among the uploaded fields — [withings-sync](https://github.com/jaroslawhartman/withings-sync)
- `ploa33/sync-withings2garmin` runs on GitHub Actions and syncs weight, body fat %, muscle mass, body water % and bone mass — [GitHub](https://github.com/ploa33/sync-withings2garmin)
- hugoh/Withings2Garmin syncs weight, body composition and blood pressure, computing BMI from Withings weight/height — [GitHub](https://github.com/hugoh/Withings2Garmin)
- **ScaleLink** (hosted, paid): $17.99/yr or $1.99/mo with 7 days free. It supports Withings and, with body composition enabled, sends weight, body fat, BMI, muscle mass, bone mass and body water to Garmin Connect — [Garmin Rumors: Introducing ScaleLink](https://garminrumors.com/introducing-scalelink/)

**Renpho → Garmin / others**
- Renpho's official third-party access list: Apple Health, Fitbit, Google Fit, Samsung Health, MyFitnessPal. Only one Renpho account can sync to one Fitbit/Google Fit account — [Renpho Health App FAQ](https://renpho.com/pages/faq-renpho-health-app); [Renpho blog: can't sync](https://renpho.com/blogs/wellness-fitness-blog/can-t-sync-your-data-to-the-renpho-health-app-here-s-how)
- Renpho support (undated Amazon Q&A): "the RENPHO app can not sync to Garmin connect, Strava and Map My Fitness now" — [Amazon Q&A](https://www.amazon.com/ask/questions/Tx21YMBNCRH6HHB)
- Garmin forum users on chained routes (Renpho→Fitbit/Google Fit/MFP→Garmin): only weight, weight change and BMI arrive, **not body fat or muscle** — [Garmin Forums thread 283812](https://forums.garmin.com/apps-software/mobile-apps-web/f/garmin-connect-web/283812/syncing-weight-data-from-renpho-scale-to-the-garmin-app/1566606); [Garmin Forums thread 354617](https://forums.garmin.com/apps-software/mobile-apps-web/f/garmin-connect-web/354617/import-weight-data-from-renpho-scale-to-the-garmin)
- A third-party help page claims Renpho app v6.5.0+ supports Android Health Connect. This is secondary and unverified — [Carbon integrations troubleshooting](https://help.joincarbon.com/en/articles/9814707-integrations-troubleshooting)
- `forkerer/RenphoGarminSync-CLI` reads Renpho via its internal APIs and writes measurements to Garmin. It needs both logins and is for personal use only — [GitHub](https://github.com/forkerer/RenphoGarminSync-CLI)
- `luispb/renpho-garmin-sync` (Windows) copies Renpho weigh-ins including body fat to Garmin and skips days already present. By default it reads the RENPHO Health app's CSV export; its optional unofficial-API login "fails for some accounts" — [GitHub](https://github.com/luispb/renpho-garmin-sync)
- `eclat-shubh/Garmin-Body-Comp-Upload` uploads body composition from Renpho or any CSV to Garmin via the FIT SDK, with no Index S2 required — [GitHub](https://github.com/eclat-shubh/Garmin-Body-Comp-Upload)

**SmartScaleConnect (AlexxIT), a multi-brand bridge**
- Sources: Garmin, Home Assistant, Mi Fitness, Xiaomi Home, Zepp Life, My TANITA, Picooc, Fitbit (archive ZIP only), CSV/JSON. Targets: Garmin, Home Assistant, Zepp Life, CSV, JSON. **Withings, Eufy, Renpho and Omron are not listed** — [SmartScaleConnect README](https://github.com/AlexxIT/SmartScaleConnect)
- Fields include weight, BMI, body fat, body water, bone mass, metabolic age, muscle mass, physique rating, protein mass, visceral fat, BMR, HR and skeletal muscle mass. It runs as a binary, Docker image or HA add-on, configured with `scaleconnect.yaml` — [SmartScaleConnect](https://github.com/AlexxIT/SmartScaleConnect)
- Caveats: "early stage, configuration and functionality can change a lot". **Garmin 2FA is not supported.** Zepp Life works only with a Xiaomi-account login and logs you out of the mobile app. Tanita weigh-in times may be wrong (time zone unknown). Mi Fitness S400 CN in the EU region needs a mod. No release dates are visible — [SmartScaleConnect](https://github.com/AlexxIT/SmartScaleConnect)

**Hume**
- Hume's Pod page says it syncs with Apple Health, Google Fit and Samsung Health — [Hume Pod 2.0 page](https://humehealth.com/pages/hume-pod-2-0-pdp3)
- Hume FAQ: "Not all Hume metrics have direct equivalents in Apple Health/Google Fit" — [Hume FAQ](https://humehealth.com/pages/faq)

### Inferences
- Apple Health is not a bridge into Garmin Connect for body fat. Garmin does not ingest body composition from Apple Health in any source found, and forum evidence says chained routes deliver weight only.
- If he buys Withings, the robust path is to read the Withings API directly into SQLite. A withings-sync-style FIT upload to Garmin would be a convenience mirror only. Note that he already authenticates python-garminconnect, so a second login source hitting Garmin SSO could raise 429/401 risk; withings-sync's own README warns about frequent logins.
- If he buys Renpho, there is no supported API at all. Every route is CSV export, a reverse-engineered Renpho API, or Apple Health → an export app.

### Gaps
- I could not confirm whether withings-sync's current release uploads fat %/muscle/bone/hydration (historically it did, but this round's README extract did not list them).
- No source dated 2025–2026 confirmed whether Renpho has since added a native Garmin link. The "cannot sync to Garmin" statement is undated.
- Whether Eufy, Omron, Xiaomi (Mi Fitness/Zepp Life) or InBody officially write to Garmin Connect: not found. Zepp Life historically had no Garmin link, but this could not be verified this round.
- Last-commit dates for the bridge repos (withings-sync, SmartScaleConnect, RenphoGarminSync) were not visible in fetched pages. Maintenance status should be checked live.

## 3. CSV / in-app data export and GDPR download

### Takeaway
Eufy documents an emailed CSV "Export All Data", but a 2024 user report says it was later removed. Renpho export is unconfirmed by official sources; one third-party tool reads a "RENPHO Health CSV export", which implies it exists. Hume reportedly exports (XML). Garmin and Withings exports were not researched this round beyond their APIs.

### Cited Findings
- EufyLife: Me → Data → "Export All Data" (since app 2.2.60). Enter your password and a CSV is emailed — [eufy support](https://service.eufy.com/article-description/How-to-Export-Data-from-the-EufyLife-App); [eufy NZ support](https://support.nz.eufy.com/support/solutions/articles/154000242608-how-to-export-data-from-the-eufylife-app-)
- A 2024 comment says the Eufy export feature was removed without replacement. The open-source `eufylife-export` extracts body data to CSV from a local (Android) backup — [deuts.net blog](https://deuts.net/2022/08/how-to-export-your-data-from-the-eufy-smart-scale-c1/); [MarconZet/eufylife-export](https://github.com/MarconZet/eufylife-export); [stcase.dev](https://www.stcase.dev/blog/exporting-eufy-smart-scale-data/)
- Renpho: `luispb/renpho-garmin-sync` defaults to "the CSV file exported by the RENPHO Health app" — [GitHub](https://github.com/luispb/renpho-garmin-sync). No official Renpho page confirming CSV export was found; a German Q&A claims export via app settings without steps — [antwort.net](https://www.antwort.net/a/technologie/wie-kann-man-daten-aus-der-renpho-health-app-exportieren.html)
- Renpho guest-mode data cannot be transferred and is lost on uninstall or device change — [Renpho blog](https://renpho.com/blogs/wellness-fitness-blog/can-t-sync-your-data-to-the-renpho-health-app-here-s-how)
- Hume: "You own your health data (exportable)". A review says data exports as XML in about a minute. The ownership claim is on the Band page — [Hume Band 2.0 page](https://humehealth.com/pages/hume-bandv2); [cpapmyway review](https://cpapmyway.com/blogs/blog/hume-band-2-body-pod-30-day-review)
- iPhone fallback for any Apple-Health-writing scale: third-party apps like Health Auto Export (JSON+CSV) and Health Export CSV export from Apple Health — [Health Auto Export](https://apple.co/3iqbU2d); [Health Export CSV](https://apps.apple.com/us/app/health-export-csv/id1477944755)

### Inferences
- An Apple Health → Health Auto Export (with REST/automation) path is a generic, brand-agnostic fallback for iPhone users. It is fragile, though, and needs the phone in the loop; it is not a server-side pull like his Garmin job.

### Gaps
- Garmin Connect "Export Your Data" (GDPR) and Withings Health Mate CSV export were not verified this round (both are known to exist from prior knowledge but are not cited here).
- Omron Connect, Xiaomi Mi Fitness/Zepp Life, Tanita and InBody app export: no sources found.

## 4. Local / open-source BLE (no cloud)

### Takeaway
openScale (Android; the wiki was edited 2026-10-17) supports many BLE scales, including Xiaomi Mi Scale v1/v2 and S400/S800, Renpho ES-CS20M/ES-26BB-B/Elis, Eufy P1/P2/C1/A1, Omron HBF/BCM, Beurer, Huawei, Yunmai and others. Body-metric decoding varies per model. Withings, Garmin and Tanita are not supported. Home Assistant's Xiaomi BLE integration had a 2025 report of S400 failing to add.

### Cited Findings
- The openScale supported list includes: Xiaomi Mi Scale v1/v2, Body Composition Scale S400/S800, S200 (weight only); Renpho Elis Solar (R-A012/R-A020), ES-26BB-B, ES-WBE28, ES-CS20M; QN Scale and QN Broadcast; Eufy A1, C1, C20, P1, P2/P2 Pro; Omron BCM-500, HBF-222T/227T/228T/230T/702T, KRD-703T, VIVA; Beurer BF-series; Sanitas/SilverCrest; Medisana; Trisa; Huawei/Honor AH100/CH100/Scale 2 Pro/3/3 Pro; Yunmai; Picooc; Etekcity; 1byone and others. **Withings, Garmin and Tanita are not listed.** The page was edited 2026-10-17 — [openScale wiki: Supported scales](https://github.com/oliexdev/openScale/wiki/Supported-scales-in-openScale)
- Per-model "Body metrics" status is ✓ / o (scale has it but needs reverse engineering) / n/a. ES-CS20M uses the Trisa library until the QN protocol is fully reverse-engineered. Huawei Scale 2 Pro/3/3 Pro need CAK/C1/C2 keys. FITINDEX FT-26R-W (QN Broadcast), AAA-series and Xiaomi S200 are weight-only. "Not every scale will work perfectly" — [openScale wiki](https://github.com/oliexdev/openScale/wiki/Supported-scales-in-openScale)
- openScale is Android-focused, with no iOS mention — [openScale wiki](https://github.com/oliexdev/openScale/wiki/Supported-scales-in-openScale)
- Home Assistant core issue #142364: the Xiaomi S400 (MJTZC01YM) could not be added via the Xiaomi BLE integration on core-2025.3.4, reported as a regression. No fix confirmed in sources — [home-assistant/core#142364](https://github.com/home-assistant/core/issues/142364)
- Xiaomi S400: dual-frequency BIA, 25 metrics, BLE 5.0, pairs with Mi Home/Xiaomi Home, optional BLE gateway for cloud upload — [Xiaomi specs (CL)](https://www.mi.com/cl/product/xiaomi-body-composition-scale-s400/specs/); [PB Tech listing](https://www.pbtech.com/product/HEAMIX21793/Xiaomi-Smart-Scale-S400-Body-Composition-Scale-Hig)
- SmartScaleConnect can take Home Assistant as a source and push to Garmin, so a local BLE → HA → Garmin path is possible — [SmartScaleConnect](https://github.com/AlexxIT/SmartScaleConnect)

### Inferences
- Since he uses an iPhone, openScale (an Android app) is only usable with a spare Android device. The realistic local path is Home Assistant/ESPHome BLE proxy → SQLite or → Garmin via SmartScaleConnect. That is a meaningful build-out compared with buying an Index S2.
- Many cheap BLE scales send body-composition values only after a vendor algorithm or user profile handshake. Raw "impedance" is often what is broadcast, and body fat is computed downstream; openScale's "o" markers reflect this.

### Gaps
- ESPHome configs for specific scales (Xiaomi Mi Scale 2 and others) were not researched this round.
- Whether any scale exposes raw impedance values through an official API: none found. Withings Getmeas returns derived masses, not impedance, per the type list above.
- Status of the HA S400 issue after March 2025: unknown.

## 5. Subscriptions: what's locked

### Takeaway
Hume says the scale works without its premium membership (about $8.99–$9.99/mo), but it is unclear which Pod data or exports are premium-only. Withings has an "Advanced Biomarkers" API plan gating some biomarkers at the developer-API level. Renpho premium's effect on export was not determinable.

### Cited Findings
- Hume: optional premium membership; "you don't need the subscription to use the scale". Price is cited as $9.99/mo by Wareable and $8.99/mo by others (sources conflict) — [Wareable Hume Body Pod 2.0 review](https://www.wareable.com/health-tech/hume-health-body-pod-2-0-review); [cpapmyway review](https://cpapmyway.com/blogs/blog/hume-band-2-review)
- Hume: "No subscription is required to use the Band or access your raw data". That page is about the Band, not explicitly the Pod — [Hume Band 2.0 page](https://humehealth.com/pages/hume-bandv2)
- Withings API: some biomarkers "Require the Advanced Biomarkers plan" — [Withings: All available health data](http://developer.withings.com/developer-guide/v3/data-api/all-available-health-data/)
- SmartScaleConnect, a free third-party alternative to paid bridges, versus ScaleLink at $17.99/yr — [ScaleLink](https://garminrumors.com/introducing-scalelink/); [SmartScaleConnect](https://github.com/AlexxIT/SmartScaleConnect)

### Gaps
- Withings+ (consumer subscription) contents and whether any Health Mate export or metric is locked behind it: not researched.
- Renpho premium membership: no source said whether export or third-party sync requires it.
- Garmin Connect+ (Garmin's paid tier): not researched for body-composition gating. No source suggested scale data is gated.
- Whether Hume Pod segmental or advanced metrics require premium: unconfirmed.

## 6. Multi-user handling / auto recognition

### Takeaway
The Index S2 stores up to 16 user profiles. Evidence on how reliably it auto-recognises users is thin, with one buyer complaint. Renpho ties one Renpho account to one Fitbit/Google Fit account, and its guest-mode data is not durable.

### Cited Findings
- Index S2: up to 16 user profiles, and the app can invite other users — [Backcountry listing](https://content.backcountry.com/garmin-index-s2-smart-scale); [Tom's Guide](https://tomsguide.com/wellness/fitness/garmin-index-s2-review)
- One buyer: the scale "does not note my posted name, took several tries" — [Competitive Cyclist listing](https://www.competitivecyclist.com/garmin-index-s2-smart-scale)
- Renpho: one Renpho account syncs to one Fitbit or Google Fit account. Guest-mode data is lost on uninstall or device change — [Renpho FAQ](https://renpho.com/pages/faq-renpho-health-app); [Renpho blog](https://renpho.com/blogs/wellness-fitness-blog/can-t-sync-your-data-to-the-renpho-health-app-here-s-how)
- SmartScaleConnect: Mi Fitness "other-user data isn't supported for the 8-electrode scale". Sanitas SBF70 needs the user name to match in openScale — [SmartScaleConnect](https://github.com/AlexxIT/SmartScaleConnect); [openScale wiki](https://github.com/oliexdev/openScale/wiki/Supported-scales-in-openScale)

### Inferences
- For a single-user household, auto-recognition matters less. If others use the scale, misattributed weigh-ins will land in his Garmin/SQLite data, so a dedupe/outlier filter in his pipeline is prudent whichever brand he buys.

### Gaps
- No Garmin-official statement on the Index S2 recognition mechanism (weight-proximity based) was retrieved. Withings, Eufy and Hume multi-user behaviour was not researched this round.

## 7. Reliability problems and Australia-specific notes

### Takeaway
The main reliability risk for any Garmin-centred pipeline is unofficial Garmin auth: SSO 401/403/429 from frequent logins, 2FA unsupported by some bridges, and the garth deprecation forcing re-login. Wi-Fi setup failures are reported for the Index S2. Fitbit/Aria is end-of-life. No Australia-specific API restrictions were found.

### Cited Findings
- withings-sync: SSO 401/403 if logins are too frequent; run about 8–10×/day — [withings-sync](https://github.com/jaroslawhartman/withings-sync)
- SmartScaleConnect: Garmin 2FA is not supported, and Garmin China servers are not supported — [SmartScaleConnect](https://github.com/AlexxIT/SmartScaleConnect)
- python-garminconnect 0.3.0 dropped garth, so old token files can't be reused — [python-garminconnect](https://github.com/cyberjunky/python-garminconnect)
- Index S2: a buyer reports it "Still does not hook up to my wifi" — [Index S2 listing/reviews (search summary)](https://www.techradar.com/reviews/garmin-index-s2)
- Renpho unofficial API login "fails for some accounts" — [luispb/renpho-garmin-sync](https://github.com/luispb/renpho-garmin-sync)
- Zepp Life sync via SmartScaleConnect logs you out of the mobile app — [SmartScaleConnect](https://github.com/AlexxIT/SmartScaleConnect)
- Fitbit Web API switch-off 2026-10-30 — [Google Health API specs](https://developers.google.com/health/migration/api-specifications)
- Omron: the third-party integration (MyDataHelps) supports only the US Omron API — [MyDataHelps](https://support.mydatahelps.org/hc/en-us/articles/33130159207315-Omron-Blood-Pressure-Readings-Data-Export)
- Tanita HealthPlanet is not guaranteed for non-Japan scales — [HealthPlanet App Store](https://apps.apple.com/us/app/healthplanet/id692700901)

### Inferences
- The healthgo repo already caps Garmin credential logins at one per 24 h. Adding withings-sync or SmartScaleConnect as a second Garmin login client would undercut that guard. If he buys Withings, he should read Withings straight into SQLite and skip uploading to Garmin, or route the upload through his existing token store.
- Overall ranking for this buyer, by integration friction: (1) **Garmin Index S2**, which needs zero new code, though body fat is consumer-grade BIA; (2) **Withings**, the only official, documented API, with a stable OAuth plus a webhook; (3) **Xiaomi/Renpho/Eufy**, which need reverse-engineered or community bridges or CSV; (4) **Hume/Omron/InBody home/Tanita**, with unknown or closed programmatic access; (5) **Fitbit Aria**, which is dead.

### Gaps
- Availability and pricing of the Index S2, Withings, Hume, Xiaomi S400 and others in Australia were not researched here (likely covered by another researcher).
- Region locks on Xiaomi Mi Fitness servers for AU accounts: not found. SmartScaleConnect only mentions CN/EU region issues.
- InBody home (H20N/H30) app export or API: no sources found this round.
- Recent (2025–2026) Reddit reports of Withings or Index S2 sync data loss: not found in this round's searches.
