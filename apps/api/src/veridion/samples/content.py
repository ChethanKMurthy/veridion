"""Content for Veridion's fictional sample companies.

Everything here is invented for demonstration and testing. The companies,
people, sites and figures do not exist. The documents deliberately contain
realistic reporting problems that the platform must detect:

* Aldermere's annual report states a 2025 energy figure (1,532,000 GJ ≈ 425,556 MWh)
  that conflicts with its sustainability report (412,300 MWh).
* Aldermere mentions renewable electricity backed by REGOs but reports no
  market-based Scope 2 figure, and does not report biogenic CO2.
* Aldermere has screened but not quantified Scope 3.
* Tessaline reports on a financial year ending 31 March and uses the financial
  control approach, so its figures are not directly comparable with Aldermere's.
* Corvane reports in ktCO2e and GWh, does not state its Scope 2 method, and
  includes a scanned (image-only) appendix page that requires OCR.
"""

from __future__ import annotations

from dataclasses import dataclass, field

FICTION_NOTICE = (
    "Fictional sample document. Created by Veridion for demonstration and testing. "
    "The company, people, sites and figures are invented and do not describe any real organization."
)


@dataclass
class SamplePage:
    html: str
    scanned: bool = False  # rendered to an image with no text layer (requires OCR)


@dataclass
class SampleDocument:
    slug: str
    title: str
    doc_type: str
    period_label: str
    header: str
    pages: list[SamplePage]
    published_on: str


@dataclass
class SampleCompany:
    slug: str
    name: str
    industry: str
    country: str
    size_band: str
    fiscal_year_end: str
    description: str
    documents: list[SampleDocument] = field(default_factory=list)


def _cover(company: str, title: str, subtitle: str) -> SamplePage:
    return SamplePage(f"""
<div class="cover">
  <p class="kicker">{company}</p>
  <h1 class="cover-title">{title}</h1>
  <p class="cover-sub">{subtitle}</p>
  <p class="notice">{FICTION_NOTICE}</p>
</div>""")


# ---------------------------------------------------------------------------
# Aldermere Materials Group — focal client (calendar year)
# ---------------------------------------------------------------------------

ALDERMERE_SR = SampleDocument(
    slug="aldermere-sustainability-report-2025",
    title="Aldermere Materials Group — Sustainability Report 2025",
    doc_type="sustainability_report",
    period_label="FY2025",
    header="Aldermere Materials Group · Sustainability Report 2025",
    published_on="2026-03-24",
    pages=[
        _cover("Aldermere Materials Group", "Sustainability Report 2025",
               "Reporting period: 1 January 2025 – 31 December 2025"),
        SamplePage("""
<h1>About this report</h1>
<p>This report covers the sustainability performance of Aldermere Materials Group plc and its subsidiaries
for the year ended 31 December 2025. It has been prepared with reference to the GRI Standards.</p>
<h2>About Aldermere</h2>
<p>Aldermere manufactures clay bricks, precast concrete products and mineral insulation for the UK
construction market. In 2025 we produced 408,000 tonnes of product from seven manufacturing plants and
employed 1,940 people.</p>
<h2>Reporting boundary</h2>
<p>Environmental data covers the seven manufacturing plants and two distribution depots over which we have
operational control. We report greenhouse gas emissions using the operational control approach.</p>
<h2>External assurance</h2>
<p>Our 2025 environmental and safety data has not been externally assured. The Audit and Risk Committee
reviewed the data collection process, and we intend to obtain limited assurance over Scope 1 and 2
emissions for 2026.</p>
<h2>Restatements</h2>
<p>There have been no restatements of previously reported figures.</p>
"""),
        SamplePage("""
<h1>Our approach to climate change</h1>
<p>The Board's Sustainability Committee oversees climate-related risks and opportunities and reviews
progress against our decarbonisation roadmap twice a year. Climate performance is included in the
annual bonus scorecard for executive directors.</p>
<h2>Targets</h2>
<p>We have committed to reduce absolute Scope 1 and 2 emissions by 42% by 2030 against a 2019 base year,
and to reach net zero across our operations by 2050.</p>
<p>In the 2019 base year, Scope 1 and 2 emissions were 81,600 tCO2e. Base-year emissions are recalculated
when acquisitions or divestments change emissions by more than 5%.</p>
<h2>Climate-related risks</h2>
<p>Our most significant transition risk is the rising cost of carbon allowances and natural gas used in
kilns. Physical risks include flooding at two riverside plants. Both risks are recorded on the Group risk
register and reviewed by the Audit and Risk Committee.</p>
"""),
        SamplePage("""
<h1>Greenhouse gas emissions</h1>
<h2>Methodology</h2>
<p>We calculate emissions in accordance with the GHG Protocol Corporate Standard. Emission factors are taken
from the UK Government GHG Conversion Factors for Company Reporting (DESNZ, 2025), and global warming
potentials from the IPCC Sixth Assessment Report (AR6). Our inventory includes carbon dioxide (CO2),
methane (CH4) and nitrous oxide (N2O); emissions of other greenhouse gases are not material.</p>
<h2>Performance</h2>
<p>In 2025, our gross Scope 1 emissions were 48,210 tCO2e, a 3.8% reduction compared with 2024, driven mainly
by kiln heat-recovery projects. Scope 1 emissions arise from natural gas combustion in kilns and dryers,
diesel used by mobile plant, and process emissions from clay.</p>
<p>Scope 2 emissions are reported using the location-based method and were 21,940 tCO2e in 2025
(2024: 23,020 tCO2e).</p>
<h3>Table 4: Greenhouse gas emissions</h3>
<table>
<tr><th>Indicator</th><th>2025</th><th>2024</th><th>2023</th></tr>
<tr><td>Scope 1 emissions (tCO2e)</td><td>48,210</td><td>50,115</td><td>52,900</td></tr>
<tr><td>Scope 2 emissions – location-based (tCO2e)</td><td>21,940</td><td>23,020</td><td>24,310</td></tr>
<tr><td>Total Scope 1 and 2 emissions (tCO2e)</td><td>70,150</td><td>73,135</td><td>77,210</td></tr>
<tr><td>GHG intensity (tCO2e per tonne of product)</td><td>0.172</td><td>0.176</td><td>0.184</td></tr>
</table>
<p>GHG intensity covers Scope 1 and Scope 2 emissions per tonne of product.</p>
<h2>Renewable electricity</h2>
<p>Since April 2024, our two largest plants have purchased renewable electricity backed by Renewable Energy
Guarantees of Origin (REGOs).</p>
"""),
        SamplePage("""
<h1>Value chain emissions</h1>
<p>We have begun screening our Scope 3 emissions across the 15 categories of the GHG Protocol Corporate
Value Chain (Scope 3) Standard. Purchased goods and services (Category 1) and upstream transportation and
distribution (Category 4) are expected to be the most significant categories.</p>
<p>Scope 3 emissions have not yet been quantified. We expect to report them for 2026, starting with
Categories 1 and 4.</p>
<h2>Working with suppliers</h2>
<p>In 2025 we asked our 40 largest suppliers to share product carbon footprints. Eighteen suppliers
responded, and we will use their data to prioritise lower-carbon cement and aggregate purchases.</p>
"""),
        SamplePage("""
<h1>Energy</h1>
<p>Total energy consumption within the organization was 412,300 MWh in 2025 (2024: 431,800 MWh). Fuel use is
converted to energy using net calorific values from the DESNZ conversion factors.</p>
<h3>Table 5: Energy consumption</h3>
<table>
<tr><th>Indicator</th><th>2025</th><th>2024</th></tr>
<tr><td>Natural gas (MWh)</td><td>268,400</td><td>281,900</td></tr>
<tr><td>Diesel (MWh)</td><td>25,000</td><td>26,700</td></tr>
<tr><td>Purchased electricity consumption (MWh)</td><td>118,900</td><td>123,200</td></tr>
<tr><td>Total energy consumption (MWh)</td><td>412,300</td><td>431,800</td></tr>
<tr><td>Share of renewable electricity (%)</td><td>22%</td><td>15%</td></tr>
<tr><td>Energy intensity (MWh per tonne of product)</td><td>1.01</td><td>1.04</td></tr>
</table>
<p>Energy intensity, which covers fuel and electricity consumed within the organization, was 1.01 MWh per
tonne of product in 2025 (2024: 1.04).</p>
"""),
        SamplePage("""
<h1>Reducing energy use and emissions</h1>
<p>Kiln heat-recovery projects at our Ashby and Kelso plants and the replacement of fourteen diesel loaders
with electric models reduced Scope 1 emissions by 2,350 tCO2e in 2025 compared with 2024.</p>
<p>Efficiency projects delivered energy savings of 6,800 MWh in 2025 against the 2024 baseline, mainly
through reduced natural gas use in kilns and dryers.</p>
<h2>Water and waste</h2>
<p>Water withdrawal was 412 megalitres in 2025 (2024: 428 megalitres), drawn from municipal supplies and
on-site boreholes.</p>
<p>We generated 18,400 tonnes of waste in 2025, most of which was recycled as fired clay and concrete fines.</p>
<h2>Health and safety</h2>
<p>Our lost-time injury frequency rate (LTIFR) was 0.82 per million hours worked in 2025 (2024: 0.95).</p>
"""),
    ],
)

ALDERMERE_AR = SampleDocument(
    slug="aldermere-annual-report-2025",
    title="Aldermere Materials Group — Annual Report and Accounts 2025",
    doc_type="annual_report",
    period_label="FY2025",
    header="Aldermere Materials Group · Annual Report and Accounts 2025",
    published_on="2026-03-10",
    pages=[
        _cover("Aldermere Materials Group", "Annual Report and Accounts 2025",
               "For the year ended 31 December 2025"),
        SamplePage("""
<h1>Chair's statement</h1>
<p>2025 was a year of steady progress for Aldermere. Despite subdued housing starts, revenue grew by 3.6% as
demand for precast concrete products remained resilient. We continued to invest in our plants, and we
remain committed to reaching net zero across our operations by 2050.</p>
<p>The Board welcomed two new independent non-executive directors during the year, strengthening our
expertise in energy markets and digital operations.</p>
"""),
        SamplePage("""
<h1>Financial review</h1>
<p>Revenue for the year ended 31 December 2025 was £412.6 million (2024: £398.1 million). Operating profit
increased to £38.9 million (2024: £35.2 million), reflecting improved plant utilisation and lower
energy costs in the second half.</p>
<h3>Financial highlights (£ million)</h3>
<table>
<tr><th>Measure</th><th>2025</th><th>2024</th></tr>
<tr><td>Revenue</td><td>412.6</td><td>398.1</td></tr>
<tr><td>Operating profit</td><td>38.9</td><td>35.2</td></tr>
<tr><td>Capital expenditure</td><td>27.4</td><td>22.8</td></tr>
</table>
"""),
        SamplePage("""
<h1>Principal risks</h1>
<p><b>Energy and carbon costs.</b> Natural gas and carbon allowance prices remain volatile. We hedge part of
our gas requirement up to 18 months ahead and continue to invest in kiln efficiency.</p>
<p><b>Climate-related physical risk.</b> Two plants are located near rivers with increasing flood risk.
Flood defences at one site were upgraded in 2025.</p>
<p><b>Regulatory change.</b> Sustainability reporting requirements continue to evolve, and customers
increasingly request product-level carbon data.</p>
"""),
        SamplePage("""
<h1>Environmental performance</h1>
<p>The company monitors operational energy consumption across its manufacturing facilities.</p>
<p>In 2025 the Group's total energy consumption was 1,532,000 GJ (2024: 1,554,500 GJ).</p>
<p>Scope 1 emissions were 48,210 tCO2e and location-based Scope 2 emissions were 21,940 tCO2e in 2025.
Streamlined Energy and Carbon Reporting disclosures are included in the Sustainability Report.</p>
"""),
        SamplePage("""
<h1>Corporate governance</h1>
<p>The Board comprises a non-executive Chair, two executive directors and five independent non-executive
directors. The Sustainability Committee, chaired by an independent non-executive director, oversees
climate strategy, health and safety, and environmental performance.</p>
<p>The Audit and Risk Committee reviews the integrity of financial and non-financial reporting, including
the processes used to collect environmental data.</p>
"""),
    ],
)

ALDERMERE = SampleCompany(
    slug="aldermere",
    name="Aldermere Materials Group",
    industry="Building materials",
    country="United Kingdom",
    size_band="1,000–5,000 employees",
    fiscal_year_end="12-31",
    description="Fictional manufacturer of clay bricks, precast concrete products and mineral insulation.",
    documents=[ALDERMERE_SR, ALDERMERE_AR],
)

# ---------------------------------------------------------------------------
# Tessaline Building Products — peer (financial year ending 31 March)
# ---------------------------------------------------------------------------

TESSALINE_REPORT = SampleDocument(
    slug="tessaline-annual-sustainability-report-2024-25",
    title="Tessaline Building Products — Annual and Sustainability Report 2024/25",
    doc_type="sustainability_report",
    period_label="FY2025",
    header="Tessaline Building Products · Annual and Sustainability Report 2024/25",
    published_on="2025-07-02",
    pages=[
        _cover("Tessaline Building Products", "Annual and Sustainability Report 2024/25",
               "For the year ended 31 March 2025"),
        SamplePage("""
<h1>About this report</h1>
<p>Tessaline manufactures roof tiles, facing bricks and landscaping products from six plants. This report
covers the financial year 1 April 2024 to 31 March 2025 (FY2024/25). Production was 361,000 tonnes.</p>
<p>We report greenhouse gas emissions using the financial control approach, in line with the GHG Protocol
Corporate Standard. Emission factors are taken from DESNZ (2024) and global warming potentials from the
IPCC Fifth Assessment Report (AR5). The inventory covers CO2, CH4, N2O and HFCs.</p>
<p>Our base year is FY2019/20. Base-year emissions are recalculated for structural changes above 5%.</p>
<p>Scope 1 and Scope 2 emissions for FY2024/25 received limited assurance from an independent assurance
provider under ISAE 3410.</p>
"""),
        SamplePage("""
<h1>Climate performance</h1>
<h3>Greenhouse gas emissions (tCO2e)</h3>
<table>
<tr><th>Indicator</th><th>FY2024/25</th><th>FY2023/24</th></tr>
<tr><td>Scope 1 emissions (tCO2e)</td><td>41,870</td><td>43,050</td></tr>
<tr><td>Scope 2 emissions – location-based (tCO2e)</td><td>17,620</td><td>18,410</td></tr>
<tr><td>Scope 2 emissions – market-based (tCO2e)</td><td>9,410</td><td>12,880</td></tr>
<tr><td>Scope 3 emissions (tCO2e)</td><td>186,300</td><td>191,700</td></tr>
<tr><td>GHG intensity – Scope 1 and 2, location-based (tCO2e per tonne of product)</td><td>0.165</td><td>0.171</td></tr>
</table>
<p>Scope 3 covers Category 1 (purchased goods and services), Category 4 (upstream transportation and
distribution) and Category 12 (end-of-life treatment of sold products), calculated using a combination of
spend-based and activity-based methods.</p>
<p>Biogenic CO2 emissions from the use of biomass fuels were 1,240 tCO2e in FY2024/25 and are reported
outside the scopes.</p>
"""),
        SamplePage("""
<h1>Energy and resources</h1>
<p>Total energy consumption in FY2024/25 was 1,298,000 GJ (FY2023/24: 1,342,600 GJ). Purchased electricity
consumption was 61,200 MWh, of which 58% was supplied under a renewable power purchase agreement.</p>
<p>Water withdrawal was 365 megalitres and we generated 15,100 tonnes of waste.</p>
<p>Fuel switching from coal to natural gas and biomass at our Brandon tile plant contributed to lower
Scope 1 emissions during the year.</p>
<h2>Targets</h2>
<p>We aim to reduce Scope 1 and 2 emissions by 50% by 2032 from the FY2019/20 baseline.</p>
<h2>Health and safety</h2>
<p>The lost-time injury frequency rate (LTIFR) was 1.12 per million hours worked in FY2024/25.</p>
"""),
    ],
)

TESSALINE = SampleCompany(
    slug="tessaline",
    name="Tessaline Building Products",
    industry="Building materials",
    country="United Kingdom",
    size_band="1,000–5,000 employees",
    fiscal_year_end="03-31",
    description="Fictional manufacturer of roof tiles, facing bricks and landscaping products.",
    documents=[TESSALINE_REPORT],
)

# ---------------------------------------------------------------------------
# Corvane Industries — peer (calendar year, scanned appendix)
# ---------------------------------------------------------------------------

CORVANE_UPDATE = SampleDocument(
    slug="corvane-sustainability-update-2025",
    title="Corvane Industries — Sustainability Update 2025",
    doc_type="sustainability_report",
    period_label="FY2025",
    header="Corvane Industries · Sustainability Update 2025",
    published_on="2026-04-15",
    pages=[
        _cover("Corvane Industries", "Sustainability Update 2025", "Calendar year 2025"),
        SamplePage("""
<h1>Performance summary</h1>
<p>Corvane Industries produces engineered stone and concrete blocks from five plants in the UK and Ireland.</p>
<p>Scope 1 emissions were 63.4 ktCO2e in 2025 (2024: 66.0 ktCO2e). Scope 2 emissions were 26.1 ktCO2e in 2025.</p>
<p>Total energy use was 498 GWh in 2025. Water withdrawal was 538,000 m3.</p>
<p>The lost-time injury frequency rate (LTIFR) was 0.64 in 2025.</p>
<p>A detailed environmental data table is provided in the appendix.</p>
"""),
        SamplePage("""
<h1>Appendix: Environmental data</h1>
<table>
<tr><th>Indicator</th><th>2025</th><th>2024</th></tr>
<tr><td>Scope 1 emissions (ktCO2e)</td><td>63.4</td><td>66.0</td></tr>
<tr><td>Scope 2 emissions (ktCO2e)</td><td>26.1</td><td>27.9</td></tr>
<tr><td>Total energy use (GWh)</td><td>498</td><td>517</td></tr>
<tr><td>Water withdrawal (m3)</td><td>538,000</td><td>551,000</td></tr>
</table>
<p>Data in this appendix was scanned from the printed board pack.</p>
""", scanned=True),
    ],
)

CORVANE = SampleCompany(
    slug="corvane",
    name="Corvane Industries",
    industry="Building materials",
    country="United Kingdom",
    size_band="1,000–5,000 employees",
    fiscal_year_end="12-31",
    description="Fictional producer of engineered stone and concrete blocks.",
    documents=[CORVANE_UPDATE],
)

# A corrected version of Aldermere's annual report, used to demonstrate how a
# replaced source document triggers reassessment of the findings that cite it.
ALDERMERE_AR_V2 = SampleDocument(
    slug="aldermere-annual-report-2025-v2",
    title=ALDERMERE_AR.title,
    doc_type="annual_report",
    period_label="FY2025",
    header=ALDERMERE_AR.header,
    published_on="2026-04-02",
    pages=[
        *ALDERMERE_AR.pages[:4],
        SamplePage(ALDERMERE_AR.pages[4].html.replace("1,532,000 GJ", "1,484,280 GJ")),
        *ALDERMERE_AR.pages[5:],
    ],
)

COMPANIES = [ALDERMERE, TESSALINE, CORVANE]
