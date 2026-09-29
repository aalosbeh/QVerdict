# Proposed two university study

Status: protocol for refinement and preregistration, not completed research.

## Research question and estimand

Does explicit training in matching quantum claims to sufficient measurement
evidence improve performance on unseen verification tasks compared with equally
intensive quantum programming instruction with conventional feedback?

Primary estimand: assignment-to-intervention effect on a delayed, individual
transfer score at the participating sites, adjusted for the prespecified baseline.
The population is participating computing students, not all university students.

## Intervention and active control

Use six weekly sessions of approximately two hours plus a common prerequisite
bridge. Both conditions receive the same concepts, circuit families, exercise
time, staff access, simulator and source materials. Both learn measurement bases.
Both can run the same tests. The treatment requires claim, prediction, evidence,
uncertainty, decision and next action in each exercise, with graduated feedback.
The active control receives ordinary correctness feedback and worked explanations
of comparable length. The difference is the explicit evidence-reasoning scaffold.

Do not create an unfair comparison by withholding X measurements or statistical
information from the control. Usability benefits from extra instructor time must
not be mistaken for effects of the proposed scaffold.

## Participants and allocation

First conduct 8–12 cognitive interviews across both sites after the appropriate
institutional determination; use these only to refine materials and rubric.
A feasibility pilot of 20–40 students assesses completion, timing, attrition and
score distributions. It is not a powered confirmatory trial.

For the main study, plan around 160 total recruits to retain about 128 participants
under an illustrative 20% attrition assumption. An independent two-arm comparison
with d=0.50, two-sided alpha=0.05 and power=0.80 needs approximately 64 analyzable
students per arm. This calculation is illustrative, not evidence that the effect
will be 0.50. Use pilot variance, reliability, actual enrollment and randomization
structure for a final simulation-based power analysis before recruitment.

Randomize individuals within each university and course section, with blocks for
baseline readiness and, when feasible, major. Every site must contain both arms.
Do not assign one university to treatment and the other to control. If peers share
feedback extensively, randomize small lab groups and model groups, or recruit
enough sections for a cluster design. With group size 20 and ICC 0.05, the simple
design effect is 1.95; 128 individual-level observations would then require about
250 analyzable participants, before attrition. Two universities are not enough
clusters to justify a university-level randomized experiment.

## Outcomes and instruments

Primary outcome: delayed transfer score, 0–16, measured approximately four weeks
after instruction on four unseen tasks. Each task receives 0–4 points:

0: unsupported decision or no relevant reasoning.
1: relevant symptom or claim identified, but no discriminating evidence.
2: a relevant test is chosen, with incomplete interpretation.
3: test and inference are sound, but uncertainty or scope is incomplete.
4: evidence, decision, uncertainty and next action are all justified.

Include a hidden relative-phase error, harmless global phase, finite-shot boundary,
and a new input or qubit ordering case. Use isomorphic parallel forms for pretest,
posttest and delayed testing, with expert review and interview-based refinement.
Do not reuse the public Bell fixture in the confirmatory transfer assessment.

Secondary outcomes: immediate transfer; unnecessary repairs to correct programs;
test-selection quality; calibration of stated confidence against correctness;
reproduction success; time on task; and, where content aligns and permission is
obtained, the QCCS. The QCCS measures concepts, not software assurance, and should
not replace the primary task assessment. Confirm its current version and usage
conditions with its developers. Do not redistribute restricted items.

Two blinded raters independently score at least a substantial prespecified subset
(proposed 25%) and adjudicate after recording original scores. Report weighted
kappa or an appropriate ICC with uncertainty, rubric content coverage, item
difficulty and response-process evidence. A locally written rubric is not a
validated instrument simply because experts reviewed it. Treat major comparisons
as exploratory unless adequately powered and support measurement comparability.

## Analysis

Preregister the primary outcome, estimand, allocation, exclusions, missing-data
strategy and multiplicity plan before examining intervention effects. Use an
ANCOVA-style model with delayed score as outcome and assignment, baseline score,
site and section as prespecified predictors. Model or adjust for the actual
randomization units. With only two sites, treat site as a fixed contextual factor;
do not estimate a national institutional variance from two universities.

Report adjusted mean differences, standardized effects and confidence intervals.
Retain assigned groups in intention-to-treat analyses. Describe missingness by arm,
use a defensible imputation model if justified, and include sensitivity analyses
for departures from its assumptions. Label per-protocol analyses secondary.
Correct planned secondary comparisons or mark exploratory analyses clearly.

Repeated measurements, tasks and circuit variants from the same student are
not independent students. For task-level models include student dependence;
for benchmark uncertainty resample circuit families, not just shot repetitions.
The primary hypothesis can fail; report null or adverse findings honestly.

## AI extension

Keep live AI out of the first confirmatory contrast to isolate the scaffold.
In a later separately powered study, randomize scaffold on/off by AI assistance
on/off in a 2-by-2 design, or use a prespecified comparison of identical frozen AI
suggestions. Archive actual model outputs, prompts, model identifiers, generation
settings, dates and dependency versions. Instructor-authored examples must not
be relabeled as naturally occurring AI defects. Evaluate students without AI on
transfer tasks to distinguish temporary assisted performance from learning.

## Ethics and operational readiness

Obtain the institutions' human-subjects determination before collecting research
data. Use appropriate consent and equivalent instructional access; participation
or refusal must not affect grades. Store deidentified research identifiers separately
from grades and consent, and agree on cross-institution access and retention.
Do not send identifiable student work to a public model endpoint. Arrange a
permitted protocol, not retrospective consent after an experiment.

## Publication and continuation decisions

- Proceed to a Transactions on Education submission when the research question,
  measurement quality, comparison and uncertainty support a defensible conclusion.
- Consider Transactions on Learning Technologies when a novel feedback technology
  has a technical evaluation and demonstrated learning support.
- Treat a small uncontrolled pilot as preliminary grant evidence, not proof of efficacy.
- If enrollment is too low, expand cohorts or publish an explicitly exploratory
  study; do not inflate sample size by counting repeated tasks as people.
