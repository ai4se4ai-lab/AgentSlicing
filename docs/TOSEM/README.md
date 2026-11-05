# TOSEM manuscript

`main.tex` is the complete paper adapted from `../TSE/main.tex`. The TSE files are unchanged.

- `main.pdf`: submission manuscript, ACM single-column `manuscript,screen,review` format with line numbers (40 pages).
- `journal-preview.pdf`: ACM `acmsmall` journal-layout preview without review line numbers (41 pages).
- `journal-preview.tex`: small wrapper around `main.tex`; all paper content remains in one source.

Build both PDFs from this directory:

```sh
make
```

Or build them individually:

```sh
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
latexmk -pdf -interaction=nonstopmode -halt-on-error journal-preview.tex
```

The builds require a current TeX Live installation with the ACM class and bibliography style, Libertine/Inconsolata/NewTX fonts, TikZ/PGFPlots, algorithm/algorithmic, multirow, adjustbox, tabularx, listings, needspace, and tcolorbox (skins/breakable). Figures, tables, and generated result macros are embedded in `main.tex`; the TOSEM source does not depend on the TSE directory at build time. `make clean` removes auxiliary build files and retains the PDFs.

The default follows ACM's [submission-format guidance](https://www.acm.org/publications/authors/submissions). TOSEM uses `acmsmall` for the journal layout; see the [ACM class guide](https://mirrors.ctan.org/macros/latex/contrib/acmart/acmguide.pdf). `nonacm` suppresses unassigned publication identifiers and rights boilerplate while retaining the ACM layout. Actual rights metadata must come from ACM after acceptance.

Anonymous authorship is retained from the TSE source. Replace it with the correct author and affiliation information if required by the selected submission track. No author identities, DOI, issue, volume, acceptance date, or publication year have been invented.

## Validation

Both PDFs were compiled with latexmk/pdfLaTeX and BibTeX, and inspected visually. Final LaTeX logs contain no warnings, unresolved citations/references, or overfull boxes. All PDF fonts are embedded, and all 67 cited works resolve. The additional-tables appendix and its cross-reference have been removed. Experimental values and the bibliography are preserved; table presentation is adapted for normal-size text.

Layout adjustments include full-width Tables 3 and 4 with expanded wording, normal-size table text, merged single-grid result tables (Tables 10, 11, and 14), and rounded light-gray research-question callouts. The Team Specification Language appendix now describes parser defaults, contracts, topology construction, validation, and model revision. Its JSON example and Python analysis listing were executed against the implementation; the example produces the two stated missing-goal keys, and the all-join repair has no symptoms at fault budget zero. Listings use compact 8-point monospaced text with 10-point line spacing, muted syntax colors, a light-gray background, and line numbers. This formatting and documentation revision is not a new scientific review.

BibTeX still reports 37 nonfatal metadata warnings for missing publisher/address fields in the inherited bibliography. References render and every citation resolves; the source bibliography was preserved rather than filling gaps with unverified metadata.
