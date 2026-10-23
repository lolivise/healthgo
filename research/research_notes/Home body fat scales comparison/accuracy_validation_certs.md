# Consumer home body-fat (BIA) smart scales: validation, accuracy, repeatability and certifications

Scope note: research run 2026-10-23, 17 tool calls. Evidence labels used throughout:
**[PR-IND]** peer-reviewed, no manufacturer funding · **[PR-OTHER-FUNDED]** peer-reviewed, funded by a third party (not the scale maker) · **[MFR]** manufacturer or retailer claim or white paper · **[MKT]** marketing only, nothing to verify · **[REG]** regulator database · **[ANEC]** single-user or blog, not evidence.

Buyer context: male, 36, 177 cm, ~88 kg, ~22-25 % BF, lifts 5x/week, Taiwanese. The goal is to track the trend through a cut or bulk.

---

## 1. Which models have peer-reviewed validation vs DEXA / 4C / lab BIA (bias, LoA, correlation)?

### Takeaway
Only a handful of the in-scope models have **any** independent peer-reviewed data. The single most useful paper is **Siedler et al. (Tinsley lab), Br J Nutr 2022/2023**, which tested 15 devices against a 4-compartment (4C) model. Its devices include **Withings Body Cardio, InBody H20N, Tanita BC-554 / BC-568 / UM-081, Omron HBF-306 / HBF-516, Renpho (unspecified 4-electrode), Wyze**, plus several cheap brands. Cross-sectional agreement was mediocre for every consumer scale: total error was **3.3-12.6 %BF** and CCC 0.48-0.94. I found **no peer-reviewed validation** of the Garmin Index S2, Withings Body Comp, Body Smart or Body Scan, Eufy P2/P3, Xiaomi S400 or Mi Scale 2, Hume Pod, Fitbit Aria Air or Aria 2, Etekcity, or the Renpho 8-electrode/MorphoScan models.

### Cited Findings

**Siedler MR, Rodriguez C, Stratton MT, ... Tinsley GM.** "Assessing the reliability and cross-sectional and longitudinal validity of fifteen bioelectrical impedance analysis devices." *British Journal of Nutrition*. DOI 10.1017/S0007114522003749. The journal record says 2022 (online); PMC lists 2023. [PR-IND]: Texas Tech funds paid for the devices. — [PMC10404482](https://pmc.ncbi.nlm.nih.gov/articles/PMC10404482/)
- **Sample:** 73 healthy adults aged 19-50 (35 M / 38 F), mean BMI 25.3 ± 4.7 (men 26.7 ± 4.9). Only **14 % Asian**, 56 % White, 25 % Hispanic. Reference: 4C model, criterion mean BF 24.7 ± 9.1 %. — [PMC10404482](https://pmc.ncbi.nlm.nih.gov/articles/PMC10404482/)
- **Test conditions were strictly controlled:** 24 h with no exercise; 8 h fasted with no fluid, caffeine or alcohol; 1 L of water before the fluid fast; voided bladder (USG 1.018); standing ≥10 min; visits 06:00-14:00. Real-world home use is noisier than this. — [PMC10404482](https://pmc.ncbi.nlm.nih.gov/articles/PMC10404482/)
- **Cross-sectional results vs 4C.** CE = constant error (mean bias), %BF points. TE = total error. "Equiv ±2 %" = statistically equivalent to 4C within ±2 %BF. — [PMC10404482](https://pmc.ncbi.nlm.nih.gov/articles/PMC10404482/)

| Device | CE %BF (95 % CI) | TE %BF | Equiv. ±2 % |
|---|---|---|---|
| InBody H20N (home, octapolar handle) | −0.1 (−0.9, 0.7) | **3.3** | Yes |
| Seca mBCA 515/514 (research-grade reference BIA) | −0.2 (−1.0, 0.6) | 3.3 | Yes |
| Tanita BC-568 InnerScan | −1.4 (−2.4, −0.4) | 4.4 | No |
| Omron HBF-306 (hand-to-hand) | −3.5 (−4.4, −2.5) | 5.4 | No |
| Omron HBF-516 | +3.3 (2.3, 4.4) | 5.6 | No |
| Tanita UM-081 | +0.6 (−0.8, 1.9) | 5.8 | Yes |
| **Withings Body Cardio** (foot-to-foot) | −0.4 (−1.7, 1.0) | 5.8 | Yes |
| Tanita BC-554 Ironman | +0.7 (−0.6, 2.1) | 5.8 | Yes |
| INEVIFIT | +1.4 | 6.8 | No |
| Vitagoods Form Fit | −1.1 | 6.8 | No |
| **Wyze Scale** | +3.6 (2.2, 5.0) | 6.9 | No |
| **RENPHO Scale** (model not named; foot-to-foot) | −1.4 (−3.1, 0.2) | 7.2 | No |
| Weight Watchers | +0.9 | 7.5 | No |
| HAWANA | +2.9 | 7.8 | No |
| Seca 804 | +11.7 | 12.6 | No |

- Overall ranges across devices: CCC **0.48-0.94**, SEE **3.1-7.5 %BF**. Six of the 15 devices had significant **negative proportional bias**, meaning they overestimate at low BF and underestimate at high BF. The paper does not give per-device CCC or limits of agreement in its text; they appear only in figures. — [PMC10404482](https://pmc.ncbi.nlm.nih.gov/articles/PMC10404482/); bias summary also in the Tinsley-lab write-up, [Substack](https://grundvilk.substack.com/p/about-half-of-the-body-composition)
- Configurations: device A was hand-to-hand, B-H and J-L foot-to-foot, and I, M, N, O octapolar (O = research grade). The paper does not map letters to models in its text. — [PMC10404482](https://pmc.ncbi.nlm.nih.gov/articles/PMC10404482/)
- The same lab notes that hand-to-foot analyzers had stronger agreement with 4C and lower individual errors than foot-to-foot models **from the same manufacturer** (citing White et al.). — [search summary of Tinsley-lab write-up](https://grundvilk.substack.com/p/about-half-of-the-body-composition)

**Frija-Masson J, et al.** "Accuracy of Smart Scales on Weight and Body Composition: Observational Study." *JMIR mHealth uHealth* 2021;9(4):e22487. PMID 33929337, NCT03803098. [PR-OTHER-FUNDED]: funded via an MSD France donation to the AP-HP Foundation; no scale-maker funding. — [PMC8122302](https://pmc.ncbi.nlm.nih.gov/articles/PMC8122302/)
- **Devices:** Téfal Body Partner (n=53), Terraillon DietPack (n=52), **Nokia/Withings Body Cardio** (n=48). Reference: GE Lunar iDXA. **Population:** hospital patients referred for DEXA (obesity, CKD, steroids); median BMI 28-31. This is not an athletic sample. — [PMC8122302](https://pmc.ncbi.nlm.nih.gov/articles/PMC8122302/)
- **Weight error (median, IQR):** Body Partner 0.3 kg (−0.1, 0.7); DietPack 0 kg (−0.4, 0.3); **Body Cardio 0.25 kg (−0.10, 0.52)**. — [PMC8122302](https://pmc.ncbi.nlm.nih.gov/articles/PMC8122302/)
- **Fat-mass error vs DXA:** Body Partner −2.2 kg (−5.8, 1.3); DietPack −4.4 kg (−6.6, 0); **Body Cardio −3.7 kg (−8.0, +0.28)**, so it underestimated FM, with an IQR spanning ~8 kg. Muscle-mass error for Body Cardio was +4.0 kg (0.1, 7.6). BF % and numeric LoA were not reported. Authors: *"Smart scales are not accurate for body composition and should not replace DEXA in patient care."* — [PMC8122302](https://pmc.ncbi.nlm.nih.gov/articles/PMC8122302/)
- Data-quality flag: the abstract's muscle-mass errors duplicate the fat-mass numbers and conflict with the Results section. — [PMC8122302](https://pmc.ncbi.nlm.nih.gov/articles/PMC8122302/)

**Other device and population evidence**
- **Chen et al., PLOS One 2016 (Tanita BC-418, an octapolar lab analyzer, not a home scale), n=711 Taiwanese vs DXA:** BIA mean 22.54 ± 9.48 %BF vs DXA 26.26 ± 11.18 %. BIA **underestimated** BF in every subgroup except the leanest men (DXA BF < 15 %), where it overestimated. [PR-IND] — [PMC4965215](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4965215/)
- **Wang & Hui 2015, four commercial BIA scales vs DXA in Chinese children/adolescents:** agreement was poor for 3 of 4 scales. Embedded equations need population-specific validation. [PR-IND] — [PMC4475745](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4475745/)
- **InBody lab analyzers (230/720/770) vs DXA:** reliable in men and women, but with systematic bias: they underestimate BF % and FM and overestimate FFM. These are lab models, not the H20/H30 home models. [PR; funding not checked] — [Kennesaw summary](https://digitalcommons.kennesaw.edu/facpubs/4673)
- **Recent consumer hand-to-foot and foot-to-foot devices vs DXA (n=83, Frontiers in Nutrition 2025):** both significantly **underestimated** BF % with poor agreement, and the error varied with BF level. [PR; devices and funding not extracted] — [Frontiers fnut.2025.1689031](https://www.frontiersin.org/articles/10.3389/fnut.2025.1689031/full)
- **Garmin Index S2 / Xiaomi:** no peer-reviewed DXA or 4C validation exists as of 2025-2026, per independent reviewers. One forum user's DEXA comparison found the Index S2 the least accurate of the scales they tried [ANEC]. Saga's informal test ranked the Xiaomi Mi Body Composition Scale 2 among the least accurate (average variance 10.68 %) [ANEC / non-scientific]. — [HMMüller review](https://www.hmmuller.com/post/garmin-index-s2-review-is-it-worth-it-in-2025-10-month-real-world-test); [Garmin forum](https://forums.garmin.com/sports-fitness/healthandwellness/f/index-s2-smart-scale/359974/index-s2-smart-scale-vs-dexa-scan); [Saga](https://www.saga.co.uk/magazine/health-and-wellbeing/how-accurate-are-smart-scales)
- **Registered but unpublished trial:** NCT05026697, "Validity and Reliability of Commercially Available BIA Devices." It includes Renpho and other home scales vs a 4C model and is almost certainly the protocol behind Siedler et al. — [ClinicalTrials.gov NCT05026697](https://clinicaltrials.gov/study/NCT05026697)

### Inferences
- **Weight function:** every studied scale reads weight within roughly ±0.3 kg of a reference. Weight is the trustworthy number on any of these scales.
- **Absolute BF %:** even the best consumer scales are off by ~3-6 %BF total error for an individual, and most foot-to-foot scales are worse (6-8 %). Only the InBody H20N matched research-grade BIA (TE 3.3 %), and the H20N is a hand-and-foot (octapolar) design. **Withings Body Cardio** is the only Withings model with independent data. It was unbiased on average vs 4C in young healthy adults (TE 5.8 %), but underestimated FM by ~3.7 kg in obese hospital patients. Later Withings models (Body Comp, Body Smart, Body Scan) presumably share related algorithms, but that is **unverified**.
- **Proportional bias:** for a muscular man at ~22-25 % BF, foot-to-foot scales with negative proportional bias, and BIA in Taiwanese men generally (Chen 2016), will tend to **under-read** BF %. A muscular build changes the impedance-to-FFM relationship, so the error could go either way. Expect a stable personal offset, not a random one.

### Gaps
- No peer-reviewed validation found for: Garmin Index S2; Withings Body Comp, Body Smart, Body Scan, Body+; Eufy P2/P3; Xiaomi S400 / Mi Scale 2; Hume Pod / Pod 2.0; Fitbit Aria Air / Aria 2; Etekcity; Renpho Elis / MorphoScan / 8-electrode; InBody H30; Omron BF-series. (Fitbit Aria and Omron HBF-514 papers are believed to exist, but they were not retrieved and are not cited.)
- No study found in resistance-trained men specifically for any consumer scale.
- Per-device CCC and Bland-Altman LoA from Siedler et al. are in figures only and were not extracted.

---

## 2. Studies of tracking CHANGE over time (not single-point accuracy)

### Takeaway
Only **Siedler et al.** tested consumer scales longitudinally against a 4C criterion, with 37 people retested after 12-16 weeks. Average bias in change was small (−0.4 to +1.3 %BF), but **total error of individual change was ~1.9-2.9 %BF** across devices, with change CCC only 0.37-0.78. Around half the devices showed poor longitudinal validity. Devices that were "equivalent within ±1 %" for change included **Renpho, Wyze, Omron HBF-306, InBody H20N** and the Seca reference. **Withings Body Cardio, Tanita BC-554/BC-568 and Omron HBF-516** were not equivalent, because they tended to overstate BF increases by ~0.6-0.8 %. I found no study of a consumer scale during a structured weight-loss or muscle-gain intervention.

### Cited Findings
- Longitudinal results vs 4C, n=37, 12-16 weeks. 4C mean change was only **+0.2 ± 2.9 %BF**, so this was a free-living cohort, not a cut. — [PMC10404482](https://pmc.ncbi.nlm.nih.gov/articles/PMC10404482/)

| Device | Device-measured change, mean (SD) %BF | CE of change (95 % CI) | Total error of change | Equiv. ±1 % |
|---|---|---|---|---|
| InBody H20N | −0.2 (2.3) | −0.4 (−1.0, 0.3) | 2.1 | Yes |
| Seca mBCA 515/514 (research) | 0.5 (2.5) | 0.3 (−0.4, 1.0) | 2.1 | Yes |
| Omron HBF-306 | 0.4 (2.0) | 0.2 (−0.5, 0.9) | 2.1 | Yes |
| Wyze | 0.4 (2.2) | 0.3 (−0.4, 1.0) | 2.1 | Yes |
| INEVIFIT | 0.2 (1.6) | 0.0 | 2.2 | Yes |
| RENPHO | −0.1 (1.3) | −0.3 (−1.1, 0.6) | 2.5 | Yes |
| Weight Watchers | −0.1 (1.4) | −0.2 | 2.5 | Yes |
| Vitagoods | −0.1 (1.3) | −0.3 | 2.5 | Yes |
| HAWANA | 0.1 (1.5) | 0.0 | 2.6 | Yes |
| Withings Body Cardio | 0.8 (2.6) | **0.6 (0.0, 1.2)** | 1.9 | No |
| Tanita BC-554 | 0.8 (2.4) | 0.6 (0.0, 1.3) | 2.0 | No |
| Tanita BC-568 | 0.9 (2.6) | 0.7 (0.1, 1.3) | 1.9 | No |
| Tanita UM-081 | 0.8 (2.5) | 0.7 (0.0, 1.3) | 1.9 | No |
| Omron HBF-516 | 1.0 (2.6) | 0.8 (0.2, 1.4) | 1.9 | No |
| Seca 804 | 1.4 (3.6) | 1.3 (0.4, 2.2) | 2.9 | No |

- Longitudinal CCC ranged **0.37-0.78**, SEE **1.7-2.6 %BF**, and 6-7 devices showed proportional bias in change. Authors: octapolar and select foot-to-foot devices "may hold potential utility for the tracking of body composition over time." — [PMC10404482](https://pmc.ncbi.nlm.nih.gov/articles/PMC10404482/)
- The Tinsley-lab summary describes "relatively poor longitudinal validity demonstrated in approximately half" of the devices. — [Substack summary](https://grundvilk.substack.com/p/about-half-of-the-body-composition)
- **Fat mass from BIA:** fat mass derived from FFM agreed with DXA at the group level but showed systematic trends at the individual level (n=288). [PR] — [search summary, unipd](https://research.unipd.it/handle/11577/3567109)
- **Foot-to-foot vs DXA in overweight adolescents (Br J Nutr 2003):** limits of agreement were much wider than hand-to-foot, and "FF-BIA and DXA are not interchangeable methods." [PR, older] — [Cambridge PDF](https://www.cambridge.org/core/services/aop-cambridge-core/content/view/928A9C4E4974483BCF1D5F7FE9C79434/S0007114503002113a.pdf/evaluation-of-two-foot-to-foot-bioelectrical-impedance-analysers-to-assess-body-composition-in-overweight-and-obese-adolescents.pdf)

### Inferences
- A device whose change SD is **smaller** than the criterion's (Renpho 1.3, Vitagoods 1.3, Weight Watchers 1.4 vs 4C 2.9) is "equivalent" on average partly because it barely moves. That damping suggests these cheap foot-to-foot scales lean heavily on weight, height, age and sex rather than impedance. They will track **weight** changes and convert them to BF %, which is useless for telling fat loss from lean loss. Withings, Tanita and InBody showed change SDs close to the criterion (2.3-2.6), which suggests real impedance-driven signal, at the cost of a ~+0.6-0.8 % upward drift in Withings and Tanita.
- **Noise vs signal for this buyer:** losing 0.3-0.5 kg fat/week at 88 kg and ~23.5 % BF changes BF % by about **0.3-0.5 points/week**. With an individual change error of ~2 %BF, under lab-controlled conditions, a single pair of readings can only resolve a true change of ~4-5 %BF with confidence. That means **8-12+ weeks** of a cut, unless many readings are averaged. Weekly BF % readings will be dominated by noise. A 7-14-day rolling average of weight is the better weekly signal, with BIA BF % checked as a monthly trend.

### Gaps
- No consumer-scale study during an actual caloric-deficit or hypertrophy intervention, and none in resistance-trained men.
- No study of whether 8-electrode consumer scales (Withings Body Scan, Renpho MorphoScan, Eufy P3, Xiaomi S400 dual-frequency) track change better than foot-to-foot ones; the only octapolar consumer device tested longitudinally is the InBody H20N.

---

## 3. Test-retest reliability / precision by model and technology

### Takeaway
**Same-session** precision of consumer BIA scales is excellent: precision error 0.0-0.49 %BF, least significant change 0-1.36 %BF. That figure is misleading, because several devices are "too precise" and probably don't re-measure impedance meaningfully. **Day-to-day** reliability is the relevant number for trend tracking. It is worse, and driven by hydration, glycogen and timing. I found no per-model day-to-day CV for any in-scope consumer scale.

### Cited Findings
- **Siedler et al.:** precision error 0.0-0.49 %, LSC 0.0-1.36 %, from two consecutive readings at the same visit. Devices B, C, E, F and H had PE 0.0-0.04 %, which the authors flagged as suspiciously low. The octapolar devices M-O had the **highest** PE, and only M and N had LSC > 0.80 %. The letters are not mapped to models in the text. — [PMC10404482](https://pmc.ncbi.nlm.nih.gov/articles/PMC10404482/)
- **Time of day, 2017 study (Thieme journal), 18 well-trained students, BIA on 4 consecutive days, AM and PM:** no systematic bias between repeats. ICC was 0.72-0.99 in the morning vs 0.61-0.99 in the afternoon, and the minimal real change ranged **4.2-41.5 %** depending on the index. The authors advise morning measurement. [PR] — [Thieme s-0043-113999](https://www.thieme-connect.de/products/ejournals/pdf/10.1055/s-0043-113999.pdf)
- **Frontiers in Nutrition 2024, InBody 770 (lab octapolar), 14 military-age adults, 5 visits over 3 weeks**, same time of day after ≥48 h without strenuous exercise: very high test-retest reliability, with small biological variability. [PR] — [Frontiers fnut.2024.1491931](https://frontiersin.org/journals/nutrition/articles/10.3389/fnut.2024.1491931/text)
- **Athletic males (n=32), short-term precision across methods:** consecutive-day precision error for fat mass was higher than same-day error for DXA, BOD POD and BIS. Day-to-day biology adds noise beyond device noise. [PR; numbers not extracted] — [Short-term precision error, resistance-trained male athletes](https://lida.sport-iat.de/ta/Record/4067868)

### Inferences
- Same-day duplicate CV is not a usable proxy for trend precision. For a lifter training 5x/week, glycogen and water swings will produce day-to-day BF % jitter of probably ±1-2 %BF on a foot-to-foot scale. That magnitude is an inference, not a measured figure for any in-scope model.
- Octapolar devices are slightly less precise within a session but more valid (lower TE) and more responsive to real change.

### Gaps
- No published day-to-day CV or MDC for Withings, Garmin, Renpho, Eufy, Xiaomi, Hume, Fitbit or InBody H20/H30 under home conditions.

---

## 4. Known systematic biases (lean/muscular men, Asians, hydration, timing, training, carbs/sodium)

### Takeaway
BIA estimates water and then infers fat, so anything that shifts water or its distribution moves the reading. Dehydration or sweating raises the BF % reading, and fluid loading or high glycogen lowers it. Bias also depends on adiposity, with a sign flip in lean men, and on population: Taiwanese DXA data show BIA under-reading BF by ~3.7 points on average.

### Cited Findings
- **Taiwanese adults, Tanita BC-418 vs DXA, n=711:** BIA mean BF 22.54 % vs DXA 26.26 %, an underestimate of ~3.7 points. BIA **over**estimated only in men with DXA BF < 15 %; adiposity level drives accuracy. — [Chen et al. 2016, PMC4965215](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4965215/)
- **Asian foot-to-foot BIA model (Wu et al., Nutrition Journal 2015), n=554 healthy Asian adults vs DXA:** an all-subjects FFM model reached r² 0.92, SEE 3.17 kg. In men, bias ranged about −2.3 ± 2.5 kg to +2.1 ± 3.2 kg FFM across body-fat strata, so the **sign of the bias shifts with fatness**. — [PMC4489024](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4489024/)
- **Chinese adults (n=704):** a separate hand-to-hand equation for men (r² 0.919, SEE 2.164 kg) shows population-specific equations are needed. — [PMC5084040](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5084040/)
- **Hydration and exercise (manufacturer guidance):** lower hydration gives a higher BF reading and vice versa; sweating temporarily raises the BF reading. [MFR] — [Tanita](https://tanita.com/posts/why-do-my-measurements-change-throughout-the-day); [Tanita EU support](https://support.tanita.eu/en/support/solutions/articles/60000687548). After a workout there is less water for current flow, which may raise BF %. [MFR] — [Conair/Weight Watchers manual](https://www.conair.com/on/demandware.static/-/Library-Sites-usConairShared/default/dw66b7ba39/Instructional%20Booklets/WW721ZF.pdf). iHealth advises measuring ≥3 h after waking, meals or intense exercise. [MFR, not trial-based] — [iHealth](https://support.ihealthlabs.com/hc/en-us/articles/8617954033933-Why-does-my-body-fat-vary)
- **Acute intake, 2026 study, n=98:** no significant time × condition effect on BF % after 600 mL water or 300 g banana. The fixed-order design limits that inference. [PR] — per search summary; source among [medsci v23p3547](https://www.medsci.org/v23p3547.pdf) / [Frontiers 2024](https://frontiersin.org/journals/nutrition/articles/10.3389/fnut.2024.1491931/text) (exact attribution not confirmed)
- **InBody lab analyzers in exercise-trained adults:** the InBody 770 overestimated FFM and underestimated FM and BF % vs DXA (42 M / 113 F). [PR] — [J Exercise & Nutrition](https://www.journalofexerciseandnutrition.com/index.php/JEN/article/view/44)

### Inferences
- For a ~23 % BF Taiwanese lifter, expect a consumer scale to **under-read BF % by a few points** relative to DXA. That offset should be roughly stable, so trends remain usable if conditions are standardized.
- During a **cut**, glycogen and water depletion (low carb, high training volume) can make BIA show **less** fat loss than truly occurred. A diet break or refeed (glycogen and water up) can show an abrupt BF % **drop** that is not fat. During a **bulk**, the reverse happens. These artefacts are the same order of magnitude (~1-2 %BF) as a month of real fat loss.
- The practical protocol is to measure the same way each time: on waking, after voiding, before food, fluid or training, and never after the 5x/week sessions. Average weekly, and judge BF % on 4-week trends.

### Gaps
- No quantified per-model effect sizes for post-training, high-sodium or high-carb days on consumer scales; the evidence found is manufacturer guidance.
- The 2016 study of 20 men (~0.8 %BF diurnal change for BIA) appeared in a search summary without a confirmable source and is excluded.

---

## 5. Certifications: medical-device status, FDA / TGA / EU MDR / OIML

### Takeaway
In the US, a body-composition analyzer falls under **21 CFR 870.2770**. Product code **MNW** needs a 510(k); **PUH** is its 510(k)-**exempt** Class II counterpart, created under the 21st Century Cures Act. Most consumer scales can therefore be sold legally with **no clearance at all**, and "FDA registered" means only establishment registration and listing. The well-publicized **Withings Body Scan FDA clearance (K230812, Aug 2023)** is for the **Scan Monitor 2.0 6-lead ECG** (21 CFR 870.2340, code DPS), **not** body composition. Renpho's "FDA approved" and Hume's "FDA-cleared" claims could not be verified in any FDA record found.

### Cited Findings
- **FDA classification:** PUH is the "class II exempt counterpart of MNW" under 21 CFR 870.2770, exempt from 510(k) subject to 870.9 limitations. [REG] — [FDA TPLC PUH](https://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfTPLC/tplc.cfm?id=1843); [beudamed PUH](https://beudamed.com/fda_classifications/PUH)
- **Body-composition 510(k) clearances do exist under MNW**, e.g., a Tanita analyzer (**K090479**, July 2009) and Jawon Medical (**K140045**, Feb 2015). [REG mirror] — [beudamed K090479](https://beudamed.com/fda510ks/K090479); [innolitics K140045](https://fda.innolitics.com/device/K140045)
- **Withings Scan Monitor 2.0, K230812:** cleared 2023-08-23, Class II, 21 CFR 870.2340 (electrocardiograph), product codes DPS (+DXH). Indication: 2-channel ECG (leads II/III recorded; I, aVF, aVL calculated). The earlier Scan Monitor, **K201456**, was cleared 2021-10-05 under the same regulation. [REG] — [FDA K230812](https://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfpmn/pmn.cfm?ID=K230812); [FDA K230812 PDF](https://www.accessdata.fda.gov/cdrh_docs/pdf23/K230812.pdf); [FDA K201456](https://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfpmn/pmn.cfm?ID=K201456)
- Withings press materials frame the Body Scan as "the first health station to receive FDA clearance" for **AFib detection via 6-lead ECG**. Segmental BIA is described as a device feature, not a cleared indication. [MFR] — [Withings press release PDF](https://media.withings.com/press/press-releases/body-scan/withings-body-scan-us-fda-clearance-082423.pdf); [Medical Design & Development](https://www.medicaldesigndevelopment.com/topics/devices/news/22871776/withings-earns-fda-clearance-for-smart-scale-with-builtin-ecg)
- **Renpho:** a Gizmodo Australia review relays Renpho saying its scales are "FDA approved." Best Buy listings claim accuracy within 2 % of physician scales. No 510(k) or approval record was found. [MKT] — [Gizmodo AU](https://gizmodo.com.au/?p=1092424); [Best Buy Renpho 8-electrode](https://www.bestbuy.com/product/renpho-8-electrode-digital-scale-with-bmi-body-fat-muscle-mass-body-composition-analyzer-larger-platform-black/J39HPQ7JX5/sku/12698860)
- **Hume Pod:**
  - Hume claims "98 % DEXA-like accuracy" [MKT]. — [Hume Health](https://humehealth.com/en-ch/pages/pdp8-v8-01)
  - Equinox's listing cites an "independent study conducted by Socotech" with results "within ±2 % of DEXA", while elsewhere on the same page claiming "within 0.2 %" for BF %. The two claims differ tenfold, and the Socotech study could not be found. [MFR/MKT, internally inconsistent] — [Equinox listing](https://shop.equinox.com/products/the-hume-pod-partner-us-only)
  - Blogs calling it "FDA-cleared" cite no database entry [ANEC]. — [blog](https://old.michaelbreed.com/hot-zone/is-hume-health-body-pod-accurate-1771240769)
  - A 2026 review describes it as a general-wellness device and notes its validation claims are non-clinical. [non-PR] — [Newswire review](https://www.newswire.com/news/hume-health-body-pod-review-2026-accuracy-features-verdict)
- **InBody H20:** the manufacturer claims "over 98 % agreement with DEXA" for its technology. [MFR] — [InBody USA H20](https://shop.inbodyusa.com/collections/h30-h20/products/h20)
- **Tanita:** claims "99 % agreement" with a research-grade benchmark. [MFR] — [Tanita](https://tanita.com/posts/beyond-dexa-the-science-that-makes-tanita-scales-more-accurate)

### Inferences
- An FDA clearance on a smart scale almost never covers the body-fat number. Withings' clearances are for ECG, and the BIA features ride along as wellness features. Brand regulatory status says nothing about body-fat trend precision.
- "98 % agreement / 98 % accurate" claims (Hume, InBody) are typically correlation coefficients or group means, which say nothing about individual error. Siedler et al. show group-mean bias near 0 alongside individual TE of ~6 %BF.

### Gaps
- **TGA ARTG (Australia):** no ARTG entries were retrieved for any in-scope scale; the search returned nothing. Check model numbers directly at tga.gov.au/resources/artg.
- **EU MDR CE class IIa / EUDAMED:** not verified for any model. Some Tanita and InBody professional models carry medical CE marks, but this was not confirmed for the home models.
- **OIML R76 / NAWI class III (weighing):** no evidence found that any in-scope consumer smart scale holds an OIML R76 or NAWI class III certificate. Consumer bathroom scales are generally not legal-for-trade instruments. Unverified either way.
- No FDA record checked for Garmin Index S2, Eufy, Xiaomi, Fitbit, Omron HBF/BF home scales, or InBody H20/H30. InBody and Omron may have 510(k)s for professional or BP devices; not confirmed.

---

## 6. Independent vs manufacturer-funded testing

### Takeaway
The two key consumer-scale validation papers (Siedler 2022/23; Frija-Masson 2021) are **not funded by any scale maker**. Siedler's senior author has disclosed in-kind equipment support from InBody (Biospace) and other body-composition companies. Every "98-99 % accuracy" figure for Hume, InBody, Tanita and Renpho is manufacturer- or retailer-originated.

### Cited Findings
- **Siedler et al.:** devices bought with Texas Tech funds; "No external entity played any role in the present work." G. M. Tinsley discloses in-kind equipment support from Size Stream, Naked Labs, Prism Labs, RJL Systems, MuscleSound and **Biospace (InBody)**, and research funding from Prism Labs. The best performer in the paper was the InBody H20N, so this COI is worth noting, though the study was independently funded. — [PMC10404482](https://pmc.ncbi.nlm.nih.gov/articles/PMC10404482/)
- **Frija-Masson et al.:** funded by an MSD France donation to the AP-HP Foundation; one author has unrelated respiratory-industry COIs; no scale-maker funding. — [PMC8122302](https://pmc.ncbi.nlm.nih.gov/articles/PMC8122302/)
- **Hume's "Socotech" study:** not published and not locatable. — [Equinox listing](https://shop.equinox.com/products/the-hume-pod-partner-us-only)

### Inferences
- **Strongest independent evidence by in-scope brand:**
  - **InBody H20N** (best absolute accuracy, good change tracking)
  - **Withings Body Cardio** (unbiased cross-sectionally in healthy adults, realistic change response but a +0.6 % upward drift in change)
  - **Tanita BC-554/568** (similar to Withings)
  - **Renpho foot-to-foot** (equivalent change on average but a damped, weight-driven response)
  - **Wyze** and **Omron HBF-516** (biased)
- **Garmin, Eufy, Xiaomi, Hume, Fitbit and the newer Withings and Renpho 8-electrode models have no independent validation.**

### Gaps
- No independent lab test located for Hume Pod / Pod 2.0, Garmin Index S2, Eufy P2/P3, Xiaomi S400, Withings Body Comp, Body Smart or Body Scan, or Renpho MorphoScan.
- The Fitbit Aria peer-reviewed literature was not retrieved within the search budget.
