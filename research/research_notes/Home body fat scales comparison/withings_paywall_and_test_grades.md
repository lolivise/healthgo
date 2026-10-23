# Withings+ sync paywall (Oct 2026), independent test grades for Withings and Garmin scales, and the Maurer v. Garmin class action

Researched 23 Oct 2026. Source labels: **[VENDOR]** manufacturer, **[IND]** independent tester or news outlet, **[IND-paywalled]** independent with results behind a paywall, **[AFF]** affiliate or retailer content, **[UGC]** user-generated (forums, comments), **[COURT]** court docket data.

---

## 1. What Withings changed in October 2026, and does it block the developer API, CSV export or Garmin bridging?

### Takeaway
Yes, it reaches the developer API. Withings' own API plans page says that from **12 Oct 2026**, any Withings account **created after that date** needs an active **Withings+** membership to share data with any app on the free "Start for Free" API plan. That covers a personal OAuth2 script registered at developer.withings.com, and by extension withings-sync and other self-hosted Withings-to-Garmin bridges. Apple Health and Google Health Connect are covered too. Accounts created on or before 12 Oct 2026 are grandfathered indefinitely, on any device. Viewing data in the Withings app and **manual CSV/PDF export remain free**. If a membership lapses, sharing pauses but history is kept and "resumes where it left off".

### Cited Findings
**Official Withings developer wording [VENDOR], live page fetched 23 Oct 2026:**
- Banner: "Withings+ becomes required on the Start for Free API plan from October 12, 2026. Withings accounts created after that date will need a membership to share health data with a free-plan app, including apps that are already live. Accounts created before that date are unaffected, and Enterprise lifts the requirement for specific use cases." — [Withings API Plans (static.withings.com)](https://static.withings.com/content/api/plans/plans.html), the content behind [developer.withings.com API plans](https://developer.withings.com/developer-guide/v3/withings-solutions/withings-api-plans/)
- Start for Free plan: free and self-serve, "Users 10 · more after review", "Withings+ Required for your users". It includes core biomarkers (Activity, Sleep, **Body**, Heart), "REST API, OAuth 2.0 and webhooks", standard rate limits, EU hosting. Footnote 1: "Applies to Withings accounts created after October 12, 2026. Accounts created before that date keep sharing health data with no membership required." — [same page](https://static.withings.com/content/api/plans/plans.html)
- Enterprise and Advanced Biomarkers plans: custom pricing. The Withings+ requirement "Can be removed" only for "specific use cases: Cellular Solutions, SDK and Research partners". — [same page](https://static.withings.com/content/api/plans/plans.html)
- FAQ on the same page:
  - "Can my users share through Apple Health or Google Health instead? **No. The requirement covers those routes too.** Integrating directly with the Withings API on Enterprise is the only way to guarantee your users can share data without their own membership."
  - "What if a user lets their Withings+ membership lapse? Sharing pauses until the membership is active again. **Historical data is not deleted, and sharing resumes where it left off.**"
  - "Why is Withings introducing this? Withings+ funds the clinical validation, regulatory clearances and infrastructure behind the data you consume." — [same page](https://static.withings.com/content/api/plans/plans.html)
- The Public API is described as "designed for individuals and partners without a formal contract", and the docs say "you can use your personal Withings account" to create an application. The developer account itself is still free ("free access is provided"). — [Withings developer guide, create your accesses](https://developer.withings.com/developer-guide/v3/integration-guide/public-health-data-api/developer-account/create-your-accesses-no-medical-cloud/)

**Consumer-side details (press) [IND]:**
- Scope: automatic sync to Apple Health and Google Health Connect needs Withings+ for accounts opened on or after **13 Oct 2026**. Accounts created on or before 12 Oct keep free sync. New users get a **one-month free trial**, then pay **US$9.95/month or US$99.50/year**. Free users can still view data in the app and export history as CSV or PDF. — [Android Authority (Oct 2026)](https://www.androidauthority.com/withings-apple-health-google-health-connect-sync-paywall-3724240/), via search snippet; direct fetch returned 403.
- Withings (via Android Headlines) says the grandfathered free sync is "tied to your account and not your device", so older accounts keep it on future Withings devices. **CSV/PDF export remains free.** — [Android Headlines, 19 Oct 2026](https://www.androidheadlines.com/2026/10/withings-decides-data-syncing-should-be-a-paid-feature.html)
- Terra API (a health-data aggregator) puts the cutoff at accounts created **on or after 13 Oct 2026**: "The cutoff depends on the account's creation date, rather than when the device was purchased." Withings links the change to its new **AI Connector**, which it says required API changes and extra privacy measures. Apps that read Withings weight via Apple Health inherit the cutoff, and "an older Withings account can therefore give a different result from a newly created one". — [Terra blog, 14 Oct 2026 [IND, industry vendor]](https://tryterra.co/blog/withings-apple-health-sync-subscription-new-accounts)
- Gadgets & Wearables was first to quote the developer-page banner (13 Oct 2026). It gives **US$9.99/month or $99.99/year** and does not mention Strava, MyFitnessPal or Garmin. — [Gadgets & Wearables, 13 Oct 2026](https://gadgetsandwearables.com/2026/10/13/withings-apple-health-sync-withings-plus/)
- Official Withings+ pages, as reported on 16 Oct 2026: $9.95/$99.50 (US), €9.95/€99.50, £8.95/£89.50, one-month trial. The cutoff is 12 Oct in the developer docs and 13 Oct in press reports, and it is "unsettled" whether an account created on 12 Oct itself is covered. — [braindetox.kr, 16 Oct 2026 [IND blog]](https://braindetox.kr/en/posts/withings_apple_health_sync_subscription_2026.html)
- Earlier notes in this folder cite Withings' digital product lead Vincent Brand, speaking to Numerama: no plans to reverse it, and he called it necessary for survival. They also give €9.99/€99.99 for France and note that CSV/PDF exports remain free. — [Techwalla, 16 Oct 2026](https://www.techwalla.com/13780361/withings-paywall-third-party-syncing-what-new-users-pay)
- **Strava is unclear.** Selectra (France) says Strava is "neither named nor excluded" by the rule. The briefing's claim that Strava is covered could not be confirmed in Withings' own wording, which only names "a free-plan app" plus Apple Health and Google Health. — [Selectra (Oct 2026)](https://selectra.info/telecom/actualites/marche/withings-apple-sante-abonnement-13-octobre), via search snippet
- Price inconsistency: US$9.95/$99.50 (Withings US page, Terra, Android Authority) against $9.99/$99.99 (Gadgets & Wearables, iDevice, a support-forum post). — [Terra](https://tryterra.co/blog/withings-apple-health-sync-subscription-new-accounts); [Gadgets & Wearables](https://gadgetsandwearables.com/2026/10/13/withings-apple-health-sync-withings-plus/)

**Reactions [UGC/IND]:**
- Withings support-community thread: "Unacceptable: Apple Health Sync is now behind a $99/year paywall for new accounts". Commenters under MacRumors' report mostly say they will avoid the brand. — [Withings community thread](https://support.withings.com/hc/en-us/community/posts/51887047154577-Unacceptable-Apple-Health-Sync-is-now-behind-a-99-year-paywall-for-new-accounts) (403 on fetch; summary via search snippet)
- Coverage also appeared on Mezha, Tech Insider, MacReview and Wi-Fi Planet (15-17 Oct 2026). — [Mezha](https://mezha.net/eng/news/dec44ddb_withings_puts_automatic_health/); [MacReview](https://macreview.com/withings-apple-health-sync-paid/)

**withings-sync / Garmin Connect bridging [UGC]:**
- The jaroslawhartman/withings-sync issue tracker has no issue mentioning Withings+ or a new-account paywall as of 23 Oct 2026. Recent issues are about token refresh (#260, 11 Sep 2026), unreliable syncing (#261, 24 Sep 2026), and Withings "Error 601 Too many requests" (#237, Jan 2026). — [withings-sync issues](https://github.com/jaroslawhartman/withings-sync/issues) (checked via `gh search issues`, 23 Oct 2026)
- Withings has no native Garmin Connect integration. Bridging relies on community tools that call the Withings OAuth2 API: withings-sync, Withings2Garmin and grrminsync. — [withings-sync on PyPI](https://pypi.org/project/withings-sync/4.2.2); [Withings2Garmin](https://github.com/sodelalbert/Withings2Garmin); [grrminsync](https://github.com/kilooo/grrminsync)

### Inferences
- **A personal script is a "free-plan app".** Per Withings' own wording, a Withings account created after 12 Oct 2026 cannot authorise a self-registered Start for Free app (Measure - Getmeas included) without an active Withings+ membership. The Enterprise exemption is limited to Cellular, SDK and Research partners, so an individual cannot get it. withings-sync and similar bridges call the same API and will hit the same block for new accounts. They will keep working for grandfathered accounts.
- **Free, unattended alternatives for a new account:** manual CSV export from the Withings app or web (free per press), then import. Or Bluetooth-local extraction, which some community projects attempt for other Withings devices (e.g. [pierosavi/withings-local](https://github.com/pierosavi/withings-local), BeamO, Oct 2026). No scale support was confirmed, so treat this as speculative.
- **"Resumes where it left off"** suggests a lapsed member could re-subscribe for one month and back-fill history through the API. That is an inference from the FAQ wording and has not been tested.
- **The cheapest route is grandfathering.** A buyer who already has a Withings account created on or before 12 Oct 2026 (e.g. an old Withings or Nokia Health account) keeps free API, Apple Health and Health Connect access on any new Withings scale, because eligibility follows the account, not the device.
- For healthgo specifically: the pipeline reads Garmin Connect. A new-account Withings scale would need Withings+ (about US$99.50/yr) or a manual CSV step to get weigh-ins into Garmin. A Garmin Index S2 writes to Garmin Connect natively at no cost.

### Gaps
- **Australia and AUD price:** no source gave an AUD price for Withings+. The Withings AU Withings+ page returned 403. No source reports a regional carve-out, and the developer-page rule has no geographic qualifier, so it very likely applies in Australia, but this is unconfirmed. A US$99.50 conversion is about A$150/yr (rough, depends on FX); Withings' local list price may differ.
- **Exact cutoff day:** "after October 12" (developer page) versus "on or after October 13" (press). Whether an account created on 12 Oct itself is covered is ambiguous. Both readings agree that accounts created on 13 Oct or later must pay.
- **Strava and MyFitnessPal** coverage is not confirmed by Withings wording.
- **GDPR data export:** no Withings support article on a full GDPR data download was retrieved. Only press statements that CSV/PDF export stays free.
- The Withings consumer support article and the official Withings+ FAQ text (the consumer side, not the developer page) were not retrievable (403).

---

## 2. Independent test grades: Stiftung Warentest (Sept 2024) and Which? (Jan 2025)

### Takeaway
Stiftung Warentest's per-model grades for the Withings Body Scan and Garmin Index S2 remain paywalled (EUR 4.90 to unlock), and no reputable press outlet published them. Free facts: 17 scales, grades ranging only from "gut" to "ausreichend". The cheap **ADE Ines won with gut (2,0)**. Omron Viva was best app scale at gut (2,3), with Beurer BF 500 also named. Several EUR 100-400 models missed "gut". Body analysis carries 30 % of the grade, measured against a physician-run hand-to-foot medical BIA. The only Withings-specific grade seen is a user claim that the **Body Scan got 3,3 (befriedigend)**. No Garmin grade was found from any reliable source. Which? per-model results (BodPod-referenced) are members-only, and no press release or coverage disclosing them was found.

### Cited Findings
**Stiftung Warentest (test 10/2024, published online 17 Sep 2024) [IND-paywalled]:**
- 17 body-fat scales: 11 with app, 6 without. "Die Noten reichen von Gut bis Ausreichend." Prices EUR 28-400. "Mehrere teure Modelle mit Preisen zwischen 100 und 400 Euro verpassen die Note Gut." Models tested: ADE Ines, Amazfit Smart Scale, Beurer BF 1000 Super Precision, Beurer BF 400, Beurer BF 500, **Garmin Index S2**, Medisana BS 444 / BS483, Omron BF511, Omron Viva, Sanitas SBF 14, Soehnle Shape Sense Connect 200 / Control 200, Tanita BC-333LE, **Withings Body Scan**, **Withings Body Smart**, Xiaomi Mi Body Composition Scale 2. — [test.de Körperfettwaagen im Test](https://www.test.de/koerperfettwaage-test-4645874-0/)
- Method and weighting: Wiegen 20 % (calibrated weights of 20/60/100/140 kg, five times each, plus a tilt test). **Körperanalyse 30 %** (body fat, muscle mass, body water, BMR; at least 30 subjects aged 20-65, 45-100 kg, three independent measurements each; reference = medical hand-to-foot BIA run by an experienced sports physician). Handhabung 30 %, Sicherheit/Haltbarkeit 10 %, Basisschutz persönlicher Daten 10 %. Devices were bought Apr-May 2024. — [test.de](https://www.test.de/koerperfettwaage-test-4645874-0/)
- Stiftung Warentest staff comments on the article: two samples per product, with extra units bought for retests if anomalies appeared (05 May 2026). The body-analysis check focused on body fat, muscle mass, water and BMR (09 Feb 2026). — [test.de comments](https://www.test.de/koerperfettwaage-test-4645874-0/)
- The Withings Body Scan detail page (dated 17.09.2024) shows the grade only after paying EUR 4.90. A legend footnote, "Einschließlich der Handsensoren", confirms the Body Scan's hand electrodes were included in testing. — [test.de Withings Body Scan](https://www.test.de/koerperfettwaage-test-4645874-detail/32290!17/)
- Test winner **ADE Ines (no app), gut (2,0), about EUR 30**. **Omron Viva** shared second among app scales, gut (2,3): "Eine günstige Waage gewinnt den Test und stellt teurere Geräte mit App in den Schatten." Withings and Garmin are not mentioned. — [t-online (updated 07 Aug 2025) [IND/AFF]](https://www.t-online.de/ratgeber/gesundheit/drogerie/id_100491172/koerperfettwaagen-im-test-stiftung-warentest-kuert-testsieger.html)
- Beurer BF 500 named as the app-category winner, nine models rated "gut", and a claim that scales **without hand sensors delivered better body-analysis data** than those with them. — [familie.de / produkte-im-test.de / testsieger.de, search snippets [AFF]](https://www.familie.de/testberichte/koerperfettwaage-test-die-besten-sind-laut-stiftung-warentest-gut-und-guenstig--01J8EQSPRYM0GE26907R42C20X). This conflicts with t-online, which names Omron Viva as the second app scale; the two may agree if Beurer BF 500 was first. Not verified.
- **Withings Body Scan = 3,3 (befriedigend); Body Smart = "mangelhaft"**, per a user post titled "Stiftung Warentest 10/2024 bestätigt schlechte Körperanalyse": "Die Body Scan ist mit Note 3,3 enttäuschend abgeschlagen. Die Body Smart erhielt sogar ein mangelhaft!" — [Withings community post [UGC]](https://support.withings.com/hc/en-us/community/posts/28736959455505-Stiftung-Warentest-10-2024-best%C3%A4tigt-schlechte-K%C3%B6rperanalyse) (search snippet only; page 403). **Contradiction:** test.de says overall grades run only "Gut bis Ausreichend", so "mangelhaft" can only be a sub-grade, probably Körperanalyse, not the overall grade.
- Galaxus retailer listings show the "Stiftung Warentest Oct 2024" result as "Very good 81/100" for the Garmin Index S2 and "Very good 84/100" for the Withings Body Scan. — [Galaxus Garmin Index S2 [AFF]](https://galaxus.it/en/s6/product/garmin-index-s2-smart-scale-18140-kg-bathroom-scales-14072280); [Galaxus Withings Body Scan [AFF]](https://galaxus.de/en/s6/product/withings-body-scan-200-kg-bathroom-scales-39920069). **Treat as unreliable.** Stiftung Warentest uses German school grades, not /100; test.de says no model scored above "gut"; and these conflict with the 3,3 user report. They are likely a retailer normalisation.
- In Galaxus' own (non-Stiftung Warentest) four-scale editorial test, Withings ranked last on body fat, with fat mass almost 6 kg too low; Garmin and Beurer were about 3 kg low. — [Galaxus.at [AFF]](https://www.galaxus.at/de/page/wie-ungenau-messen-koerperfettwaagen-fuer-den-hausgebrauch-34909)

**Which? (UK, tested Jan 2025) [IND-paywalled]:**
- Which? checks body fat against a **BodPod** and weight against calibrated weights. Tested brands include Renpho, Salter, Withings, Fitbit, Etekcity and Argos models. Best Buy and Don't Buy verdicts and per-model body-fat scores are members-only. — [Which? smart bathroom scales explained](https://www.which.co.uk/reviews/bathroom-scales/article/smart-bathroom-scales-explained); [Which? body composition explained](https://www.which.co.uk/reviews/bathroom-scales/article/body-composition-explained)
- No public Which? press release, newspaper story or manufacturer release citing a Which? smart-scale grade was found.

### Inferences
- If the 3,3 report is accurate, the EUR ~300-400 Withings Body Scan scored clearly below a EUR 30 foot-only scale. That fits test.de's free headline (expensive models missed "gut") and the claim that hand sensors gave no accuracy advantage.
- Garmin Index S2's grade is unknown. It falls in the EUR 100-400 band, so it may be among the models that missed "gut", but nothing confirms this.
- The test.de reference is medical BIA, not DEXA or BodPod, so even a good grade means "agrees with clinical BIA", not "accurate against a gold standard".

### Gaps
- Official per-model Stiftung Warentest grades for the Withings Body Scan, Withings Body Smart and Garmin Index S2, including the Körperanalyse sub-grade. Paywalled; EUR 4.90 unlocks them at [test.de](https://www.test.de/koerperfettwaage-test-4645874-detail/32290!17/). No heise, Chip or Focus article listing them was found.
- Which? Best Buy / Don't Buy designations and any Withings or Garmin result: members-only; nothing public found.
- No Withings or Garmin press release citing either tester's grade was found (consistent with mediocre results, but that is an inference).

---

## 3. Status of the Garmin Index S2 class action after June 2026 (Maurer v. Garmin)

### Takeaway
The case is **live and has moved past the pleadings opening**. Garmin moved to dismiss for failure to state a claim on **21 Aug 2026**. The plaintiff filed an **amended complaint on 2 Oct 2026**, and the court entered an **order on the motion to dismiss on 5 Oct 2026** (text not public). The case is not terminated as of CourtListener's index around 22 Oct 2026. There is no class certification, settlement or merits ruling.

### Cited Findings
- *Maurer v. Garmin International, Inc.*, **No. 1:26-cv-06389 (N.D. Ill.)**, filed 29 May 2026. Defendants: Garmin International, Inc., Garmin USA, Inc., Garmin Ltd. Judge **John J. Tharp Jr.**, Magistrate Judge Beth W. Jantz. Cause 28:1332 diversity fraud; nature of suit 370 Other Fraud; plaintiff's jury demand. Plaintiff's counsel: Harper T. Segui, **Milberg Coleman Bryson Phillips Grossman PLLC**. Date terminated: none. — [CourtListener docket 73417481 [COURT]](https://www.courtlistener.com/docket/73417481/maurer-v-garmin-international-inc/) (via CourtListener search API, 23 Oct 2026)
- Docket entries (date filed, entry number, CourtListener short description; full documents not in RECAP) [COURT]: — [CourtListener](https://www.courtlistener.com/docket/73417481/maurer-v-garmin-international-inc/)
  - 2026-05-29 #1 Complaint (jury demand); #2 Civil cover sheet
  - 2026-06-01 Case assigned to Judge Tharp; magistrate consent notice; #5 Summons issued to Garmin International and Garmin USA
  - 2026-07-06 #9 Motion for extension of time; 2026-07-08 #11 Order on motion for extension of time
  - 2026-07-08 #10 Motion to appear pro hac vice; 2026-07-09 #12 Order on pro hac vice
  - **2026-08-21 #14 Motion to dismiss for failure to state a claim**
  - **2026-10-02 #18 Amended complaint**
  - **2026-10-05 #19 Order on motion to dismiss for failure to state a claim**
- Complaint allegations (secondary): foot-to-foot BIA is "incapable of accurate body composition measurements". Maurer bought the scale in Aug 2024 and saw large discrepancies against a DEXA scan. He seeks damages and a declaration that the scale cannot accurately measure body composition. The 56-page complaint cites the 2021 JMIR study, which tested Tefal, Terraillon and Withings scales but not Garmin. — [the5krunner, 5 Jun 2026 [IND blog]](https://the5krunner.com/2026/06/05/garmin-sued-accuracy-claims/); [Notebookcheck (Jun 2026) [IND]](https://www.notebookcheck.net/Did-Garmin-lie-Lawsuit-accuses-Garmin-of-misleading-customers-with-Index-S2-marketing.1316361.0.html); [Gadgets & Wearables, 3 Jun 2026](https://gadgetsandwearables.com/2026/06/03/garmin-index-s2-lawsuit/)
- Truth in Advertising lists the case as pending. — [TINA, Garmin Index S2 class action [IND]](https://truthinadvertising.org/class-action/garmin-index-s2-smart-scale/)
- Garmin's 10-Q for the quarter ended 27 Jun 2026 has only boilerplate under Legal Proceedings ("management does not expect that the results in any of these legal proceedings will have a material adverse effect"). It does not name this case. — [Garmin 2026 Q2 10-Q [VENDOR]](https://s25.q4cdn.com/374139208/files/doc_financials/2026/q2/2026_Q2_10-Q.pdf)

### Inferences
- Amending three weeks after a motion to dismiss usually means the plaintiff amended in response, and a same-week order typically strikes or denies the original motion as moot, with a new briefing schedule against the amended complaint. This is standard N.D. Ill. practice, but the 5 Oct order's text was not seen, so whether any claim was dismissed is unconfirmed.
- Expect a renewed Garmin motion to dismiss the amended complaint in late Oct to Nov 2026. A ruling is unlikely before early 2027. No consumer remedy (refund or settlement) is in sight as of Oct 2026.

### Gaps
- Text of the 5 Oct 2026 order (#19), the motion to dismiss (#14) and the amended complaint (#18): not in RECAP. PACER access or a Law360 or Top Class Actions write-up would be needed, and none was found.
- Any entries after 5 Oct 2026 (e.g. a renewed motion to dismiss) may exist but were not indexed by CourtListener at the time checked.
