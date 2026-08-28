# Corpus Manifest — IP-SAKTI Sahayak

Authoritative document manifest for the MVP Intellectual Property & Regulatory Legal Corpus.
Every document is mapped to exactly one of the **5 Qdrant Cloud collections** described in `context.md §3a`.

---

## Summary by Collection

| Collection | Target Content | Count in MVP Manifest | Chunking Strategy Class (`chunker.py`) |
|---|---|:---:|---|
| `legal_statutory` | Indian Acts, Rules, Regulations, Official Patent/GI Guidelines | 16 | `LegalStatutoryChunker` (Section/Subsection level: 200–800 tokens) |
| `standards_formulations` | API/AFI monographs, First-Schedule classical texts, PCIM&H standards | 7 | `StandardsFormulationsChunker` (Monograph/Formulation entry level) |
| `procedural_forms` | NBA ABS Application Forms, SBB Checklists, AYUSH Licensing Forms | 8 | `ProceduralFormsChunker` (Form Section/Field-group level: 150–400 tokens) |
| `international_export` | TRIPS, CBD/Nagoya Protocol, WIPO GRATK Treaty, EU/US Herbal Regulations | 8 | `InternationalExportChunker` (Article level: 300–800 tokens) |
| `case_law_prior_art` | Landmark TKDL prior art revocation dossiers (Turmeric, Neem, Basmati) | 3 | `CaseLawChunker` (Paragraph level with full case metadata on every chunk) |
| **Total** | | **42** | |

---

## 1. `legal_statutory` Collection (Indian Statutes, Rules & Official Guidelines)

### DOC-IN-PAT-001: The Patents Act, 1970
- **Document ID**: `doc_in_patents_act_1970`
- **Corpus Collection**: `legal_statutory`
- **Jurisdiction**: `INDIA`
- **Document Type**: `STATUTE`
- **Authority**: Legislative Department, Ministry of Law and Justice, Government of India
- **Effective / Amendment Status**: Act No. 39 of 1970, as amended by Patents (Amendment) Act 2005
- **Key Provisions**:
  - `Section 3(p)`: Inventions which in effect are traditional knowledge or an aggregation/duplication of known properties of traditionally known component(s) are NOT patentable.
  - `Section 3(d)`: Mere discovery of a new form of a known substance which does not result in the enhancement of the known efficacy is not an invention.
  - `Section 3(e)`: Mere admixture resulting only in aggregation of properties is not an invention.
  - `Section 10(4)(d)(ii)`: Mandatory disclosure of the source and geographical origin of biological material used in an invention.
  - `Section 25(1)(k) & 25(2)(k)`: Opposition on grounds that invention was anticipated by traditional knowledge.
  - `Section 64(1)(p)`: Revocation of patent if invention was anticipated having regard to traditional knowledge (TKDL ground).
- **Official Source URL**: https://www.indiacode.nic.in/handle/123456789/1392
- **Verification Status**: VERIFIED

### DOC-IN-PAT-002: The Patents Rules, 2003 (as amended up to 2024)
- **Document ID**: `doc_in_patents_rules_2024`
- **Corpus Collection**: `legal_statutory`
- **Jurisdiction**: `INDIA`
- **Document Type**: `RULE`
- **Authority**: Department for Promotion of Industry and Internal Trade (DPIIT), Ministry of Commerce and Industry
- **Effective / Amendment Status**: As amended by the Patents (Amendment) Rules, 2024 (G.S.R. 190(E), 15 March 2024)
- **Key Provisions**: Form 1 declarations, Form 2 provisional/complete specifications, Form 27 working of patents, biological material source disclosure requirements.
- **Official Source URL**: https://ipindia.gov.in/rules-patents.htm
- **Verification Status**: VERIFIED

### DOC-IN-PAT-003: CGPDTM Guidelines for Examination of Patent Applications relating to Traditional Knowledge & Biological Material
- **Document ID**: `doc_in_cgpdtm_tk_guidelines_2012`
- **Corpus Collection**: `legal_statutory`
- **Jurisdiction**: `INDIA`
- **Document Type**: `GUIDELINE`
- **Authority**: Office of the Controller General of Patents, Designs and Trade Marks (CGPDTM), IP India
- **Effective / Amendment Status**: Published 2012; operative guideline for Indian Patent Office examiners
- **Key Provisions**: Guiding principles 1 to 5 for examination of claims touching Ayurveda/Siddha/Unani; screening against TKDL; combination vs. synergistic formulations.
- **Official Source URL**: https://ipindia.gov.in/writereaddata/Portal/IPOGuidelines/1_37_1_traditional-knowledge-08march2013.pdf
- **Verification Status**: VERIFIED

### DOC-IN-PAT-004: Manual of Patent Office Practice and Procedure (Chapter on Pharmaceutical & TK Inventions)
- **Document ID**: `doc_in_manual_patent_practice_2019`
- **Corpus Collection**: `legal_statutory`
- **Jurisdiction**: `INDIA`
- **Document Type**: `MANUAL`
- **Authority**: CGPDTM, DPIIT, Ministry of Commerce and Industry
- **Effective / Amendment Status**: Updated 2019 edition
- **Key Provisions**: Procedural requirements for searching TK databases; NBA clearance requirements prior to grant under Section 6 of the Biological Diversity Act.
- **Official Source URL**: https://ipindia.gov.in/manual-patents.htm
- **Verification Status**: VERIFIED

### DOC-IN-TM-001: The Trade Marks Act, 1999
- **Document ID**: `doc_in_trademarks_act_1999`
- **Corpus Collection**: `legal_statutory`
- **Jurisdiction**: `INDIA`
- **Document Type**: `STATUTE`
- **Authority**: Legislative Department, Ministry of Law and Justice
- **Effective / Amendment Status**: Act No. 47 of 1999
- **Key Provisions**: Section 9 (Absolute grounds for refusal - descriptive Ayurvedic terms), Section 11 (Relative grounds), Class 5 (Ayurvedic pharmaceutical and medicinal preparations), Class 3 (Ayurvedic cosmetics/skincare), Class 30/32 (Ayurveda Aahara/herbal teas).
- **Official Source URL**: https://www.indiacode.nic.in/handle/123456789/1993
- **Verification Status**: VERIFIED

### DOC-IN-TM-002: The Trade Marks Rules, 2017
- **Document ID**: `doc_in_trademarks_rules_2017`
- **Corpus Collection**: `legal_statutory`
- **Jurisdiction**: `INDIA`
- **Document Type**: `RULE`
- **Authority**: DPIIT, Ministry of Commerce and Industry
- **Effective / Amendment Status**: G.S.R. 199(E), 6 March 2017
- **Key Provisions**: Classification of goods (Nice Classification), Form TM-A application procedures for herbal and AYUSH brands.
- **Official Source URL**: https://ipindia.gov.in/rules-trademarks.htm
- **Verification Status**: VERIFIED

### DOC-IN-GI-001: The Geographical Indications of Goods (Registration and Protection) Act, 1999
- **Document ID**: `doc_in_gi_act_1999`
- **Corpus Collection**: `legal_statutory`
- **Jurisdiction**: `INDIA`
- **Document Type**: `STATUTE`
- **Authority**: Legislative Department, Ministry of Law and Justice
- **Effective / Amendment Status**: Act No. 48 of 1999
- **Key Provisions**: Section 2(e) (Definition of GI for agricultural and natural goods), Section 9 (Prohibition of registration of certain terms), Section 20-22 (Infringement and Authorized User registration for indigenous herbal crops).
- **Official Source URL**: https://www.indiacode.nic.in/handle/123456789/1994
- **Verification Status**: VERIFIED

### DOC-IN-GI-002: The Geographical Indications of Goods Rules, 2002
- **Document ID**: `doc_in_gi_rules_2002`
- **Corpus Collection**: `legal_statutory`
- **Jurisdiction**: `INDIA`
- **Document Type**: `RULE`
- **Authority**: DPIIT, Ministry of Commerce and Industry
- **Key Provisions**: Application procedures for GI registration of Ayurvedic medicinal herbs (e.g. Navara rice, Alleppey Green Cardamom, Malabar Pepper).
- **Official Source URL**: https://ipindia.gov.in/rules-gi.htm
- **Verification Status**: VERIFIED

### DOC-IN-BDA-001: The Biological Diversity Act, 2002 (as amended by Amendment Act 2023)
- **Document ID**: `doc_in_bda_act_2023`
- **Corpus Collection**: `legal_statutory`
- **Jurisdiction**: `INDIA`
- **Document Type**: `STATUTE`
- **Authority**: Ministry of Environment, Forest and Climate Change (MoEFCC), Government of India
- **Effective / Amendment Status**: Act No. 18 of 2003, as amended by Biological Diversity (Amendment) Act, 2023 (Act No. 10 of 2023)
- **Key Provisions**:
  - `Section 3`: Requirement of NBA approval for non-Indian citizens/entities to access biological resources.
  - `Section 4`: Transfer of results of research relating to biological resources.
  - `Section 6`: Mandatory prior approval of NBA before applying for any IPR based on biological resources/knowledge obtained from India.
  - `Section 7`: Prior intimation to State Biodiversity Board (SBB) for Indian entities/practitioners.
  - `Section 40`: Exemption of normally traded commodities (NTAC list).
  - `2023 Amendment Relief`: Exemption for registered Ayush practitioners and cultivated medicinal plants from certain prior intimation burdens under specified conditions.
- **Official Source URL**: https://www.indiacode.nic.in/handle/123456789/2046
- **Verification Status**: VERIFIED

### DOC-IN-BDA-002: The Biological Diversity Rules, 2024 / 2004
- **Document ID**: `doc_in_bda_rules_2024`
- **Corpus Collection**: `legal_statutory`
- **Jurisdiction**: `INDIA`
- **Document Type**: `RULE`
- **Authority**: National Biodiversity Authority (NBA) / MoEFCC
- **Effective / Amendment Status**: Rules governing computation of benefit sharing fee, timelines for IPR approval (Form III), and NTAC notifications.
- **Official Source URL**: http://nbaindia.org/content/17/14/1/rules.html
- **Verification Status**: VERIFIED

### DOC-IN-BDA-003: Guidelines on Access to Biological Resources and Associated Knowledge and Benefits Sharing Regulations, 2014
- **Document ID**: `doc_in_nba_abs_guidelines_2014`
- **Corpus Collection**: `legal_statutory`
- **Jurisdiction**: `INDIA`
- **Document Type**: `REGULATION`
- **Authority**: National Biodiversity Authority (NBA)
- **Effective / Amendment Status**: S.O. 3013(E), 21 November 2014
- **Key Provisions**: Calculation matrix for ABS fee: 0.1% to 0.5% of ex-factory sale price for commercial utilization; 2% to 5% of royalty on commercialized IPR.
- **Official Source URL**: http://nbaindia.org/uploaded/pdf/Gazette_Notification_ABS_Guidelines.pdf
- **Verification Status**: VERIFIED

### DOC-IN-DRUG-001: The Drugs and Cosmetics Act, 1940 (Chapter IVA — Provisions Relating to Ayurvedic, Siddha and Unani Drugs)
- **Document ID**: `doc_in_drugs_cosmetics_act_1940`
- **Corpus Collection**: `legal_statutory`
- **Jurisdiction**: `INDIA`
- **Document Type**: `STATUTE`
- **Authority**: Ministry of Health and Family Welfare / Ministry of Ayush
- **Effective / Amendment Status**: Act No. 23 of 1940, Chapter IVA inserted by Act 13 of 1964
- **Key Provisions**:
  - `Section 3(a)`: Definition of Ayurvedic, Siddha or Unani (ASU) drug.
  - `Section 33A - 33P`: Licensing, manufacturing, misbranded drugs, adulterated drugs, spurious drugs, ASU Technical Advisory Board (ASUTAB), and First Schedule book listing.
- **Official Source URL**: https://www.indiacode.nic.in/handle/123456789/2263
- **Verification Status**: VERIFIED

### DOC-IN-DRUG-002: The Drugs and Cosmetics Rules, 1945 (Part XVI to XIX — ASU Licensing & Labeling)
- **Document ID**: `doc_in_drugs_cosmetics_rules_1945`
- **Corpus Collection**: `legal_statutory`
- **Jurisdiction**: `INDIA`
- **Document Type**: `RULE`
- **Authority**: Ministry of Ayush / Central Drugs Standard Control Organization (CDSCO)
- **Effective / Amendment Status**: Part XVI (Licensing), Part XVI-A (Approval of Institutions), Part XVII (Labeling, Packing), Part XVIII (Govt Analysts/Inspectors)
- **Key Provisions**: Rule 151-170, Form 24D (Manufacturing License), Form 24E (Loan License), Rule 158B (Requirements for submission of proof of efficacy for ASU drugs with novel formulations vs. classical formulations).
- **Official Source URL**: https://cdsco.gov.in/opencms/opencms/en/Drugs/Ayush/
- **Verification Status**: VERIFIED

### DOC-IN-FSSAI-001: Food Safety and Standards (Ayurveda Aahara) Regulations, 2022
- **Document ID**: `doc_in_fssai_ayurveda_aahara_2022`
- **Corpus Collection**: `legal_statutory`
- **Jurisdiction**: `INDIA`
- **Document Type**: `REGULATION`
- **Authority**: Food Safety and Standards Authority of India (FSSAI), Ministry of Health and Family Welfare
- **Effective / Amendment Status**: F. No. Std/SP-05/A-Aahara/FSSAI-2021, 5 May 2022
- **Key Provisions**: Definition of "Ayurveda Aahara" (food prepared per recipes/principles of authoritative Ayurvedic books); explicit prohibition on synthetic additives/vitamins; strict distinction from Ayurvedic drugs (cannot make therapeutic/disease cure claims); mandatory "Ayurveda Aahara" logo on packaging.
- **Official Source URL**: https://www.fssai.gov.in/upload/notifications/2022/05/627a69b76c8c4Gazette_Notification_Ayurveda_Aahara_09_05_2022.pdf
- **Verification Status**: VERIFIED

### DOC-IN-DSG-001: The Designs Act, 2000 & Designs Rules, 2001
- **Document ID**: `doc_in_designs_act_2000`
- **Corpus Collection**: `legal_statutory`
- **Jurisdiction**: `INDIA`
- **Document Type**: `STATUTE`
- **Authority**: Legislative Department / DPIIT
- **Key Provisions**: Novel shape, configuration, and ornamentation of Ayurvedic product packaging and dispensers (Locarno Class 9 - Packaging and containers).
- **Official Source URL**: https://www.indiacode.nic.in/handle/123456789/1915
- **Verification Status**: VERIFIED

### DOC-IN-TKDL-001: CSIR-TKDL Public Information & Access Policy Framework
- **Document ID**: `doc_in_tkdl_policy_framework`
- **Corpus Collection**: `legal_statutory`
- **Jurisdiction**: `INDIA`
- **Document Type**: `GUIDELINE`
- **Authority**: Council of Scientific and Industrial Research (CSIR) & Ministry of Ayush
- **Effective / Amendment Status**: Public domain policy document (2022 TKDL expansion)
- **Key Provisions**: Scope of TKDL coverage (classical formulation texts in 5 international languages); terms of access agreements with international patent offices (USPTO, EPO, JPO, etc.); boundary between open public informational records and proprietary database.
- **Official Source URL**: https://www.tkdl.res.in/
- **Verification Status**: VERIFIED

---

## 2. `standards_formulations` Collection (Pharmacopoeias, Monographs & Classical Texts)

### DOC-STD-API-001: The Ayurvedic Pharmacopoeia of India (API) — Part I, Volume I (Single Drugs)
- **Document ID**: `doc_std_api_part1_vol1`
- **Corpus Collection**: `standards_formulations`
- **Jurisdiction**: `INDIA`
- **Document Type**: `MONOGRAPH`
- **Authority**: Pharmacopoeia Commission for Indian Medicine & Homoeopathy (PCIM&H), Ministry of Ayush
- **Key Monographs Included**:
  - *Ashwagandha* (Withania somnifera Dunal. - Root)
  - *Tulsi* (Ocimum sanctum Linn. - Leaf)
  - *Amalaki* (Emblica officinalis Gaertn. - Fruit pericarp)
  - *Haritaki* (Terminalia chebula Retz. - Fruit pericarp)
  - *Bibhitaki* (Terminalia bellirica Roxb. - Fruit pericarp)
  - *Guduchi* (Tinospora cordifolia Miers. - Stem)
  - *Yastimadhu* (Glycyrrhiza glabra Linn. - Root)
- **Fields per Monograph**: Botanical name, Ayurvedic synonyms, classical properties (Rasa, Guna, Virya, Vipaka, Prabhava), therapeutic uses (Karma, Rogaghnata), identity tests, assay, TLC fingerprint standards.
- **Official Source URL**: https://pcimh.gov.in/
- **Verification Status**: VERIFIED

### DOC-STD-API-002: The Ayurvedic Pharmacopoeia of India (API) — Part I, Volumes II to IX (Key Medicinal Herbs)
- **Document ID**: `doc_std_api_part1_vols2_9`
- **Corpus Collection**: `standards_formulations`
- **Jurisdiction**: `INDIA`
- **Document Type**: `MONOGRAPH`
- **Authority**: PCIM&H, Ministry of Ayush
- **Key Monographs Included**: *Brahmi* (Bacopa monnieri), *Shatavari* (Asparagus racemosus), *Arjuna* (Terminalia arjuna), *Neem* (Azadirachta indica), *Haridra/Turmeric* (Curcuma longa), *Guggulu* (Commiphora wightii), *Kalmegh* (Andrographis paniculata).
- **Official Source URL**: https://pcimh.gov.in/
- **Verification Status**: VERIFIED

### DOC-STD-AFI-001: The Ayurvedic Formulary of India (AFI) — Part I (Classical Formulations)
- **Document ID**: `doc_std_afi_part1`
- **Corpus Collection**: `standards_formulations`
- **Jurisdiction**: `INDIA`
- **Document Type**: `MONOGRAPH`
- **Authority**: Department of Ayush / PCIM&H
- **Key Classical Formulation Categories**:
  - *Asava and Arishta* (Fermented preparations: Draksharishta, Ashwagandharishta)
  - *Churna* (Powders: Triphala Churna, Trikatu Churna, Sitopaladi Churna)
  - *Taila* (Medicated oils: Mahanarayana Taila, Kshirabala Taila)
  - *Ghrita* (Medicated clarified butter: Brahmi Ghrita, Triphala Ghrita)
  - *Vati and Gutika* (Tablets/Pills: Chandraprabha Vati, Yograj Guggulu)
  - *Avaleha* (Confections/Jams: Chyawanprash, Vasavaleha)
- **Metadata**: Authoritative treatise citation, ingredient ratios, processing method (Shodhana/Bhavana), indications.
- **Official Source URL**: https://pcimh.gov.in/
- **Verification Status**: VERIFIED

### DOC-STD-AFI-002: The Ayurvedic Formulary of India (AFI) — Part II & III
- **Document ID**: `doc_std_afi_part2_3`
- **Corpus Collection**: `standards_formulations`
- **Jurisdiction**: `INDIA`
- **Document Type**: `MONOGRAPH`
- **Authority**: PCIM&H, Ministry of Ayush
- **Key Content**: Expanded compound formulations, Kwatha Churna, Lepa, Bhasma standards.
- **Official Source URL**: https://pcimh.gov.in/
- **Verification Status**: VERIFIED

### DOC-STD-SCH1-001: First Schedule to the Drugs and Cosmetics Act, 1940 (Authoritative Classical Texts List)
- **Document ID**: `doc_std_first_schedule_books`
- **Corpus Collection**: `standards_formulations`
- **Jurisdiction**: `INDIA`
- **Document Type**: `STATUTE`
- **Authority**: Ministry of Ayush / Legislative Department
- **List of 54 Authoritative Treatise References**:
  - *Charaka Samhita* (Agnivesha / Dridhabala)
  - *Sushruta Samhita* (Sushruta / Nagarjuna)
  - *Ashtanga Hridaya* & *Ashtanga Samgraha* (Vagbhata)
  - *Sharangadhara Samhita* (Sharangadhara)
  - *Bhavaprakasha* (Bhavamishra)
  - *Madhava Nidana* (Madhavakara)
  - *Bhaishajya Ratnavali* (Govinda Dasa)
  - *Rasa Tarangini* & *Rasa Ratna Samucchaya*
  - *Sahasrayogam* & *Chikitsa Manjari*
  - *Ayurveda Sara Samgraha*
- **Role in System**: Gating authority for distinguishing **Classical Ayurvedic Medicine** (Section 3(a) of Drugs Act) from **Proprietary Medicine** or **New Drug**.
- **Official Source URL**: https://cdsco.gov.in/opencms/opencms/en/Drugs/Ayush/
- **Verification Status**: VERIFIED

### DOC-STD-PCIMH-001: PCIM&H General Testing Guidelines & Quality Parameters for ASU Formulations
- **Document ID**: `doc_std_pcimh_quality_standards`
- **Corpus Collection**: `standards_formulations`
- **Jurisdiction**: `INDIA`
- **Document Type**: `GUIDELINE`
- **Authority**: Pharmacopoeia Commission for Indian Medicine & Homoeopathy
- **Key Provisions**: Heavy metal limits (Lead, Cadmium, Mercury, Arsenic), pesticide residue limits, aflatoxin limits, microbial contamination limits for domestic sale and export clearance.
- **Official Source URL**: https://pcimh.gov.in/
- **Verification Status**: VERIFIED

### DOC-STD-CCRAS-001: CCRAS Standard Operating Procedures and Guidelines for Phytochemical Characterization of Ayurvedic Formulations
- **Document ID**: `doc_std_ccras_phytochemical_sop`
- **Corpus Collection**: `standards_formulations`
- **Jurisdiction**: `INDIA`
- **Document Type**: `GUIDELINE`
- **Authority**: Central Council for Research in Ayurvedic Sciences (CCRAS), Ministry of Ayush
- **Key Provisions**: Standardization benchmarks, marker compounds for authentication, chromatographic fingerprinting protocols.
- **Official Source URL**: http://www.ccras.nic.in/
- **Verification Status**: VERIFIED

---

## 3. `procedural_forms` Collection (Procedural Checklists, Applications & Compliance Forms)

### DOC-FORM-NBA-001: NBA Form I — Application for Access to Biological Resources and Associated Traditional Knowledge
- **Document ID**: `doc_form_nba_form1`
- **Corpus Collection**: `procedural_forms`
- **Jurisdiction**: `INDIA`
- **Document Type**: `FORM`
- **Authority**: National Biodiversity Authority (NBA)
- **Governing Law**: Section 3 & 19 of Biological Diversity Act 2002; Rule 14 of BD Rules
- **Structure / Checklist**:
  - Applicant profile (Non-Indian entity/individual / Foreign-controlled corporate)
  - Details of biological resources to be accessed (taxa, parts, quantity, geographical location)
  - Intended purpose (Research / Commercial utilization / Bio-survey)
  - Proposed Benefit Sharing arrangement
- **Official Source URL**: http://nbaindia.org/content/26/60/1/forms.html
- **Verification Status**: VERIFIED

### DOC-FORM-NBA-002: NBA Form II — Application for Transfer of Research Results
- **Document ID**: `doc_form_nba_form2`
- **Corpus Collection**: `procedural_forms`
- **Jurisdiction**: `INDIA`
- **Document Type**: `FORM`
- **Authority**: National Biodiversity Authority (NBA)
- **Governing Law**: Section 4 & 19 of Biological Diversity Act 2002; Rule 16 of BD Rules
- **Structure / Checklist**: Publication/collaboration details, foreign recipient info, benefit sharing commitment.
- **Official Source URL**: http://nbaindia.org/content/26/60/1/forms.html
- **Verification Status**: VERIFIED

### DOC-FORM-NBA-003: NBA Form III — Application for Seeking Prior Approval for Applying for Intellectual Property Rights
- **Document ID**: `doc_form_nba_form3`
- **Corpus Collection**: `procedural_forms`
- **Jurisdiction**: `INDIA`
- **Document Type**: `FORM`
- **Authority**: National Biodiversity Authority (NBA)
- **Governing Law**: Section 6 & 19 of Biological Diversity Act 2002; Rule 18 of BD Rules
- **Structure / Checklist**:
  - Title of the invention / Patent Application Number
  - Country/Patent Office where application is filed or proposed to be filed
  - Biological resource and traditional knowledge components utilized
  - Commercialization plan and expected royalties
  - Mandatory approval timeline prior to grant of patent
- **Official Source URL**: http://nbaindia.org/content/26/60/1/forms.html
- **Verification Status**: VERIFIED

### DOC-FORM-NBA-004: NBA Form IV — Application for Third Party Transfer of Accessed Biological Resources
- **Document ID**: `doc_form_nba_form4`
- **Corpus Collection**: `procedural_forms`
- **Jurisdiction**: `INDIA`
- **Document Type**: `FORM`
- **Authority**: National Biodiversity Authority (NBA)
- **Governing Law**: Section 20 of Biological Diversity Act 2002; Rule 19 of BD Rules
- **Official Source URL**: http://nbaindia.org/content/26/60/1/forms.html
- **Verification Status**: VERIFIED

### DOC-FORM-SBB-001: State Biodiversity Board (SBB) Prior Intimation Checklist for Indian Entities
- **Document ID**: `doc_form_sbb_intimation_checklist`
- **Corpus Collection**: `procedural_forms`
- **Jurisdiction**: `INDIA`
- **Document Type**: `FORM`
- **Authority**: State Biodiversity Boards / NBA
- **Governing Law**: Section 7 & 24 of Biological Diversity Act 2002
- **Structure / Checklist**: Intimation requirements for commercial utilization by Indian citizens/firms; cultivated source certificates; exemptions for registered local vaids/hakims.
- **Official Source URL**: http://nbaindia.org/
- **Verification Status**: VERIFIED

### DOC-FORM-AYUSH-001: Form 24D — Application for Grant/Renewal of License to Manufacture Ayurvedic (including Siddha) or Unani Drugs for Sale
- **Document ID**: `doc_form_ayush_form24d`
- **Corpus Collection**: `procedural_forms`
- **Jurisdiction**: `INDIA`
- **Document Type**: `FORM`
- **Authority**: State Licensing Authorities (SLA) / Ministry of Ayush
- **Governing Law**: Rule 153, Drugs and Cosmetics Rules 1945
- **Structure / Checklist**: GMP compliance (Schedule T), technical staff qualifications, testing laboratory infrastructure, classical text reference or proof of efficacy dossier for proprietary drugs.
- **Official Source URL**: https://cdsco.gov.in/
- **Verification Status**: VERIFIED

### DOC-FORM-AYUSH-002: Form 24E — Application for Grant/Renewal of Loan License to Manufacture ASU Drugs
- **Document ID**: `doc_form_ayush_form24e`
- **Corpus Collection**: `procedural_forms`
- **Jurisdiction**: `INDIA`
- **Document Type**: `FORM`
- **Authority**: State Licensing Authorities (SLA)
- **Governing Law**: Rule 153A, Drugs and Cosmetics Rules 1945
- **Official Source URL**: https://cdsco.gov.in/
- **Verification Status**: VERIFIED

### DOC-FORM-CCPA-001: CCPA Compliance Checklist for AYUSH Advertisements & Misleading Claims
- **Document ID**: `doc_form_ccpa_ayush_ad_guidelines`
- **Corpus Collection**: `procedural_forms`
- **Jurisdiction**: `INDIA`
- **Document Type**: `GUIDELINE`
- **Authority**: Central Consumer Protection Authority (CCPA), Ministry of Consumer Affairs
- **Governing Law**: Consumer Protection Act 2019 / Drugs and Magic Remedies (Objectionable Advertisements) Act 1954
- **Structure / Checklist**: Prohibited claims (Schedule J diseases: cancer, diabetes cure, etc.); substantiation standards for herbal efficacy claims in digital/print advertising.
- **Official Source URL**: https://consumeraffairs.nic.in/
- **Verification Status**: VERIFIED

---

## 4. `international_export` Collection (Treaties, International IP & Export Regimes)

### DOC-INT-TRIPS-001: WTO Agreement on Trade-Related Aspects of Intellectual Property Rights (TRIPS)
- **Document ID**: `doc_int_trips_agreement`
- **Corpus Collection**: `international_export`
- **Jurisdiction**: `INTERNATIONAL`
- **Document Type**: `TREATY`
- **Authority**: World Trade Organization (WTO)
- **Effective / Amendment Status**: In force 1 January 1995; amended 2005/2017
- **Key Articles**:
  - `Article 27.1`: Patentable subject matter (novelty, inventive step, industrial applicability).
  - `Article 27.2`: Ordre public / morality exclusions.
  - `Article 27.3(b)`: Protection of plant varieties (patent vs. sui generis system).
  - `Article 29`: Conditions on patent applicants (clear disclosure).
- **Official Source URL**: https://www.wto.org/english/docs_e/legal_e/27-trips_01_e.htm
- **Verification Status**: VERIFIED

### DOC-INT-CBD-001: Convention on Biological Diversity (CBD, 1992)
- **Document ID**: `doc_int_cbd_1992`
- **Corpus Collection**: `international_export`
- **Jurisdiction**: `INTERNATIONAL`
- **Document Type**: `TREATY`
- **Authority**: Secretariat of the Convention on Biological Diversity (UNEP)
- **Effective / Amendment Status**: In force 29 December 1993
- **Key Articles**:
  - `Article 8(j)`: Traditional knowledge, innovations, and practices of indigenous and local communities.
  - `Article 15`: Access to Genetic Resources (Sovereign rights, Prior Informed Consent - PIC, Mutually Agreed Terms - MAT, Fair and equitable sharing of benefits).
- **Official Source URL**: https://www.cbd.int/convention/text/
- **Verification Status**: VERIFIED

### DOC-INT-NAGOYA-001: The Nagoya Protocol on Access to Genetic Resources and the Fair and Equitable Sharing of Benefits Arising from their Utilization
- **Document ID**: `doc_int_nagoya_protocol_2010`
- **Corpus Collection**: `international_export`
- **Jurisdiction**: `INTERNATIONAL`
- **Document Type**: `TREATY`
- **Authority**: CBD Secretariat, United Nations
- **Effective / Amendment Status**: Adopted 29 October 2010, entered into force 12 October 2014
- **Key Articles**: Articles 5 (Benefit-sharing), 6 (Access obligations), 7 (Access to TK), 13-14 (National focal points & ABS Clearing-House), 15-18 (Compliance with domestic legislation of provider countries).
- **Official Source URL**: https://www.cbd.int/abs/text/
- **Verification Status**: VERIFIED

### DOC-INT-WIPO-001: WIPO Treaty on Intellectual Property, Genetic Resources and Associated Traditional Knowledge (GRATK Treaty, 2024)
- **Document ID**: `doc_int_wipo_gratk_treaty_2024`
- **Corpus Collection**: `international_export`
- **Jurisdiction**: `INTERNATIONAL`
- **Document Type**: `TREATY`
- **Authority**: World Intellectual Property Organization (WIPO)
- **Effective / Amendment Status**: Adopted by Diplomatic Conference on 24 May 2024
- **Key Articles**:
  - `Article 3`: Mandatory Patent Disclosure Requirement — Patent applicants in contracting parties must disclose the country of origin of genetic resources and/or the indigenous people/local community providing associated traditional knowledge.
  - `Article 4`: Exceptions and Limitations.
  - `Article 5`: Non-retroactivity.
  - `Article 6`: Information systems (TK databases, digital libraries).
- **Official Source URL**: https://www.wipo.int/meetings/en/details.jsp?meeting_id=82108
- **Verification Status**: VERIFIED

### DOC-INT-EU-001: EU Directive 2004/24/EC — Traditional Herbal Medicinal Products Directive (THMPD)
- **Document ID**: `doc_int_eu_thmpd_2004`
- **Corpus Collection**: `international_export`
- **Jurisdiction**: `EU`
- **Document Type**: `REGULATION`
- **Authority**: European Parliament and Council of the European Union / European Medicines Agency (EMA)
- **Effective / Amendment Status**: Directive 2004/24/EC amending Directive 2001/83/EC
- **Key Provisions**: Simplified registration procedure for traditional herbal medicinal products; requirement of proof of 30 years of traditional medicinal use (at least 15 years within the EU); quality monograph standards (EMA / HMPC monographs); implications for classical Ayurvedic medicines exported to EU.
- **Official Source URL**: https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32004L0024
- **Verification Status**: VERIFIED

### DOC-INT-EU-002: EU Regulation (EC) No 1924/2006 — Nutrition and Health Claims Made on Foods
- **Document ID**: `doc_int_eu_health_claims_2006`
- **Corpus Collection**: `international_export`
- **Jurisdiction**: `EU`
- **Document Type**: `REGULATION`
- **Authority**: European Commission / European Food Safety Authority (EFSA)
- **Key Provisions**: Botanicals "on-hold" health claims list; substantiation required for marketing Ayurvedic botanicals as food supplements in the European Union.
- **Official Source URL**: https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32006R1924
- **Verification Status**: VERIFIED

### DOC-INT-US-001: US Dietary Supplement Health and Education Act of 1994 (DSHEA) / 21 CFR Part 111
- **Document ID**: `doc_int_us_dshea_1994`
- **Corpus Collection**: `international_export`
- **Jurisdiction**: `USA`
- **Document Type**: `REGULATION`
- **Authority**: US Food and Drug Administration (FDA)
- **Governing Law**: Public Law 103-417 / 21 CFR Part 101 & Part 111
- **Key Provisions**: Classification of Ayurvedic herbs as "dietary supplements"; New Dietary Ingredient (NDI) notification requirements for novel extracts; Structure/Function claims vs. Disease claims; cGMP standards under 21 CFR 111.
- **Official Source URL**: https://www.fda.gov/food/dietary-supplements
- **Verification Status**: VERIFIED

### DOC-INT-CITES-001: CITES Checklist of Medicinal and Aromatic Plant Species Listed in Appendices I, II, and III
- **Document ID**: `doc_int_cites_medicinal_plants`
- **Corpus Collection**: `international_export`
- **Jurisdiction**: `INTERNATIONAL`
- **Document Type**: `GUIDELINE`
- **Authority**: CITES Secretariat (UNEP) / Wildlife Crime Control Bureau (India)
- **Key Provisions**: CITES export permit requirements for Ayurvedic botanical species (e.g. *Nardostachys jatamansi* / Spikenard, *Pterocarpus santalinus* / Red Sanders, *Aquilaria malaccensis* / Agarwood, *Saussurea costus* / Kuth); non-detriment findings (NDF).
- **Official Source URL**: https://cites.org/eng/app/appendices.php
- **Verification Status**: VERIFIED

---

## 5. `case_law_prior_art` Collection (Landmark Prior Art Revocation Dossiers)

> [!NOTE]
> Indian court judgments for case law are explicitly deferred for MVP (empty collection initialized in Qdrant).
> The records below are landmark traditional knowledge prior art revocation dossiers where CSIR / India successfully defended Ayurvedic prior art against foreign biopiracy patents, serving as canonical eval benchmarks.

### DOC-CASE-TK-001: Turmeric Wound Healing Patent Revocation (US Patent 5,401,504)
- **Document ID**: `doc_case_turmeric_revocation`
- **Corpus Collection**: `case_law_prior_art`
- **Jurisdiction**: `USA` / `INDIA`
- **Document Type**: `CASE_LAW`
- **Authority**: United States Patent and Trademark Office (USPTO) / CSIR India
- **Re-examination Date**: 1997
- **Key Findings**: USPTO revoked all claims of US Patent 5,401,504 (assigned to University of Mississippi Medical Center) claiming novel use of turmeric powder for wound healing, on grounds of lack of novelty anticipated by ancient Sanskrit texts and classical Ayurvedic treatises cited in Hindi and Urdu.
- **Official Source URL**: https://www.tkdl.res.in/
- **Verification Status**: VERIFIED

### DOC-CASE-TK-002: Neem Antifungal Patent Revocation (EPO Patent 0436257)
- **Document ID**: `doc_case_neem_revocation`
- **Corpus Collection**: `case_law_prior_art`
- **Jurisdiction**: `EU` / `INDIA`
- **Document Type**: `CASE_LAW`
- **Authority**: European Patent Office (EPO) Technical Board of Appeal
- **Revocation Date**: 8 March 2005 (Case T 0416/01)
- **Key Findings**: Revocation of patent granted to W.R. Grace & Co. for hydrophobic extract of neem seeds as fungicide; Opposition sustained on lack of novelty and inventive step due to established prior public use in Ayurvedic agriculture across India.
- **Official Source URL**: https://www.epo.org/
- **Verification Status**: VERIFIED

### DOC-CASE-TK-003: Basmati Rice Patent Claims Revocation (US Patent 5,663,484)
- **Document ID**: `doc_case_basmati_revocation`
- **Corpus Collection**: `case_law_prior_art`
- **Jurisdiction**: `USA` / `INDIA`
- **Document Type**: `CASE_LAW`
- **Authority**: USPTO / APEDA India
- **Key Findings**: Successful re-examination challenge resulting in RiceTec surrendering key broad patent claims covering traditional Basmati grain characteristics.
- **Official Source URL**: https://www.tkdl.res.in/
- **Verification Status**: VERIFIED
