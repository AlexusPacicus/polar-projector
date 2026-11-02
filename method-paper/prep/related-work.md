# Related work: candidate references

Phase 0 preparation for the method paper (`method-paper/BRIEF.md:48-49`). Eight candidates on reproducible research,
verifiable artifacts and executable papers, each with a link and one line on how it relates to the case. Written on
2026-11-02 by an AI agent (Claude) in a cloud session, outside the governed channel (`method-paper/BRIEF.md:30-32`).
The author has not reviewed it.

## How these were checked, and what was not

- **No link was opened from this session.** The environment's network policy refused `doi.org`,
  `api.crossref.org` and `www.acm.org` (the proxy answered `CONNECT` with HTTP 403 when tried with `curl` in this
  session), and the fetch tool could not resolve `api.crossref.org`. Whether each link works is therefore unverified.
- **Metadata was corroborated by web search instead,** on 2026-11-02. Each entry says which fields matched across
  search results and links the result pages it relied on.
- **Status labels:**
  - *Metadata confirmed, link not opened*: authors, title, venue, year and DOI all appear, consistently, in search
    results.
  - *Partly confirmed, link not opened*: at least one field could not be confirmed; the entry names it.
- **To finish the check,** open each link, or allow `doi.org` and `api.crossref.org` in the environment's network
  settings and have the check re-run.
- **Where the numbers come from.** Years, volumes, issues, pages and DOIs come from the search results named in each
  entry, not from this repository. Repository facts in the "Relates" lines cite `path:line` at commit `501c67f`, or
  a commit.

## Candidates

### 1. Buckheit & Donoho (1995): reproducible research

Buckheit, J. B., & Donoho, D. L. (1995). WaveLab and Reproducible Research. In A. Antoniadis & G. Oppenheim (Eds.),
*Wavelets and Statistics* (pp. 53–81 or 55–81; sources differ). Springer.
<https://doi.org/10.1007/978-1-4612-2544-7_5>

**Relates:** the classic argument that a computational article only advertises the code and data behind its
figures; the case answers it differently, by treating the manuscript as an output that CI checks against committed
artifacts (`docs/ARCHITECTURE.md:9-10`, `README.md:114-118`).

**Status: partly confirmed, link not opened.** Authors, title, editors, publisher, year and DOI appear in search
results; a bibliography gives the DOI, and a copy is hosted by Stanford
(<https://web.stanford.edu/dept/statistics/cgi-bin/donoho/wp-content/uploads/2018/08/wavelab.pdf>). Not confirmed:
the page range. Secondary sources attribute the "advertising" sentence to this paper, paraphrasing Claerbout, in
wording that varies between them (for example Barba, <https://arxiv.org/pdf/1802.03311>), so check the original
before quoting it.

### 2. Peng (2011): reproducibility as a minimum standard

Peng, R. D. (2011). Reproducible Research in Computational Science. *Science*, 334(6060), 1226–1227.
<https://doi.org/10.1126/science.1213847>

**Relates:** proposes reproducibility as the minimum standard when replication is not possible, on a spectrum that
runs from publication only to linked, executable code and data; the case sits at the linked end, adds a CI check
(`README.md:114-122`), and claims no replication (one corpus, one encoder, one host:
`paper/polar-projector-paper.md:887-891`).

**Status: metadata confirmed, link not opened.** Author, title, journal, volume, issue, first page, DOI and the
issue date (2 December 2011) appear in search results: a PDF copy's header
(<https://cs.nyu.edu/~shasha/papers/Science-2011-Peng-1226-7.pdf>), and the EASE
(<https://ease.org.uk/2011/12/b-reproducible-research-in-computational-science/>) and ModelDB
(<https://modeldb.science/citations/224258>) records. The last page, 1227, comes from one bibliography.

### 3. Sandve, Nekrutenko, Taylor & Hovig (2013): ten rules

Sandve, G. K., Nekrutenko, A., Taylor, J., & Hovig, E. (2013). Ten Simple Rules for Reproducible Computational
Research. *PLoS Computational Biology*, 9(10), e1003285. <https://doi.org/10.1371/journal.pcbi.1003285>

**Relates:** its Rule 9, "Connect Textual Statements to Underlying Results", is the rule the registry mechanizes:
every claim needs a row before it enters the manuscript (`paper/claims.md:3-5`), and the presence check fails the
build when a checked figure is not printed (`tools/verify_paper_tables.py:599-627`).

**Status: metadata confirmed, link not opened.** All citation fields and Rule 9's title appear in search results:
PubMed Central (<https://pmc.ncbi.nlm.nih.gov/articles/PMC3812051/>) and an ESIP mailing-list post listing the
rules (<https://lists.esipfed.org/pipermail/esip-preserve/2013/001060.html>). Rule 9's body text was not read.

### 4. Nosek, Ebersole, DeHaven & Mellor (2018): preregistration

Nosek, B. A., Ebersole, C. R., DeHaven, A. C., & Mellor, D. T. (2018). The preregistration revolution. *PNAS*,
115(11), 2600–2606. <https://doi.org/10.1073/pnas.1708274114>

**Relates:** separates prediction from postdiction by fixing the analysis plan before outcomes are seen; the
registry applies that split claim by claim (`paper/claims.md:52-56`), but registers by commit order in the project's
own repository rather than with a third party, with 49 to 384 seconds between protocol and results commits
(`21e8e45` → `c265abb`; `1c363bb` → `1e9d217`; `case-data.md` §8).

**Status: metadata confirmed, link not opened.** All citation fields and the publication date (13 March 2018)
appear in search results: PubMed Central (<https://pmc.ncbi.nlm.nih.gov/articles/PMC6233068>), Scinapse
(<https://www.scinapse.io/papers/2779812635>) and PubPeer
(<https://pubpeer.com/publications/E96C39735908C94D88D0481220182A>). The prediction/postdiction distinction appears
in the abstract as quoted in those results.

### 5. Jimenez et al. (2017): the Popper convention

Jimenez, I., Sevilla, M., Watkins, N., Maltzahn, C., et al. (2017). The Popper Convention: Making Reproducible
Systems Evaluation Practical. *2017 IEEE International Parallel and Distributed Processing Symposium Workshops
(IPDPSW)*, 1561–1570. <https://doi.org/10.1109/IPDPSW.2017.157> (DOI not confirmed)

**Relates:** the closest prior design: each experiment is managed as a software project and re-run through continuous
integration; the case's CI re-runs no benchmark and instead checks the manuscript against committed artifacts
(`tools/verify_paper_tables.py:676-677`, `.github/workflows/ci.yml:40`).

**Status: partly confirmed, link not opened.** Confirmed: the title, the venue (IPDPS Workshops 2017; one UCSC slide
deck names the workshop REPPAR 2017), pages 1561–1570 from a DBLP-derived record
(<https://puma.ub.uni-stuttgart.de/bibtex/11ae6b50313e9daa4a97990f10cb9e46b>), and the reliance on continuous
integration from the UCSC technical report
(<https://tr.soe.ucsc.edu/research/technical-reports/UCSC-SOE-16-10>). Not confirmed: the DOI, and the full author
list, which differs between sources. The four names given are those the technical report lists, and the report's
title differs slightly ("Popper: Making Reproducible Systems Performance Evaluation Practical").

### 6. Nuijten et al. (2016): automated consistency checks of printed numbers

Nuijten, M. B., Hartgerink, C. H. J., van Assen, M. A. L. M., Epskamp, S., & Wicherts, J. M. (2016). The prevalence
of statistical reporting errors in psychology (1985–2013). *Behavior Research Methods*, 48(4), 1205–1226.
<https://doi.org/10.3758/s13428-015-0664-2>

**Relates:** statcheck recomputes p-values from the reported test statistics and found an inconsistent p-value in
half of the papers it checked that used null-hypothesis tests; like the case's verifier, it checks consistency, not
whether the analysis measured the right thing (`README.md:124-125`).

**Status: metadata confirmed, link not opened.** All citation fields and the abstract's findings appear in search
results: PubMed Central (<https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5101263/>), and the Tilburg
(<https://repository.tilburguniversity.edu/items/91a6866e-3643-4db9-b7c2-8054f0497e3c>) and Utrecht
(<https://research-portal.uu.nl/en/publications/the-prevalence-of-statistical-reporting-errors-in-psychology-1985/>)
repositories.

### 7. ACM Artifact Review and Badging, Version 1.1 (2020): verifiable artifacts

Association for Computing Machinery. (2020). *Artifact Review and Badging*, Version 1.1, 20 August 2020.
<https://www.acm.org/publications/policies/artifact-review-and-badging-current> (URL not confirmed)

**Relates:** badges that reviewers award after checking that artifacts are available and work and that results
reproduce; the case has no such outside evaluation, and its check is self-administered, runs in CI on pushes to
`main` and on pull requests (`.github/workflows/ci.yml:3-6`), and covers consistency between paper and artifacts
only (`README.md:124-125`).

**Status: partly confirmed, link not opened.** Confirmed: Version 1.1 is the current policy, dated 20 August 2020
(SIGIR's badging page, <https://sigir.org/general-information/acm-sigir-artifact-badging/>; the CCS 2025 call for
artifacts, <https://sigsac.org/ccs/CCS2025/call-for-artifacts/>), and the Version 1.0 page exists, is marked
"not current" and points to 1.1 (<https://www.acm.org/publications/policies/artifact-review-badging>). Not
confirmed: the Version 1.1 URL above and its exact badge names.

### 8. Nowakowski et al. (2011): the Collage executable paper

Nowakowski, P., Ciepiela, E., Harężlak, D., Kocot, J., Kasztelnik, M., Bartyński, T., Meizner, J., Dyk, G., &
Malawski, M. (2011). The Collage Authoring Environment. *Procedia Computer Science*, 4, 608–617.
<https://doi.org/10.1016/j.procs.2011.04.064>

**Relates:** the winning entry of Elsevier's Executable Paper Grand Challenge, in which readers re-run code embedded
in the article; the case keeps execution in the repository and CI and the manuscript static, so drift is caught
after it happens rather than prevented by generating the numbers.

**Status: metadata confirmed, link not opened.** Authors and DOI appear in the DICE team's publication record
(<https://dice.cyfronet.pl/publications/2011-01-01_the_collage_authorin/>). Volume 4, the year and the pages come
from the paper's own header as quoted in search results; the DICE record shows a different volume number. The
prize appears on two independent pages
(<https://reproducibleresearch.net/2011/07/16/elsevier-executable-paper-grand-challenge/>;
<https://occamstypewriter.org/trading-knowledge/2011/06/13/elsevier-and-the-executable-paper/>).

## Considered, not included

- **Akhlaghi et al. (2021),** "Toward Long-Term and Archivable Reproducibility", *Computing in Science &
  Engineering* 23(3), 82–91, <https://doi.org/10.1109/MCSE.2021.3072860> (title, venue and DOI found in search
  results, for example <https://arxiv.org/abs/2006.03018v3>). Its Maneage template might be the closest mechanism to
  this case, if it writes the paper's numbers from the pipeline, but search could not confirm that. Worth reading
  before Phase 1.

## Where each could go in the outline

| Reference | Outline section (`outline.md`) |
|---|---|
| Buckheit & Donoho (1995); Peng (2011) | §1 Introduction: the problem and the standard |
| Sandve et al. (2013) | §3.1 Claims registry |
| Nosek et al. (2018) | §3.2 Pre-registration labels; §6 Limits (self-registration) |
| Jimenez et al. (2017); Nuijten et al. (2016) | §3.4 Verifier; §6 Limits (consistency, not validity) |
| ACM (2020) | §6 Limits (no outside evaluation) |
| Nowakowski et al. (2011) | §1 or §6: detecting drift versus preventing it by generating numbers |
