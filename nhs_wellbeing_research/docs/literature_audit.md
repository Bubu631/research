# Literature and novelty audit

Checked 2026-09-11. Primary research papers, publisher/author copies, official proceedings and NHS documentation were used. Search results are discovery aids; unverified publisher status is not silently promoted to a journal publication. The candidate bibliography is `candidate_references.bib` in this directory.

## Main finding

Temporal empirical Bayes ranking of health institutions is already directly covered by earlier work. Gaussian filtering, regression to the mean, heteroskedastic ranking and selecting by a posterior loss cannot be claimed as new methods. A defensible paper can contribute an unusually explicit **decision and identification audit**: separate observable forecasting from latent ranking, show how ranking objectives differ, report an exact restricted noise-sensitivity map, and execute a carefully versioned NHS panel study without causal or departmental extrapolation.

## Closest primary research

### 1. Repeated health-provider empirical Bayes ranking

Hans C. van Houwelingen, Ronald Brand and Thomas A. Louis, *Empirical Bayes methods for monitoring health care quality*, manuscript posted as [arXiv:2009.03058](https://arxiv.org/abs/2009.03058). The full [author-submitted PDF](https://arxiv.org/pdf/2009.03058) was downloaded and read, especially Sections 6–7 (printed pages 17–21). Its original material appears older than its arXiv posting; no journal publication was verified, so cite the available 2020 record without inventing one.

This is a direct predecessor, not a distant generic EB citation. It gives conditional Gaussian predictions from repeated provider measurements, explicitly fits stationary autoregressive and random-coefficient latent structures, uses measurement precision related to provider size, and assesses predictive rankability. Its observational caution is also explicit. The new paper must not claim that combining temporal provider data, measurement precision and shrinkage is a new algorithm.

### 2. Decision-theoretic selection under heterogeneous precision

Jiaying Gu and Roger Koenker (2023), *Invidious Comparisons: Ranking and Selection as Compound Decisions*, **Econometrica 91(1):1–41**, DOI [10.3982/ECTA19304](https://doi.org/10.3982/ECTA19304). The [official published PDF](https://www.econometricsociety.org/publications/econometrica/2023/01/01/Invidious-Comparisons-Ranking-and-Selection-as-Compound-Decisions/file/ecta200493.pdf) verifies authors, title and pages.

It already formulates selection from noisy scalar measurements with heterogeneous precision as a compound decision problem, connects it to multiple testing, and applies methods to dialysis providers. Our fixed-k posterior-severity regret result is an elementary Bayes action under a chosen loss, not a new general optimal-ranking principle. The restricted noise-multiplier threshold map should be presented as a diagnostic specialization.

### 3. Loss-specific rankings

Rongheng Lin, Thomas A. Louis, Susan M. Paddock and Greg Ridgeway (2006), *Loss Function Based Ranking in Two-Stage, Hierarchical Models*, **Bayesian Analysis 1(4):915–946**, DOI [10.1214/06-BA130](https://doi.org/10.1214/06-BA130). [PubMed's primary article record](https://pubmed.ncbi.nlm.nih.gov/20607112/) provides verified metadata and abstract; the PMC mirror presented a browser challenge and was not bypassed.

The paper studies rank losses and classification relative to percentile cutpoints, with renal-provider data. The manuscript should cite it before contrasting posterior means, expected ranks and bottom-k membership probabilities. A rule optimal for one of these is not automatically optimal for the others.

### 4. Agreement between true and reported top lists

Nicholas C. Henderson and Michael A. Newton (2016), *Making the cut: improved ranking and selection for large-scale inference*, **JRSS Series B 78(4):781–804**, DOI [10.1111/rssb.12131](https://doi.org/10.1111/rssb.12131). The [author-hosted published PDF](https://pages.stat.wisc.edu/~newton/papers/publications/rvalues.pdf) and [author publication list](https://pages.stat.wisc.edu/~newton/papers/publications/) verify publication. An earlier arXiv full text was downloaded and examined.

Their r-value procedure studies agreement between leading lists while accounting for unequal measurement precision. It helps explain why raw means can overrepresent noisy units and testing-based ranks can favor precise units. Their population-quantile and capacity formulation should not be conflated with our exact finite-M probability that unit i belongs to the realized latent bottom k. Both objectives are established selection problems, not a new discovery.

### 5. Recent heteroskedastic ranking and resource constraints

Bowen Gang, Luella Fu, Gareth M. James and Wenguang Sun (2026), *Ranking and selection in large-scale inference of heteroscedastic units*, **The Annals of Applied Statistics 20(1)**, DOI [10.1214/25-AOAS2123](https://doi.org/10.1214/25-AOAS2123). Its [arXiv version](https://arxiv.org/abs/2306.08979) predates publication. The [official IMS issue contents](https://www.imstat.org/publications/aoas/aoas_20_1/aoas_20_1.pdf) and publisher-deposited Crossref record establish the March 2026 journal appearance. The candidate entry omits an unverified ending page rather than assuming one from the next article's start.

The paper directly treats constrained ranking/selection of heterogeneous-precision units with practical magnitude and error-rate considerations. Describing our study as the first general finite-resource extension of noisy rankings would be untenable. Its objective and error control differ from a declared posterior-severity or membership loss.

### 6. Robust empirical Bayes ranking under regression-model error

Nicholas C. Henderson and Nicholas Hartman (2025), *Targeted Parameter Estimation for Robust Empirical Bayes Ranking*, [arXiv:2511.16530](https://arxiv.org/abs/2511.16530). The 49-page [full preprint](https://arxiv.org/pdf/2511.16530) was downloaded; the introduction, targeted rank-loss construction and stated scope were read. No peer-reviewed publication was established.

It targets regression parameters using ranking loss rather than ordinary likelihood, with robustness to covariate-adjustment misspecification and a longitudinal school example. It is a close warning against equating good mean-model fit with good ranks. Our interval sensitivity certificate addresses uncertainty in a fixed common measurement-noise multiplier; it is not this broader robust EB estimator and should not be presented as a substitute for it.

### 7. Provider size and non-quality heterogeneity

Lu Xia, Kevin He, Yanming Li and John Kalbfleisch (2022), *Accounting for total variation and robustness in profiling health care providers*, **Biostatistics 23(1):257–273**, DOI [10.1093/biostatistics/kxaa024](https://doi.org/10.1093/biostatistics/kxaa024). The [publisher record](https://academic.oup.com/biostatistics/article-abstract/23/1/257/5856610) and [PubMed metadata](https://pubmed.ncbi.nlm.nih.gov/32530460/) agree. The [arXiv PDF](https://arxiv.org/pdf/1907.07809) was downloaded and read. Online publication was 2020; the journal issue year is 2022.

It addresses variation outside provider control and develops a size-adaptive empirical-null approach. This directly cautions against labeling all between-organisation dispersion as management quality or treating variance-versus-size relationships as pure sampling noise. It does not identify response-level NHS wellbeing noise from aggregate scores.

### 8. Verification of Gaussian ranks is also established

Jeremy Goldwasser, Will Fithian and Giles Hooker (2025), *Gaussian Rank Verification*, **Stat 14(3):e70087**, DOI [10.1002/sta4.70087](https://doi.org/10.1002/sta4.70087). The [university repository](https://escholarship.org/uc/item/109601xh), [publisher issue](https://onlinelibrary.wiley.com/toc/20491573/2025/14/3) and publisher-deposited DOI metadata establish publication. One author page lists issue 2, conflicting with the publisher; the candidate entry follows issue 3. The [arXiv abstract](https://arxiv.org/abs/2501.14142) describes heteroskedastic Gaussian winner and top-k verification.

This is relevant if the manuscript uses the word “certificate.” Our posterior regret bound and deterministic κ-interval membership certificate are not frequentist selective-inference rank verification with known standard errors. The empirical NHS noise variances are not automatically known, so no off-the-shelf rank guarantee follows.

## Classical foundations that should be credited

- Adrian G. Barnett, Jolieke C. van der Pols and Annette J. Dobson (2005), *Regression to the mean: what it is and how to deal with it*, **International Journal of Epidemiology 34(1):215–220**, [DOI 10.1093/ije/dyh299](https://doi.org/10.1093/ije/dyh299). Online appearance was 2004, issue year 2005. It covers apparent changes produced by baseline selection and measurement variation. Our conditional AR(1) expression makes model components explicit but does not discover RTM.
- Harvey Goldstein and David J. Spiegelhalter (1996), *League Tables and Their Limitations: Statistical Issues in Comparisons of Institutional Performance*, **JRSS Series A 159(3)**. The [university-hosted published PDF](https://www.bristol.ac.uk/media-library/sites/cmm/migrated/documents/statistical-issues-for-league-tables1.pdf) includes discussion through page 443. We cite 385–443 with a discussion note rather than confusing the shorter main-paper range with the full discussion article. Measurement uncertainty, contextualization and limitations of health/education rankings are longstanding concerns.
- R. E. Kalman (1960), *A New Approach to Linear Filtering and Prediction Problems*, **Journal of Basic Engineering 82(1):35–45**, [DOI 10.1115/1.3662552](https://doi.org/10.1115/1.3662552), with the [original paper hosted at UNC](https://www.cs.unc.edu/~welch/kalman/media/pdf/Kalman1960.pdf). Posterior conditioning/optimal filtering is classical. A publisher access attempt returned 403 and no access control was bypassed.

## Official NHS facts affecting scientific validity

The [official survey information page](https://nhssurveys.co.uk/nss/survey-information/) distinguishes occupation weighting within benchmarking groups from organisation-size weighting for aggregated outputs. It explicitly says prior-year results displayed in 2025 are reweighted to the 2025 occupation profile. Thus a common 2025-vintage panel can support retrospective temporal validation, but strict historical-release forecasting requires archived vintages or a clear limitation. The same page confirms higher 0–10 scores indicate better experiences.

The [official FAQ](https://www.nhsstaffsurveys.com/faqs/) says benchmark organisation reports are occupation-weighted, whereas directorate/breakdown results are unweighted. It discourages a single top/bottom list across all organisation types, and advises comparisons within benchmark groups. It also distinguishes confidentiality suppression below 10 responses from score interpretation and says published aggregates cannot reproduce all composite-score calculations. These facts undermine the outline's automatic three-weight product, universal departmental thresholds and national league-table framing.

The [2025 Guide to Understanding and Using Results](https://www.nhsstaffsurveys.com/static/78c1b2ea66833a3c9ca46834477a204b/NHS-Staff-Survey-2025-A-Guide-to-Understanding-and-Using-Results.pdf) is a separate official source for interpretation and reporting. Dataset download URLs and releases should additionally be documented by the data-audit agent; the present audit does not claim that all field-level comparability issues have been resolved.

## What the new paper could honestly add

1. A linked diagnostic from declared decision objective to latent/noise assumptions, then to a reproducible public-panel validation that only claims what its observations can test.
2. A precise counterexample showing that identical observed Gaussian panels can support different latent/noise decompositions, while carefully distinguishing common-noise rescaling from actual mean-rank nonidentification under heterogeneous latent variance.
3. A transparent restricted noise-multiplier ranking-flip map: pairwise affine sign functions yield exact interval stability under stated one-year assumptions. Its usefulness should be demonstrated by real sensitivity calculations; algebra alone is a modest contribution.
4. Paired simulations separating score-severity regret, true latent bottom-k overlap, predictive MSE, selection-induced observed change and intervention inference. These quantities should not be collapsed into one “ranking quality” number.
5. A genuinely audited NHS application: benchmark-aware comparison, annual weighting-vintage checks, retained failed predictions, sensitivity to nonresponse/common trends, and no pretense of verified departmental sample-size thresholds.

The proposed result is closer to statistical decision analysis and health-services measurement than a novel machine-learning architecture. Conference competitiveness depends on the executed evidence and the importance of its findings; this audit does not establish a first-of-its-kind theorem or promise acceptance.

## Source-access and metadata record

Full PDFs were locally downloaded for van Houwelingen et al., Henderson–Newton, Henderson–Hartman and Xia et al. under the private research workspace for reading; source URLs above remain the authoritative references. Publisher/author originals were checked for Gu–Koenker and Goldstein–Spiegelhalter. Some publisher pages rejected direct retrieval; available primary author copies, official issue records and publisher-deposited DOI metadata were used, without bypassing access controls. Recent references were searched as of 2026-09-11. No relevant source was found that justifies importing the outline's fixed 20/120-response or 15-percentage-point rules into NHS departments.
