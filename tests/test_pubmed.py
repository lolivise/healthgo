from __future__ import annotations

from datetime import date

from healthgo import pubmed

XML = b"""<PubmedArticleSet><PubmedArticle>
<MedlineCitation><PMID>111</PMID><Article>
  <Journal><JournalIssue><PubDate><Year>2026</Year></PubDate></JournalIssue><ISOAbbreviation>Sports Med</ISOAbbreviation></Journal>
  <ArticleTitle>Protein <i>in</i> a deficit</ArticleTitle>
  <Abstract><AbstractText Label="RESULTS">Lean mass kept.</AbstractText><AbstractText Label="CONCLUSION">Eat protein.</AbstractText></Abstract>
  <PublicationTypeList><PublicationType>Journal Article</PublicationType><PublicationType>Meta-Analysis</PublicationType></PublicationTypeList>
</Article></MedlineCitation>
<PubmedData><ArticleIdList><ArticleId IdType="pubmed">111</ArticleId><ArticleId IdType="doi">10.1/x</ArticleId></ArticleIdList>
  <ReferenceList><Reference><ArticleIdList><ArticleId IdType="pmc">PMC999</ArticleId></ArticleIdList></Reference></ReferenceList>
</PubmedData></PubmedArticle></PubmedArticleSet>"""


def test_parse_keeps_own_ids_only():
    [p] = pubmed.parse(XML)
    assert p["pmid"] == "111" and p["year"] == "2026" and p["journal"] == "Sports Med"
    assert p["title"] == "Protein in a deficit"
    assert p["pmcid"] is None  # PMC999 belongs to a cited paper
    assert p["doi"] == "10.1/x"
    assert "**Results:** Lean mass kept." in p["abstract"]


def test_render_puts_index_before_abstracts():
    [p] = pubmed.parse(XML)
    p["queries"] = [1]
    md = pubmed.render("fat-loss", date(2026, 10, 1), date(2026, 12, 31),
                       [{"query": "q", "count": 70, "pmids": ["111"]}], [p])
    assert md.index("## Index") < md.index("## Abstracts")
    assert "- 111 · MA · 2026 · Protein in a deficit" in md
    assert "truncated" in md


def test_quarter_label():
    assert pubmed.quarter(date(2027, 1, 10)) == "2027-Q1"
    assert pubmed.quarter(date(2026, 12, 31)) == "2026-Q4"
