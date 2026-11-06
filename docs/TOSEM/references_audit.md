# TOSEM bibliography verification

Audit date: 2026-11-05. Scope: all **69 records** in `references.bib`, including the two currently uncited records. All original citation keys are preserved.

## Findings and policy

- All 69 cited works/records have verifiable existence in arXiv, publisher-registered Crossref metadata, or the original journal archive. No invented work was identified. This is a bibliographic identity/metadata audit, not a review of whether each citation supports every scientific claim in the paper.
- 25 records now cite the verified arXiv version. Ten were converted from journal/conference records; fifteen already cited arXiv.
- 44 records remain published references because the live arXiv title search did not yield the same work with matching authors. A negative search is not proof that no arXiv version exists. Related papers returned by search were rejected rather than substituted.
- Every arXiv replacement matches the title and complete ordered author list. Agentless has an additional title prefix on arXiv; its authors and underlying title match the published work. Published venue, pagination, volume/issue, and publisher DOI were removed from preprint entries. The `eprint`, `archivePrefix`, `primaryClass`, and URL come from the live arXiv record. Years use first arXiv submission, and the JSON records the latest version inspected.
- Remaining publication identities were checked by DOI against Crossref's live publisher-deposited records, including subtitles when titles were split across fields. Holm's article was checked against the original JSTOR issue table of contents. Publisher/journal pages resolve ambiguous or defective metadata as described below.
- Citation-key years are stable identifiers, not evidence of publication dates. For example, the Efron key contains 1993 but its selected DOI/edition is dated 1994; the Leveson key contains 2011 but the verified publication is 2012. Both remain explicitly documented rather than changing keys and breaking citations.

## Material corrections

- **Wohlin:** the entry's key named the 2012 book but its DOI and year selected the 2000 edition. It now consistently cites the [verified 2012 edition](https://link.springer.com/book/10.1007/978-3-642-29044-2).
- **Vargha–Delaney:** corrected the first-page-only range to 101–132 and selected the [publisher DOI](https://journals.sagepub.com/doi/10.3102/10769986025002101). The older JSTOR Crossref deposit duplicates Vargha as a third author; the two-author publisher record takes precedence.
- **Wilcoxon:** corrected 80 to 80–83, confirmed by the [original issue contents](https://www.jstor.org/stable/i350470).
- **MCMAS:** use 2017 for volume 19, issue 1, pages 9–30; 2015 is its online-first date. Both dates are present in the [publisher record](https://link.springer.com/article/10.1007/s10009-015-0378-x).
- **Cobleigh and Z3:** replaced the series-only `booktitle` with the actual TACAS proceedings title, retaining LNCS separately and adding verified volumes [2619](https://link.springer.com/chapter/10.1007/3-540-36577-X_24) and [4963](https://link.springer.com/chapter/10.1007/978-3-540-78800-3_24).
- Added publisher names and publisher locations only when present in verified publisher metadata. Corrected IEEE series-volume hyphens. Retained correct Păsăreanu spelling rather than copying the publisher's corrupted uppercase diacritics.

Three nonfatal ACM BibTeX warnings remain for unspecified publisher addresses in Benveniste, Efron, and Leveson. Addresses have not been guessed merely to silence these warnings.

## Evidence and reproducibility

`references_audit.json` contains one decision per entry, the original and final fields, field-level changes, live source URLs, arXiv search results (including rejected candidates), and publisher metadata. `references_audit.csv` is the compact review index. Existing TSE verification files were used only to locate candidate identifiers, and were rechecked live; they were not accepted as the verification evidence. The TSE bibliography was not modified.

The per-entry table below links directly to the selected record. The JSON also preserves the source for every original DOI, including entries converted to arXiv. All 69 arXiv lookups completed without a network error. No entry was verified solely from an unrelated title match.

| Citation key | Selected version | Source | Changed fields |
|---|---|---|---|
| `hong2024metagpt` | arXiv | [arXiv:2308.00352](https://arxiv.org/abs/2308.00352) | archivePrefix, eprint, howpublished, primaryClass, title |
| `qian2024chatdev` | arXiv | [arXiv:2307.07924](https://arxiv.org/abs/2307.07924) | archivePrefix, booktitle, doi, eprint, pages, primaryClass, title, url, year, entry_type |
| `huang2023agentcoder` | arXiv | [arXiv:2312.13010](https://arxiv.org/abs/2312.13010) | archivePrefix, eprint, howpublished, primaryClass, title |
| `islam2024mapcoder` | arXiv | [arXiv:2405.11403](https://arxiv.org/abs/2405.11403) | archivePrefix, booktitle, doi, eprint, pages, primaryClass, title, url, entry_type |
| `dong2024selfcollab` | arXiv | [arXiv:2304.07590](https://arxiv.org/abs/2304.07590) | archivePrefix, doi, eprint, journal, number, pages, primaryClass, title, url, volume, year, entry_type |
| `du2024debate` | arXiv | [arXiv:2305.14325](https://arxiv.org/abs/2305.14325) | archivePrefix, eprint, howpublished, primaryClass, title |
| `wang2024moa` | arXiv | [arXiv:2406.04692](https://arxiv.org/abs/2406.04692) | archivePrefix, eprint, howpublished, primaryClass, title |
| `wu2024autogen` | arXiv | [arXiv:2308.08155](https://arxiv.org/abs/2308.08155) | archivePrefix, eprint, howpublished, primaryClass, title |
| `li2023camel` | arXiv | [arXiv:2303.17760](https://arxiv.org/abs/2303.17760) | archivePrefix, eprint, howpublished, primaryClass, title |
| `he2025llmmas` | arXiv | [arXiv:2404.04834](https://arxiv.org/abs/2404.04834) | archivePrefix, doi, eprint, journal, number, pages, primaryClass, title, url, volume, year, entry_type |
| `hou2024llm4se` | arXiv | [arXiv:2308.10620](https://arxiv.org/abs/2308.10620) | archivePrefix, doi, eprint, journal, number, pages, primaryClass, title, url, volume, year, entry_type |
| `fan2023llmse` | arXiv | [arXiv:2310.03533](https://arxiv.org/abs/2310.03533) | archivePrefix, booktitle, doi, eprint, pages, primaryClass, title, url, entry_type |
| `cemri2025why` | arXiv | [arXiv:2503.13657](https://arxiv.org/abs/2503.13657) | archivePrefix, eprint, howpublished, primaryClass, title |
| `zhang2025which` | arXiv | [arXiv:2505.00212](https://arxiv.org/abs/2505.00212) | archivePrefix, eprint, howpublished, primaryClass, title |
| `jimenez2024swebench` | arXiv | [arXiv:2310.06770](https://arxiv.org/abs/2310.06770) | archivePrefix, eprint, howpublished, primaryClass, title |
| `xia2025agentless` | arXiv | [arXiv:2407.01489](https://arxiv.org/abs/2407.01489) | archivePrefix, doi, eprint, journal, number, pages, primaryClass, title, url, volume, year, entry_type |
| `tao2024magis` | arXiv | [arXiv:2403.17927](https://arxiv.org/abs/2403.17927) | archivePrefix, booktitle, doi, eprint, pages, primaryClass, title, url, entry_type |
| `liu2024agentbench` | arXiv | [arXiv:2308.03688](https://arxiv.org/abs/2308.03688) | archivePrefix, eprint, howpublished, primaryClass, title |
| `yehudai2025survey` | arXiv | [arXiv:2503.16416](https://arxiv.org/abs/2503.16416) | archivePrefix, eprint, howpublished, primaryClass, title |
| `wang2026agentspec` | arXiv | [arXiv:2503.18666](https://arxiv.org/abs/2503.18666) | archivePrefix, eprint, howpublished, primaryClass, title |
| `debenedetti2024agentdojo` | arXiv | [arXiv:2406.13352](https://arxiv.org/abs/2406.13352) | archivePrefix, eprint, howpublished, primaryClass, title |
| `greshake2023not` | arXiv | [arXiv:2302.12173](https://arxiv.org/abs/2302.12173) | archivePrefix, booktitle, doi, eprint, pages, primaryClass, title, url, entry_type |
| `ruan2024toolemu` | arXiv | [arXiv:2309.15817](https://arxiv.org/abs/2309.15817) | archivePrefix, eprint, howpublished, primaryClass, title |
| `inan2023llamaguard` | arXiv | [arXiv:2312.06674](https://arxiv.org/abs/2312.06674) | archivePrefix, eprint, howpublished, primaryClass, title |
| `rebedea2023nemo` | arXiv | [arXiv:2310.10501](https://arxiv.org/abs/2310.10501) | archivePrefix, author, booktitle, doi, eprint, pages, primaryClass, title, url, entry_type |
| `meyer1992applying` | Published; no matching arXiv located | [DOI](https://doi.org/10.1109/2.161279) | None |
| `benveniste2018contracts` | Published; no matching arXiv located | [DOI](https://doi.org/10.1561/9781680834031) | None |
| `misra1981proofs` | Published; no matching arXiv located | [DOI](https://doi.org/10.1109/tse.1981.230844) | volume |
| `jones1983tentative` | Published; no matching arXiv located | [DOI](https://doi.org/10.1145/69575.69577) | None |
| `abadi1993composing` | Published; no matching arXiv located | [DOI](https://doi.org/10.1145/151646.151649) | None |
| `dealfaro2001interface` | Published; no matching arXiv located | [DOI](https://doi.org/10.1145/503271.503226) | None |
| `cobleigh2003learning` | Published; no matching arXiv located | [DOI](https://doi.org/10.1007/3-540-36577-x_24) | address, booktitle, publisher, series, volume |
| `weiser1984program` | Published; no matching arXiv located | [DOI](https://doi.org/10.1109/tse.1984.5010248) | volume |
| `horwitz1990interprocedural` | Published; no matching arXiv located | [DOI](https://doi.org/10.1145/960116.53994) | None |
| `wong2016survey` | Published; no matching arXiv located | [DOI](https://doi.org/10.1109/TSE.2016.2521368) | None |
| `zeller2002simplifying` | Published; no matching arXiv located | [DOI](https://doi.org/10.1109/32.988498) | None |
| `jones2005empirical` | Published; no matching arXiv located | [DOI](https://doi.org/10.1145/1101908.1101949) | address, publisher |
| `kildall1973unified` | Published; no matching arXiv located | [DOI](https://doi.org/10.1145/512927.512945) | address, publisher |
| `kam1977monotone` | Published; no matching arXiv located | [DOI](https://doi.org/10.1007/bf00290339) | None |
| `johnson1994program` | Published; no matching arXiv located | [DOI](https://doi.org/10.1145/178243.178258) | address, publisher |
| `vanderaalst1998application` | Published; no matching arXiv located | [DOI](https://doi.org/10.1142/s0218126698000043) | None |
| `lengauer1979fast` | Published; no matching arXiv located | [DOI](https://doi.org/10.1145/357062.357071) | None |
| `knight1986experimental` | Published; no matching arXiv located | [DOI](https://doi.org/10.1109/tse.1986.6312924) | volume |
| `avizienis1985nversion` | Published; no matching arXiv located | [DOI](https://doi.org/10.1109/tse.1985.231893) | volume |
| `littlewood1989conceptual` | Published; no matching arXiv located | [DOI](https://doi.org/10.1109/32.58771) | None |
| `calder2003feature` | Published; no matching arXiv located | [DOI](https://doi.org/10.1016/s1389-1286(02)00352-3) | None |
| `arcuri2011practical` | Published; no matching arXiv located | [DOI](https://doi.org/10.1145/1985793.1985795) | address, publisher |
| `vargha2000critique` | Published; no matching arXiv located | [DOI](https://doi.org/10.3102/10769986025002101) | doi, pages, title |
| `holm1979simple` | Published; no matching arXiv located | [Journal archive](https://www.jstor.org/stable/4615733) | None |
| `wilcoxon1945individual` | Published; no matching arXiv located | [DOI](https://doi.org/10.2307/3001968) | pages |
| `mcnemar1947note` | Published; no matching arXiv located | [DOI](https://doi.org/10.1007/bf02295996) | None |
| `efron1993introduction` | Published; no matching arXiv located | [DOI](https://doi.org/10.1201/9780429246593) | None |
| `wohlin2012experimentation` | Published; no matching arXiv located | [DOI](https://doi.org/10.1007/978-3-642-29044-2) | address, doi, publisher, year |
| `demoura2008z3` | Published; no matching arXiv located | [DOI](https://doi.org/10.1007/978-3-540-78800-3_24) | address, booktitle, publisher, series, volume |
| `cook1971complexity` | Published; no matching arXiv located | [DOI](https://doi.org/10.1145/800157.805047) | address, publisher |
| `lomuscio2017mcmas` | Published; no matching arXiv located | [DOI](https://doi.org/10.1007/s10009-015-0378-x) | year |
| `leveson2011engineering` | Published; no matching arXiv located | [DOI](https://doi.org/10.7551/mitpress/8179.001.0001) | publisher |
| `ferrante1987program` | Published; no matching arXiv located | [DOI](https://doi.org/10.1145/24039.24041) | None |
| `reiter1987theory` | Published; no matching arXiv located | [DOI](https://doi.org/10.1016/0004-3702(87)90062-2) | None |
| `ruijters2015fault` | Published; no matching arXiv located | [DOI](https://doi.org/10.1016/j.cosrev.2015.03.001) | None |
| `cimatti2015contracts` | Published; no matching arXiv located | [DOI](https://doi.org/10.1016/j.scico.2014.06.011) | None |
| `cofer2012compositional` | Published; no matching arXiv located | [DOI](https://doi.org/10.1007/978-3-642-28891-3_13) | address, booktitle, publisher, series |
| `bozzano2014formal` | Published; no matching arXiv located | [DOI](https://doi.org/10.1007/978-3-319-11936-6_7) | address, booktitle, publisher, series |
| `clarke2003cegar` | Published; no matching arXiv located | [DOI](https://doi.org/10.1145/876638.876643) | None |
| `mcmillan1999circular` | Published; no matching arXiv located | [DOI](https://doi.org/10.1007/3-540-48153-2_30) | address, booktitle, publisher, series |
| `namjoshi2010completeness` | Published; no matching arXiv located | [DOI](https://doi.org/10.1145/1740582.1740584) | None |
| `pozzi2006exact` | Published; no matching arXiv located | [DOI](https://doi.org/10.1109/TCAD.2005.855950) | None |
| `ball2003symptom` | Published; no matching arXiv located | [DOI](https://doi.org/10.1145/604131.604140) | address, publisher |
| `groce2006error` | Published; no matching arXiv located | [DOI](https://doi.org/10.1007/s10009-005-0202-0) | None |

## Build validation

Both manuscript layouts were rebuilt with latexmk/pdfLaTeX and BibTeX. Citation keys and reported experimental values are unchanged. LaTeX logs have no undefined references/citations or overflowing boxes. The BibTeX warnings above concern optional address metadata, not unresolved citations.
