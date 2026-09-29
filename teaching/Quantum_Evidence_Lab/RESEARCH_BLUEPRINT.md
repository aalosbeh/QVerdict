# Quantum Computing Education and Software Assurance Research

Research blueprint for a two university collaboration

Prepared for Dr Anas AlSobeh and a collaborating faculty member

Evidence reviewed through 24 September 2026

## 1 Recommended research direction

Develop and evaluate an accessible quantum software verification curriculum in which students learn to decide what evidence justifies trusting a quantum program. The central learning objective is to select a discriminating test, interpret uncertainty, and recognize when the evidence cannot support a decision. Use free local simulations, a shared assessment, and a controlled study at two universities.

The proposed paper title is **Learning to Verify Quantum Programs through Uncertainty Aware Feedback Across Two Universities**. The strongest initial venue fit is **IEEE Transactions on Education**, with a Scholarship of Discovery framing if the study generates new educational knowledge. A more technically ambitious version can target **IEEE Transactions on Learning Technologies** if a genuinely new feedback system is developed and evaluated. The present pilot is useful preliminary work, but it is not a submission-ready Transactions paper.

The project's scientific question is: **Can students learn to recognize the limits of their tests and select sufficient evidence for quantum software decisions, and does this ability transfer to unfamiliar tasks?** This question is narrower and more defensible than proposing a new quantum course, a general AI tutor, or a quantum machine learning demonstration.

Your earlier correspondence establishes an interest in accessible quantum education for Information Systems and Technology students and potential curriculum exchange with Dakota State. It does not establish a research commitment by that institution or identify the collaborator for this project. The design below works with your actual partner university once courses, expertise and enrollment are confirmed.

The intended novelty is an educational mechanism and its evidence: explicit reasoning about observability, uncertainty and the scope of a software claim. Known state-verification mathematics provides the technical foundation. The study must show a contribution beyond existing accessible quantum instruction, autograding and quantum software engineering courses. No claim of being the first system or guaranteeing journal acceptance is justified at this stage.

## 2 Research scope and evidence quality

This is a targeted research landscape review, not a completed systematic literature review. Searches covered quantum education, student reasoning and assessment, quantum software testing and debugging, AI-assisted repair, accessible tools, IEEE journal guidance and active NSF programs. Publication dates and source status were checked against the September 2026 cutoff. Primary papers, author manuscripts, official documentation and official program pages were preferred.

Important query families included quantum programming education and assessment; quantum software testing and debugging benchmarks; adaptive measurements and shot budgets; AI quantum program repair; quantum conceptual surveys; and NSF IUSE and Future CoRe. Backward checks included the 2026 software engineering course report and established quantum state verification. Recent arXiv items were screened as emerging work; some were available only through indexed primary-source abstracts. Their detailed methods have not been independently reproduced here.

The most decision-relevant accessible sources are the 2024 quantum autograding paper, the 2026 quantum software engineering course manuscript, the official IEEE journal criteria, and current NSF solicitations. The 2026 QCCS and defect reproducibility preprints are valuable leads, but publication status and instrument versions should be reconfirmed before manuscript submission. A search that does not find an identical intervention does not prove uniqueness.

Before preregistration, the two faculty should complete a structured novelty matrix using IEEE Xplore, ACM Digital Library, Scopus or Web of Science if institutional access is available, and arXiv. Record search strings, dates, screening rules, inclusion decisions and citation chaining. Compare methods and outcomes, not only titles. This is the remaining step needed before describing the literature review as systematic.

## 3 Current directions and their value for this project

| Direction | Evidence and significance | Recommended role |
|---|---|---|
| Quantum software quality and reproducibility | Roadmaps and practitioner research identify testing, limited observability, dependencies and debugging as important problems [3–5]. | Core research area and workplace connection. |
| Measurement cost and uncertainty | QuFid already studies adaptive noise-aware measurement budgets; efficient state verification has a much longer history [6, 7]. | Teach and reuse; do not claim adaptive shots as a new invention. |
| AI-assisted quantum programming | QBugLM and recent repair benchmarks show that this is already an active research area [10, 11]. | A carefully scoped extension about verifying suggestions and learning transfer. |
| Research-based quantum assessment | QCCS and the 2026 education resource letter strengthen the assessment landscape [12–14]. | Combine appropriate concept assessment with a new, separately validated performance task. |
| Hybrid quantum and classical workflows | IBM's current course catalog includes quantum and HPC integration; Project Triad emphasizes integrated quantum systems [21, 30]. | Context for IT operations and later research expansion. |
| Post-quantum migration | NIST has published ML-KEM, ML-DSA and SLH-DSA standards and migration resources [22, 23]. | Strong companion strand for IS and IT, kept conceptually distinct from quantum programming. |
| Error correction and resource estimation | Current IBM and Microsoft materials support advanced study of fault tolerance and resource requirements [18, 21]. | An advanced elective extension after the core study. |

Post-quantum cryptography uses classical algorithms designed to resist quantum attacks. It is not quantum key distribution and does not require a quantum computer. A quantum circuit lesson must not be presented as a practical implementation of post-quantum security. Likewise, a laptop simulation can establish software behavior under its model; it cannot demonstrate hardware quantum advantage.

The assessment of which direction is best is a project-specific judgment, not a bibliometric ranking. For this collaboration, software verification offers a useful combination of relevance, low cost, clear performance measures and a manageable first experiment.

Four concrete opportunities deserve different priorities. **First**, uncertainty-aware verification education is the recommended first paper because its mechanism and outcomes can be studied affordably. **Second**, a reproducibility workbench for quantum teaching artifacts could become a strong separate software-engineering project, but must add more than version pinning and must compare with existing benchmark infrastructure. **Third**, a post-quantum migration curriculum built around cryptographic inventory and decision evidence is especially relevant to IS/IT, but its research question would concern cybersecurity learning and adoption rather than quantum programming. **Fourth**, a quantum machine-learning cybersecurity classifier is an optional advanced project; simply adding a quantum model to a familiar dataset is unlikely to establish a distinctive contribution without careful classical baselines, resource accounting and a specific scientific hypothesis.

## 4 Closest prior work and the defensible gap

| Prior work | What it already contributes | What this proposal must add |
|---|---|---|
| Salehi, Seskir and Tepe, IEEE Transactions on Education [1] | A CS-oriented entry to quantum computing using linear algebra and programming. | Evidence of a specific verification-reasoning mechanism, rather than accessibility alone. |
| Beaumont and Wakevainen, ITiCSE 2024 [2] | Efficient autograding using quantum-function equivalence and reuse across similar submissions. | Students choosing sufficient evidence and demonstrating delayed transfer; not merely faster grading. |
| Miranskyy, 2026 course report [3] | A full quantum software engineering course with executable artifacts and lifecycle reasoning. The report is observational. | A controlled, two-site test with a matched comparator and blinded performance scoring. |
| Testing and debugging roadmap [4] and practitioner study [5] | Existing testing approaches, development challenges and practical needs. | A targeted educational intervention linked to observable engineering behaviors. |
| QuFid, AAAI 2026 [6] | Adaptive measurement planning for fidelity estimation on noisy backends. | A learning contribution or new feedback design, not an adaptive-shot novelty claim. |
| State verification literature [7] | Efficient verification using suitable quantum measurements. | Translation into accessible evidence reasoning and demonstration of its educational effect. |
| Bugs4Q [8] and 2026 reproducibility study [9] | Real defects and evidence that benchmark execution can depend strongly on SDK versions. | A versioned teaching benchmark with equivalent controls, uncertainty cases and traceable defect provenance. |
| QBugLM and LLM repair benchmark [10, 11] | Automated or model-assisted quantum debugging and repair. | Whether students learn to evaluate proposals independently, rather than the model's repair accuracy alone. |
| QCCS and curriculum research [12–15] | Conceptual assessment and evidence about introductory content. | A complementary assessment of verification actions and inference limits. |

The 2026 course report is particularly important: a paper claiming that software engineering is a new way to teach quantum would be difficult to defend. Our narrower claim should concern **the transfer of evidence selection and calibrated decision-making**, measured on unseen programs.

The proposed contribution bundle has four elements. First, define an observable competency progression from interpreting counts to designing a discriminating test. Second, implement feedback that distinguishes an unsupported claim from a contradicted claim. Third, evaluate it against equally intensive instruction. Fourth, release reusable tasks, code, rubrics and a reproducibility guide. These are proposed contributions until evaluated; their combination is a candidate gap, not proof of unprecedented work.

## 5 What students learn and why universities would adopt it

All students learn the same quantum foundations: qubits, small state vectors, superposition, relative versus global phase, H/X/Z/CNOT gates, entanglement, measurement bases and sampling. A common mathematical bridge covers complex numbers, probabilities, two-by-two matrices and tensor products through worked examples. Accessibility means teaching the necessary mathematics explicitly, not removing it.

| Audience | Authentic task | Observable evidence |
|---|---|---|
| CS and software engineering | Test a quantum subroutine, detect a hidden phase defect and accept an equivalent implementation. | Correct tests, defensible assertions and regression cases. |
| IT | Reproduce an experiment, inspect dependency versions, separate execution failure from statistical variation and document a hybrid workflow. | Environment manifest, successful replay and a justified troubleshooting decision. |
| IS | Convert a stated requirement into an acceptance criterion and communicate whether the evidence supports deployment or further investigation. | Traceable acceptance record, uncertainty statement and decision rationale. |

Every track retains genuine quantum content. An IS student must explain why a measurement cannot distinguish candidate states; an IT student must reason about the difference between simulator behavior and a physical backend; a CS student must state the limits of testing a single input.

Adoption can begin with one 60–90 minute lesson, then a six-week module inside an existing software engineering, emerging technologies or applied computing course. A full elective is a later option. Use a shared repository, instructor answer keys, a short readiness diagnostic, accessible written explanations, tested package versions and a simulator-only fallback. The current package includes the first lesson and technical pilot, not all six finished modules.

Institutional value should be measured through implementation evidence: instructor preparation time, student setup success, completion, learning outcomes, maintenance burden and intention to reuse backed by an actual next offering. Do not use projected quantum employment demand as the sole justification. The immediate transferable capabilities are testing, reproducibility, statistical reasoning and responsible technical decision-making.

## 6 Proposed learning design

Each exercise follows a concrete sequence: state the claim; predict what a test should show; choose and run the test; assess the strength and limits of the evidence; decide whether to accept, reject or gather more evidence; then justify a repair or next test. This is an instructional design proposal, not a claim to have invented inquiry-based learning.

| Week | Quantum and engineering focus | Student product |
|---|---|---|
| Bridge | Python, probability, complex numbers and small matrices | Readiness check and worked examples |
| 1 | States, gates and finite-shot variation | Prediction and reproducible run record |
| 2 | Relative phase and measurement bases | A test that catches a Z-invisible defect |
| 3 | Entanglement versus classical correlation | Evidence distinguishing a Bell state from a mixture |
| 4 | Tolerances, confidence and inconclusive results | Acceptance rule with stated assumptions |
| 5 | New inputs, bit ordering and environment drift | Regression tests and reproduction report |
| 6 | Unseen case and stakeholder decision | Verification portfolio and individual assessment |

Feedback should identify what evidence is missing without immediately revealing the repair. For example: “These Z-basis results are compatible with more than one state. Which permitted test could distinguish them?” Later prompts can show a partial worked example. Fade the scaffold as competence develops, and assess delayed transfer without it.

For a more ambitious learning-technology paper, develop a counterexample-guided feedback engine. Given a task contract, test history and a bounded candidate set, it would select a next measurement or prompt that distinguishes remaining explanations. It must disclose when multiple explanations remain observationally equivalent. Compare its prompts with fixed expert hints and a nonadaptive feedback system. This engine is proposed work; the supplied code implements measurement evidence, not adaptive tutoring.

## 7 Concrete example and completed technical pilot

The target is the Bell state Phi-plus, the equal coherent combination of 00 and 11. A phase-flipped program prepares Phi-minus, the equal combination with a minus sign. Both give exactly the same ideal Z-basis distribution: 50% 00 and 50% 11. More Z samples cannot resolve the difference. Measuring both qubits in X reveals even parity for the target and odd parity for the phase-flipped state.

This example is a standard quantum fact, not a novel algorithm. Its research value is that it makes a common verification error observable: accepting a claim because an inadequate test passed. A second case compares the Bell state with an incoherent 00/11 mixture. A third accepts a global phase change as equivalent. Together they test whether students can avoid both missed defects and unnecessary repairs.

The local pilot executed 17 hand-selected output states with 400 simulated repetitions per state and four testing policies. Each policy therefore has 6,800 case-runs, totaling 27,200 final policy outcomes. These are synthetic measurement trials, not human participants or independent circuit families. The required output-state fidelity was set to at least 0.90. This is an instructional specification, not an industry threshold.

| Testing policy | Wrong decisions out of 6800 | Inconclusive outcomes | Mean shots |
|---|---|---|---|
| Z-only teaching negative control | 2597 | 0.00% | 1536.0 |
| Fixed XX and ZZ confidence rule | 7 | 35.37% | 1536.0 |
| Staged XX and ZZ confidence rule | 5 | 37.81% | 800.7 |
| Fixed XX YY and ZZ confidence rule | 0 | 32.57% | 1536.0 |

The staged rule used 47.9% fewer shots on average than fixed XX/ZZ for this suite, with a higher inconclusive rate. This is a cost-versus-resolution tradeoff, not proof of overall superiority. The three-basis comparator resolved more cases. Zero observed wrong decisions for that comparator does not mean its error probability is zero.

For the phase-flipped case, the Z-only rule falsely supported the contract in all 400 repetitions. Both two-basis methods contradicted it in all 400; the staged rule stopped at 96 shots. For the exact-threshold phase-mixture case, almost all statistically controlled decisions remained inconclusive. Seven and five wrong rejections, respectively, occurred in the fixed and staged two-basis rules. Including these outcomes prevents a misleading perfect-performance claim.

The statistical rules use exact binomial intervals and account for multiple observables. The staged rule also accounts for all three planned looks at cumulative budgets of 96, 384 and 1536. Support requires the entire fidelity interval to be above the specification; contradiction requires it below; otherwise the decision is inconclusive. The README derives the bounds and defines the fidelity convention. Validity assumes independent identical preparations and trusted measurements; it does not cover arbitrary hardware drift or biased readout.

The NumPy/SciPy pilot ran in Python 3.12.14. An independent local Qiskit 2.5.2 calculation checked all 51 state/basis probabilities, with maximum absolute discrepancy approximately 3.33 times ten to the minus sixteen. Analytic fixtures and 200 random density matrices also checked the fidelity relationships. No QPU, paid service, live AI model or student data was used. The package contains version pins, raw counts, results and runnable code.

Most importantly, a failed state contract does not identify its cause. A code defect and a physical channel can sometimes produce indistinguishable output states. Root-cause diagnosis requires additional evidence such as ideal-simulator replay, calibration data or controlled interventions. The paper should teach this limitation rather than train students to infer an unsupported cause.

## 8 Two university study needed for publication

Use a common six-week module with treatment and active-control groups at both universities. Match time, concepts, tools, measurement options and staff support. The treatment receives the explicit evidence-reasoning scaffold and graduated prompts. The control receives conventional feedback and worked explanations of comparable length. Withholding the useful measurement basis from the control would create an unfair test.

The primary research question concerns delayed performance on unfamiliar verification tasks. Secondary questions concern unnecessary repairs, confidence calibration, reproduction success and differences associated with prior readiness. Questions about CS, IS and IT differences should be exploratory unless the design has sufficient subgroup size and comparable measurement.

Randomize within institutions and sections; do not place one university entirely in each condition. Start with 8–12 cognitive interviews and a 20–40 student feasibility pilot. For planning only, approximately 128 analyzable students gives 80% power for a two-sided independent-group test of an effect size of 0.50 at alpha 0.05. Recruiting 160 assumes 20% attrition. This is not a prediction of the effect. Recalculate with actual variance, reliability, clustering and the intended model before recruitment.

If randomization occurs in lab groups or sections, account for that clustering and recruit enough groups. Two institutions do not constitute enough clusters for a university-level experiment. If total enrollment is small, use an explicitly exploratory study or additional cohorts; do not count repeated tasks as additional students.

The primary outcome is a prespecified delayed transfer score on four unseen tasks, scored using a 0–4 rubric per task. Include phase sensitivity, harmless equivalence, finite-sample ambiguity and an unfamiliar input or ordering issue. Use blinded raters, expert review, cognitive interviews and parallel forms. Report reliability and response-process evidence. The QCCS can be a secondary conceptual measure if it matches the taught material and its developers permit the intended use [12–14]. Its current public page still contains earlier-term access instructions, so obtain the current instrument directly.

Preregister the estimand, primary outcome, allocation, exclusions, missing-data plan and multiplicity handling. Analyze the assigned treatment with baseline and site/section adjustment appropriate to the allocation. Report effect estimates and confidence intervals, not only p-values. Preserve student dependence in task-level analyses. Document attrition, contamination, instructor effects, fidelity of implementation and assessment limitations.

Obtain the relevant institutional human-subjects determination before collecting research data. Arrange consent, equivalent educational access, separation of research participation from grades, deidentification and a cross-site data agreement. These arrangements enable a credible study; they are not completed by this report.

## 9 Technical benchmark expansion and AI extension

The present two-qubit demonstration is intentionally small. A publishable technical evaluation should include multiple circuit families, unseen task templates, equivalent transformations, known noise models, genuine defects where reproducible, and version failures identified separately from semantic faults. A proposed starting design is 8–12 families and approximately 100–200 reviewed instances; the final size should follow defect coverage and feasibility, not an arbitrary large number.

Add GHZ preparation, Bernstein–Vazirani, small teleportation components, reversible subroutines and simple parameterized circuits only when each has a clear specification. Separate testing one prepared output from testing a function over inputs. Evaluate measurement selection, erroneous feedback, abstention, computational cost and failures across held-out families. Use real Bugs4Q cases only after revalidating them under pinned environments; older defects may disappear or change meaning [8, 9].

Competitive comparisons must include a strong fixed multi-basis method, established verification or equivalence techniques where their assumptions match, and expert-designed feedback. A Z-only heuristic is a teaching negative control, not sufficient evidence for beating the state of the art. Use ablations of uncertainty display, claim explanation, adaptive hints and measurement selection. Resample circuit families when estimating generalization; repeated shots on one fixture do not establish cross-program validity.

AI is optional for the first paper. Avoid a complicated factorial study until the base intervention is reliable. A later study can compare scaffold on/off and AI assistance on/off, with a separately justified sample size. Preserve actual prompts, model identifiers, dates, settings and generated artifacts. Check every proposed repair against held-out tests and measure unsupported confidence as well as correctness. Instructor-created defects must not be labeled naturally occurring AI errors.

A free baseline can use frozen, clearly attributed code suggestions or an appropriately licensed local model when available. The current package uses instructor-prepared examples, so it incurs no model cost and makes no claims about model performance. The research outcome should distinguish students succeeding with assistance from students retaining independent competence.

## 10 Free resources and sensible tool choices

| Resource | Best use | Access and limitation |
|---|---|---|
| IBM Quantum Learning and classroom modules [16, 21] | Main quantum concepts and short CS activities | Public learning materials; use current platform pages rather than archived textbook tutorials. |
| Qiskit local simulation [17] | Repeatable Python experiments and circuit validation | No cloud account for local execution. Pin and record versions. |
| Quirk [19] | First visual explanation of gates and measurement | Free browser simulator for small circuits; supply textual alternatives. |
| QWorld QBronze [20] | Programming and mathematics bridge | Public notebooks and free workshop offerings; check notebook compatibility and reuse license. |
| Microsoft QDK Learning and Katas [18] | A second language or advanced software-engineering extension | Free open-source toolkit; do not assume optional Copilot or cloud execution is free. |
| PennyLane Codebook [24] | Optional mathematical and QML enrichment | Public interactive resource; unnecessary for the core pilot. |
| ACE QIS and QCCS [12, 14] | Research-informed curriculum and concept assessment | Check access and adaptation conditions; do not publish restricted assessment items. |
| NIST PQC and migration guidance [22, 23] | IS and IT extension on cryptographic inventory and transition | Public guidance; this is classical post-quantum security, not quantum circuit programming. |

Use one primary SDK for the first study. The recommended stack is Python, local Qiskit, NumPy/SciPy, notebooks or VS Code, and a versioned project repository. No GPU or HPC allocation is required for the supplied two-qubit experiment. Small simulations make installation, replication and assessment much easier to control.

IBM Classroom Accounts are an optional demonstration route. Current documentation specifies 10 minutes of QPU use per instance per rolling 28-day window, subject to the account process and access conditions [16]. They are not an unlimited research resource. Hardware access should enrich the course without becoming a dependency for completing assignments or collecting the primary outcomes.

Free tools do not make the project costless. Faculty time, student research assistance, assessment expertise, accessibility, participant support and maintenance need institutional support or funding. Publication may also involve charges: the current ToE guidance offers a traditional route without an open-access payment, while optional open access and excess-length charges have separate rules [25].

## 11 Journal strategy and example manuscript

| Venue | Fit for this project | Evidence needed |
|---|---|---|
| IEEE Transactions on Education | Best initial fit for a rigorous learning and assessment study | Educational question, defensible measurement, strong comparator and evidence beyond satisfaction. |
| IEEE Transactions on Learning Technologies | Strong conditional fit for a substantive new feedback technology | Technical or design knowledge plus convincing support for learning. A course evaluation alone is insufficient. |
| IEEE Transactions on Quantum Engineering | Possible later technical paper | A genuine contribution to quantum engineering or software, evaluated beyond classroom usefulness. |
| IEEE Transactions on Software Engineering | Stretch target for a distinct mature research contribution | New generalizable testing, diagnosis or verification method with realistic benchmark evidence. |

These venue judgments follow official scope statements [25–28]. They are not predictions of acceptance, rankings or impact-factor claims. Match the completed contribution to the journal. Do not force one manuscript to carry education, an AI benchmark, a new verifier, cybersecurity migration and national workforce policy simultaneously.

An example of a relevant accepted Transactions paper is **A Computer Science-Oriented Approach to Introduce Quantum Computing to a New Audience**, by Özlem Salehi, Zeki Seskir and İlknur Tepe, DOI 10.1109/TE.2021.3078552 [1]. Its existence supports the venue's interest in accessible quantum education while also showing why accessibility alone is no longer a sufficient novelty claim.

For the proposed ToE manuscript, use this argument: existing instruction can teach circuit construction, yet students also need to know when their observations justify a software claim; the intervention explicitly teaches that reasoning; the study tests independent transfer using a controlled design. State the mechanism, scope and competing explanation clearly.

Suggested manuscript structure: problem and educational research question; closest related work and gap; intervention and comparison; measurement development; two-site methods; learning results; technical feasibility and reproducibility; threats and adoption implications. The current ToE page specifies structured abstracts and initial lengths up to eight pages for Discovery and Application [25]. Keep detailed tasks, code and analytic derivations in permitted supplementary artifacts.

Provisional abstract concept: “Quantum programming instruction increasingly gives computing students access to executable circuits, but correct execution and plausible output do not establish that a program satisfies its intended specification. We propose an instructional approach that makes the relationship among claims, measurement choices and uncertainty explicit. A local simulation pilot demonstrates tasks in which computational-basis observations cannot reveal a relative-phase defect and tasks in which limited evidence warrants an inconclusive decision. A planned two-university controlled study will evaluate delayed transfer, unnecessary repair and confidence calibration against matched instruction. The resulting contribution will depend on measured educational outcomes and the validity of the assessment.” This is a proposal abstract; it must be replaced with actual methods and findings before submission.

## 12 NSF pathway and preliminary evidence

The most direct first funding fit is **IUSE EDU Engaged Student Learning Level 1**. The current NSF 23-510 solicitation supports early-stage studies and cross-institution partnerships, with a maximum of $400,000 over three years. The next listed deadline is **20 January 2027**, at 5 p.m. the submitting organization's local time [29]. A two-university collaboration does not automatically require a higher funding level.

A second route is **Computing Education Research under Future CoRe**, NSF 25-543, if the principal contribution concerns how students learn probabilistic computing and transfer verification reasoning. The current solicitation accepts proposals at any time and lists target review dates; the program page lists **4 February 2027** and **9 September 2027** as upcoming targets. Awards can be up to $1 million over four years, with scope-appropriate smaller projects encouraged [31, 32]. CER is a better initial discussion than selecting FET merely because the topic includes quantum.

For a later project whose central innovation is a new verification method, **Software and Hardware Foundations** within Future CoRe is a more natural technical route [31, 33]. Project Triad provides strategic context about integrated quantum systems and workforce needs. Its initiative page does not itself establish an open small education solicitation or automatic eligibility for this project [30].

Proposed IUSE concept: **Learning to Verify Probabilistic Quantum Software Across Computing Disciplines**. Aim 1 develops and validates the competency framework and tasks. Aim 2 tests the learning mechanism at two universities. Aim 3 studies adoption, accessibility and transfer to additional computing contexts. The intellectual contribution is knowledge about evidence-based reasoning in probabilistic software. Broader impacts are reusable materials and accessible pathways for computing students who lack a prior physics background.

A practical preliminary package includes the executed pilot and its limitations; a reviewed literature gap; a usable lesson; cognitive-interview findings; initial task reliability and timing; reproducibility at the partner university; and a realistic recruitment and analysis plan. A submitted or accepted paper can strengthen this evidence, but IUSE Level 1 explicitly allows well-grounded proposals without pilot data [29]. Do not delay a suitable proposal solely to obtain a journal acceptance.

The January 2027 deadline is a short runway from September 2026. It is realistic only for an early-stage proposal with clearly labeled technical and feasibility evidence, appropriate institutional preparation and a credible team. It is not realistic to promise a completed, reviewed two-university study and accepted Transactions article by that deadline. If the priority is a stronger preliminary paper, run the main study in spring 2027 and discuss a later funding cycle with the program officer.

Budget categories should follow real effort: faculty research time, undergraduate assistants, educational measurement or evaluation expertise, participant support where appropriate, dissemination and sustainable maintenance. A predominantly local-simulation project does not need a large quantum hardware budget. Before routing, verify the active solicitation, personnel submission limits, institutional eligibility and the applicability of any collaborator's international status. The partner's identity and location have not been assumed here.

## 13 Collaboration and execution plan

| Period | Deliverable and decision |
|---|---|
| Next two weeks | Agree on the research question, actual partner courses, faculty roles, quantum expertise and accessible mathematics bridge. Reproduce the supplied pilot at both sites. |
| October to November 2026 | Complete the structured literature comparison, expert task review and institutional research determination. Conduct approved cognitive interviews. |
| November to December 2026 | Run the feasibility pilot if approvals and scheduling permit. Refine the assessment, power analysis and recruitment plan. Decide whether January IUSE readiness is sufficient. |
| Spring 2027 | Run the preregistered controlled study and delayed assessment. Keep technical benchmark development separate from confirmatory outcome decisions. |
| Summer 2027 | Analyze findings, prepare the Transactions manuscript and release permitted materials. Null findings should remain reportable. |
| After initial evidence | Extend to more institutions, advanced circuit families or an independently scoped AI-assisted condition; discuss CER or SHF funding fit. |

Dr AlSobeh can lead the IS/IT learning context, requirements-to-evidence tasks, applied computing integration and institutional coordination. The partner can lead a complementary course population, quantum content review or software verification expertise, depending on their actual background. Both should share instrument design, randomization decisions, blinded scoring and interpretation. If neither has substantial quantum verification expertise, obtain a qualified domain reviewer. Educational measurement expertise is also valuable; do not assume subject expertise substitutes for it.

The immediate go/no-go conditions are concrete: the partner can reproduce the artifact; both institutions can recruit an appropriate cohort; the tasks measure the intended competency; and the literature comparison supports the specific gap. If any condition fails, narrow or revise the study before expanding the platform. The first publication should make one claim exceptionally well and leave the larger research program room to grow.

## References and source notes

[1] Ö. Salehi, Z. Seskir and İ. Tepe. A Computer Science-Oriented Approach to Introduce Quantum Computing to a New Audience. IEEE Transactions on Education. DOI 10.1109/TE.2021.3078552. Author manuscript records acceptance; early access 2021, volume 65 in 2022. https://arxiv.org/abs/2010.13552

[2] J. Beaumont and K. Wakevainen. Scalable Autograding for Quantum Programming Assignments. ITiCSE 2024. DOI 10.1145/3649217.3653619. Publisher abstract and conference program reviewed; full publisher text was not accessible. https://doi.org/10.1145/3649217.3653619

[3] A. Miranskyy. A Course on the Introduction to Quantum Software Engineering Experience Report. arXiv:2602.07589, v2, 27 April 2026. Full HTML reviewed; treated here as an author manuscript, without assuming journal publication. https://arxiv.org/html/2602.07589v2

[4] Testing and Debugging Quantum Programs The Road to 2030. ACM Transactions on Software Engineering and Methodology, 2025. DOI 10.1145/3715106. Publisher-indexed record reviewed. https://doi.org/10.1145/3715106

[5] J. Zappin, T. Stalnaker, O. Chaparro and D. Poshyvanyk. Challenges and Practices in Quantum Software Testing and Debugging Insights from Practitioners. Author manuscript, 2026 TOSEM version; earlier preprint arXiv:2506.17306. Author publication page identifies TOSEM acceptance. https://ojcchar.github.io/files/42-tosem25-quantum-test-debug.pdf

[6] T. Li, Z. Zhao and J. Yin. Adaptive Fidelity Estimation for Quantum Programs with Graph-Guided Noise Awareness. AAAI 40(1), 695–703, 14 March 2026. DOI 10.1609/aaai.v40i1.37035. Official proceedings abstract reviewed. https://ojs.aaai.org/index.php/AAAI/article/view/37035

[7] S. Pallister, N. Linden and A. Montanaro. Optimal Verification of Entangled States with Local Measurements. Physical Review Letters 120, 170502, 2018. DOI 10.1103/PhysRevLett.120.170502. https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.120.170502

[8] Bugs4Q A benchmark of existing bugs to enable controlled testing and debugging studies for quantum programs. Journal of Systems and Software, 2023. Publisher record and repository reviewed. https://www.sciencedirect.com/science/article/pii/S0164121223002005 ; https://github.com/Z-928/Bugs4Q-Framework

[9] On the Reproducibility of Quantum Software Defect Datasets A Case Study of Bugs4Q. arXiv:2606.27124, June 2026. Indexed primary abstract and author institutional record reviewed; full text not retrieved. https://arxiv.org/abs/2606.27124

[10] A. B. B. Pham, H. T. Nguyen and M. Usman. QBugLM An Agentic Benchmarking Framework for LLM-based Quantum Software Debugging. arXiv:2606.07314; author page confirms QSW 2026 acceptance. Detailed performance claims are not used here. https://arxiv.org/abs/2606.07314 ; https://hoaio.com/research/

[11] Benchmarking Large Language Models on Repairing Qiskit Programs using Bugs4Q. arXiv:2607.09007, July 2026. Indexed primary abstract reviewed; treated as a preprint. https://arxiv.org/abs/2607.09007

[12] J. C. Meyer et al. Measuring student understanding in quantum computing Development and validation of the Quantum Computing Conceptual Survey. arXiv:2608.14459, August 2026. Indexed primary abstract reviewed; treated as a preprint. https://arxiv.org/abs/2608.14459

[13] J. C. Meyer, S. Goorney, T. Kushimo and Z. C. Seskir. Resource Letter QIE-1 Research in quantum information education. arXiv:2606.06445, June 2026. Indexed primary abstract reviewed; treated as a preprint. https://arxiv.org/abs/2606.06445

[14] PhysPort. Quantum Computing Conceptual Survey and Adaptable Curricular Exercises for QIS. Current pages reviewed; contact developers about term-specific access and instrument version. https://www.physport.org/assessments/assessment.cfm?A=QCCS ; https://www.physport.org/curricula/ACEQIS/

[15] J. C. Meyer, G. Passante, S. J. Pollock and B. R. Wilcox. Introductory quantum information science coursework at US institutions content coverage. EPJ Quantum Technology 11, 16, 2024. DOI 10.1140/epjqt/s40507-024-00226-0. Full article reviewed. https://link.springer.com/article/10.1140/epjqt/s40507-024-00226-0

[16] IBM. Classroom modules and Create a Classroom Account. Official learning and access documentation. https://quantum.cloud.ibm.com/learning/en/modules/computer-science ; https://quantum.cloud.ibm.com/docs/en/guides/classroom-accounts

[17] IBM. Exact simulation with Qiskit SDK primitives and StatevectorSampler documentation. https://quantum.cloud.ibm.com/docs/en/guides/simulate-with-qiskit-sdk-primitives ; https://quantum.cloud.ibm.com/docs/en/api/qiskit/qiskit.primitives.StatevectorSampler

[18] Microsoft. Quantum Development Kit overview and Katas in QDK Learning. https://learn.microsoft.com/en-us/azure/quantum/qdk-main-overview ; https://learn.microsoft.com/en-us/azure/quantum/katas-qdk-learning

[19] C. Gidney. Quirk browser quantum circuit simulator and source repository. https://algassert.com/quirk ; https://github.com/Strilanc/Quirk

[20] QWorld. QBronze educational resources. https://qworld.net/workshop-bronze/

[21] IBM Quantum Learning. Current course catalog including error correction and integration with high-performance computing. https://quantum.cloud.ibm.com/learning/en/courses

[22] NIST. Post-Quantum Cryptography Standardization. FIPS 203, 204 and 205. https://csrc.nist.gov/Projects/Post-Quantum-Cryptography/Post_Quantum_Cryptography-Standardization

[23] NIST NCCoE. Migration to Post-Quantum Cryptography guidance and frequently asked questions. https://pages.nist.gov/nccoe-migration-post-quantum-cryptography/

[24] PennyLane. Codebook. https://pennylane.ai/codebook/

[25] IEEE Education Society. Transactions on Education Author Resources. Current evidence requirements, article format and publication options. https://ieee-edusociety.org/publication/toe/toe-author-resources

[26] IEEE Education Society. Transactions on Learning Technologies scope. https://ieee-edusociety.org/publication/about-publications/tlt

[27] IEEE Transactions on Quantum Engineering. Subject areas and article types. https://tqe.ieee.org/subject-areas/

[28] IEEE Computer Society. Transactions on Software Engineering call and scope. https://www.computer.org/digital-library/journals/ts/cfp-ieee-transactions-on-software-engineering

[29] NSF. IUSE EDU, NSF 23-510, and current program page. Solicitation and listed January 2027 date reviewed. https://www.nsf.gov/funding/opportunities/iuse-edu-improving-undergraduate-stem-education-directorate-stem/nsf23-510/solicitation ; https://www.nsf.gov/funding/opportunities/iuse-edu-improving-undergraduate-stem-education-directorate-stem

[30] NSF. Project Triad initiative. Strategic context, not a standalone small education solicitation. https://www.nsf.gov/funding/initiatives/project-triad

[31] NSF. Future Computing Research, NSF 25-543, and current program page. https://www.nsf.gov/funding/opportunities/future-core-computer-information-science-engineering-future-computing/nsf25-543/solicitation ; https://www.nsf.gov/funding/opportunities/future-core-computer-information-science-engineering-future-computing

[32] NSF. Computing Education Research. https://www.nsf.gov/funding/opportunities/computing-education-research

[33] NSF. Software and Hardware Foundations. https://www.nsf.gov/funding/opportunities/shf-software-hardware-foundations

[34] Y. Li, M. Shao, J. Zhao and Q. Wang. A Methodological Analysis of Empirical Studies in Quantum Software Testing. arXiv:2601.08367; publisher-indexed TOSEM DOI 10.1145/3819590, June 2026. Primary abstract reviewed. A useful methodological checklist for benchmark expansion. https://arxiv.org/abs/2601.08367

All web resources were checked or retrieved on 24 September 2026. No access to restricted assessment items or subscription-only full texts is implied. Recheck active funding and journal requirements when preparing a submission.
