# Theoretical Framework and Research Hypotheses

---

## 1. Research Question

The central question motivating this research is: *Do coordination mechanisms designed for scarcity break down under post-scarcity conditions, or do they find new purpose?*

More precisely: when the material conditions that coordination mechanisms were designed to solve largely disappear, do those mechanisms (1) collapse — becoming vestigial, abandoned, or irrelevant; (2) persist through institutional inertia — continuing to operate even though the underlying need has dissolved; or (3) repurpose — redirecting themselves to coordinate around the remaining scarce goods, specifically status, attention, meaning, and time?

The third outcome is the most theoretically productive and the least empirically studied. If market mechanisms migrate from coordinating material goods to coordinating status and meaning, the result is not the absence of economy but a structurally different economy operating on different scarcity constraints. This paper develops a falsifiable hypothesis set for each of the seven major coordination mechanisms and specifies the simulation requirements necessary to produce genuine surprises — outcomes that could overturn, not merely confirm, the prior analysis.

---

## 2. Key Definitions

### 2.1 Coordination Mechanisms

Coordination mechanisms are systems through which agents determine who receives what, who performs what tasks, and how collective action is organized. Under material scarcity, the dominant mechanisms are as follows:

| Mechanism | What it coordinates | Why scarcity makes it necessary |
|-----------|--------------------|---------------------------------|
| **Price/market signals** | Production and consumption | Price encodes relative scarcity, directing producers toward underserved goods and consumers toward conservation. |
| **Money** | Universal exchange, value storage, unit of account | Required only because goods are scarce enough to need rationing; enables deferred consumption and indirect exchange. |
| **Property rights** | Control over resources | Meaningful only when goods are scarce enough to generate rival claims; abundance of a good eliminates the enforcement rationale. |
| **Employment/contracts** | Labor allocation | Agents trade time for money because money purchases scarce goods; the bargain has no basis if goods are freely available. |
| **Taxation/redistribution** | Public goods provision, deficit support | Presupposes unequal access to scarce resources; enables transfer from surplus to deficit. |
| **Reputation/reciprocity** | Informal mutual aid | Coordination without formal systems: "I help you now, you help me later." Grounded in social rather than material exchange; potentially robust to material abundance. |
| **Queuing** | Access when demand exceeds supply | First-come-first-served allocation; disappears when supply meets or exceeds demand. |

For simulation purposes, each mechanism is operationalized as a behavioral pattern measurable by adoption rate, coordination efficiency, and stability across varying scarcity parameters.

### 2.2 How Scarcity Manifests

The material conditions these mechanisms evolved to solve include:

- **Rivalrous consumption**: One agent's use of a good reduces availability for others — the foundational economic problem.
- **Opportunity cost**: Choosing one option forecloses another, forcing prioritization across agents and time.
- **Labor scarcity**: Human time and attention are finite, generating specialization and exchange.
- **Uncertain future access**: Inability to guarantee future consumption motivates saving, investment, and insurance. The financial lifecycle (earn, save, retire) is structurally dependent on this uncertainty.
- **Competition driving innovation and conflict**: Scarcity simultaneously produces productive competition (build superior goods) and destructive competition (hoarding, exclusion, exploitation).
- **Compounding inequality**: Differential access to scarce resources accumulates over time; initial advantages become self-reinforcing.

### 2.3 Post-Scarcity Defined

Post-scarcity, as analyzed in this research, refers to the condition in which AI and automation drive the marginal cost of most material goods toward zero — making access to food, shelter, healthcare, education, energy, and information no longer a meaningful constraint for the majority of the population.

This definition does not imply abundance of everything. Several categories of goods remain inherently scarce even under material abundance:

- **Human attention**: Finite hours and cognitive limits are not altered by production automation.
- **Social status**: Relative by definition; zero-sum regardless of material conditions.
- **Unique experiences**: A specific conversation, a particular place at a particular time — non-replicable.
- **Physical location**: Desirable locations and proximity remain rivalrous.
- **Time**: Mortality is not a production problem.

Under post-scarcity, the binding constraint shifts from material to psychological and social. The hard coordination problem becomes the allocation of meaning, purpose, identity, and status — not food and shelter. This shift is precisely what distinguishes this research from adjacent work on automation and labor displacement, which typically assumes that material scarcity is redistributed rather than eliminated.

---

## 3. Causal Pathway and Research Scope

Post-scarcity without specifying its cause is underspecified as an analytical premise. The causal pathway determines which coordination mechanisms activate first, which institutions bear initial disruption pressure, and what the geographic and temporal distribution of the transition looks like. The following pathways are distinguishable:

| Causal Pathway | Leading Mechanism | Geographic Locus | Timeline |
|----------------|-------------------|------------------|----------|
| **AI/automation** | Labor displacement, production cost collapse | Advanced economies institutionally; individually accessible globally via compute access | Near-term (5–20 years) |
| Energy abundance | Production cost collapse via energy | Energy-importing nations benefit most | Medium-term |
| Nanotech/replicators | Material goods become near-free | Unpredictable | Long-term/speculative |
| Political/institutional | Managed distribution (UBI, commons) | Policy-dependent | Variable |

This research analyzes the AI-driven pathway exclusively. It is the most plausible near-term causal chain, offers the most concrete empirical grounding in current labor market data, and produces the most tractable simulation parameters. An important complication distinguishes the AI pathway from all prior technological transitions: AI capability does not follow industrial-era distribution patterns. It follows internet access, compute access, and individual initiative — not national infrastructure. Institutional adoption is geographically concentrated in advanced economies; individual capability is globally accessible given connectivity. This asymmetry must be reflected in simulation agent design.

### 3.1 Frame A and Frame B: Sequential Phases of a Single Phenomenon

Two analytical frames are distinguishable in the post-scarcity literature. These are not alternative research perspectives; they are sequential phases of the same process, where Frame A's output constitutes Frame B's enabling condition.

| Frame | Research Question | Premises | Temporal Position |
|-------|----------|----------|--------|
| **A: Human economy disrupted** | What happens to human coordination mechanisms when AI collapses material costs? | Humans are still primary economic actors; AI is the disruptive force | Near-term — measurably underway |
| **B: AI agent economy** | What happens when AI agents become autonomous economic actors? | Human coordination mechanisms have already transformed; AI agents operate autonomously | Follows from Frame A's completion |

The causal chain runs as follows: Frame A plays out — human coordination mechanisms collapse or repurpose, the employment bargain dissolves, production automates, material scarcity ends. These outcomes are precisely the conditions that enable Frame B. AI agents can only become autonomous economic actors in a world where human-labor-dependent structures have already unwound. Frame B does not replace Frame A; it inherits Frame A's landscape.

The present paper addresses Frame A in full. Frame B is treated in the Discussion as the next-order question that Frame A's conclusions directly raise — not a separate paper, not a footnote, but the explicit destination the analysis points toward.

---

## 4. Hypothesis Set and Mechanism Matrix

The following predictions are first-principles hypotheses, not conclusions. Each is falsifiable; the simulation must be designed so that it is capable of overturning them. A simulation that merely encodes its assumptions will confirm them. The value of the analysis lies precisely in the gap between what prior reasoning predicts and what the simulation produces.

### 4.1 Prior Analysis (Pre-Simulation)

| Mechanism | Collapse | Persist | Repurpose | Hypothesis Summary |
|-----------|:--------:|:-------:|:---------:|-----------------|
| Price/market signals | | | **H** | Prices migrate from material goods to remaining scarce goods (attention, status, location, access) |
| Money | **H** | | | Money's three functions (fungible exchange, store of value, unit of account) all depend on material scarcity; replacement tokens are structurally different tools |
| Property rights | | | **H** | Subject matter shifts from material goods to identity, data, location, and creative works |
| Employment/contracts | **H** | | | The compensatory bargain (time for money for scarce goods) has no basis; voluntary activity is structurally different from employment |
| Taxation/redistribution | **H** | | | Nothing material to redistribute when material resources are abundant; remaining scarce goods (status, attention) are not taxable |
| Reputation/reciprocity | | | **H** | Expands from supplementary informal mechanism to dominant coordination system for all remaining scarce goods |
| Queuing | **H** | | | Supply exceeds demand; apparent post-scarcity "queues" are status mechanisms in disguise |

*(H = hypothesis, subject to validation or falsification by simulation)*

The predicted pattern is four collapses and three repurposings, with no mechanism surviving on inertia alone. The empty "persist" column reflects the claim that coordination mechanisms are tools rather than habits: when the problem they solve disappears, they either find a new problem or they cease to function. This is precisely the kind of clean prediction that warrants skepticism — reality typically produces messier outcomes. The simulation must grant agents sufficient autonomy to produce "persist" outcomes if the empirical dynamics support them.

### 4.2 Falsification Criteria

| Mechanism | Hypothesis | Falsified if simulation shows... |
|-----------|-----------|----------------------------------|
| Price signals | Repurpose | Agents abandon pricing entirely, or pricing for non-material goods fails to stabilize |
| Money | Collapse | A single fungible token emerges as universal exchange medium post-scarcity |
| Property rights | Repurpose | Agents cease enforcing ownership claims even for non-material goods |
| Employment | Collapse | Stable compensatory employer-employee patterns form voluntarily under abundance |
| Taxation | Collapse | Agents self-organize redistributive collection mechanisms for non-material goods |
| Reputation | Repurpose | Reputation does not become dominant; some other mechanism coordinates remaining scarce goods |
| Queuing | Collapse | True first-come-first-served allocation persists for goods unrelated to status signaling |

---

## 5. Simulation Requirements for Fair Falsification

A simulation designed to produce fair tests of these hypotheses must satisfy five requirements:

**1. Agent autonomy over mechanism choice.** Agents must be able to adopt, abandon, modify, or invent coordination mechanisms — not follow scripted behavior. If agents can only select from a preset menu of outcomes (collapse, persist, or repurpose), the simulation is circular and cannot generate genuine findings.

**2. Parametric transition.** Post-scarcity does not arrive as a binary switch. The transition variables — speed (years versus decades), completeness (full versus partial abundance), and distribution (uniform versus geographically patchy) — must be tunable. Different parameter regimes may produce different verdicts for the same mechanism.

**3. Emergent behavior space.** The simulation must permit agents to produce coordination patterns not designed into the system. This is the mechanism by which genuine surprises are generated — a mechanism predicted to collapse may instead mutate into something outside the three-outcome framework. The three-category classification (collapse, persist, repurpose) may itself be insufficient; the simulation should be capable of revealing that.

**4. Path dependence.** The sequence and speed of mechanism changes matters. If money collapses before reputation scales up, a coordination vacuum may arise that produces temporary "persist" outcomes — not from inertia but from necessity during the transitional gap. This is an empirically distinct finding from the baseline prediction.

**5. Multiple runs with stochastic variation.** Single-run results are uninformative. Verdicts must be robust across varied initial conditions and random seeds. A hypothesis is treated as confirmed only if the outcome is consistent across the majority of runs under specified parameter conditions.

---

## 6. Measurement Framework

Three outcome categories are operationalized as follows.

### 6.1 Collapse: Irreversible Zero

**Definition:** A two-stage test.

1. *Sustained absence:* Mechanism adoption rate drops below 5% of agents and remains there for N consecutive cycles (N calibrated per mechanism based on baseline adoption rate under scarcity).
2. *Reversibility probe:* Scarcity conditions are temporarily reintroduced. If the mechanism recovers, it was dormant — a form of persist, not collapse. If it does not recover, collapse is confirmed: the mechanism has been forgotten, replaced, or structurally disassembled beyond recovery.

The reversibility probe is necessary because sustained absence alone cannot distinguish a dead mechanism from a dormant one. A mechanism that reactivates when scarcity returns was never genuinely abandoned; agents retained the behavioral pattern. That is persist, not collapse.

**Threshold calibration:** The 5% threshold and N-cycle duration must be set per mechanism relative to baseline adoption rates under scarcity. A mechanism with 90% baseline adoption falling to 5% is unambiguous. A mechanism with 15% baseline falling to 5% falls within noise margin.

**Scope:** This definition measures *whether* collapse occurred, not why, and not what replaced the mechanism. Functional replacement is retroanalysis — performed after collapse is confirmed by examining what coordination patterns filled the gap.

### 6.2 Persist: Per-Mechanism Idle Detection

**Definition:** Mechanism adoption remains above threshold, but the mechanism is no longer solving its coordination problem. Agents are executing the form without the function.

There is no universal persist metric. "Going through the motions" has a distinct empirical signature for each mechanism:

| Mechanism | Active signal (coordination is functioning) | Idle signal (persisting without function) |
|-----------|------------------------|------------------------------------------|
| **Price signals** | Prices converge, correlate with relative scarcity of some good, and alter agent behavior | Prices are set but random, non-convergent, or ignored — numbers without coordination effect |
| **Money** | Tokens are exchanged for goods/services, stored for future use, and their quantity affects agent options | Tokens are accumulated but never spent, or spent without changing receiver behavior — hoarding without function |
| **Property rights** | Ownership claims are enforced, violations have consequences, and ownership determines access | Claims are made but never contested, or contested but never enforced — ownership without exclusion |
| **Employment** | Agent output depends on the employment relationship; work would not occur without the compensation structure | Agents "work" but their activity is indistinguishable from what they would do without a contract — activity without dependency |
| **Taxation** | Collected resources are pooled and allocated to address a measurable deficit or fund a public good | Resources are collected into a pool that is not disbursed, or disbursed without targeting any deficit — collection without allocation |
| **Reputation** | Reputation scores predict and influence access to scarce goods; high-reputation agents receive measurably different outcomes | Scores are tracked but do not correlate with differential access — ranking without consequence |
| **Queuing** | Queue position determines access order; earlier arrival produces earlier access | Agents form lines but access order does not correlate with arrival order — lines without priority |

The cross-mechanism metric is coordination efficiency: does the mechanism reduce entropy in resource allocation compared to random assignment? If a mechanism's presence produces the same allocation pattern as its absence, it is persisting without function.

### 6.3 Repurpose: Behavioral Continuity with Information Structure Check

**Definition:** The mechanism's behavioral pattern (bidding, claiming, ranking, queuing) continues, but applied to goods in a different scarcity domain than its origin. The mechanism performs the same operation on different subject matter.

**Primary criterion — behavioral continuity:** If agents are still bidding, it remains pricing. If agents are still claiming exclusive control, it remains property rights. The behavioral pattern is the mechanism's identity.

**Required qualifier — information structure check:** Same behavior combined with the same information structure constitutes confirmed repurposing. Same behavior combined with a different information structure requires flagging as a potential novel mechanism.

This qualifier is most relevant for one specific case: trust-as-price. Agents may assign numerical values to trust and compare them — behavior identical to market pricing. In a simulation with AI agents, however, trust is objectively computable from behavioral track records. Under scarcity, prices exist because value is *not* objectively computable; price is a discovery mechanism for hidden information. If agents "price" something already objectively known, the behavioral pattern is identical but the informational function is inverted. That is not repurposed pricing; it is a new mechanism wearing pricing's behavioral form.

**Flagging protocol:** When behavioral continuity is detected, the information structure check asks:
1. Is the mechanism serving as a *discovery* process — revealing hidden information through agent interaction? If yes, the information structure is the same. Repurpose is confirmed.
2. Is the mechanism serving as a *labeling* process — assigning numbers to already-known quantities? If yes, the information structure differs. Flag as a potential novel mechanism; do not auto-classify as repurpose.

This distinction applies only to mechanisms involving numerical signaling (price, reputation scores). Mechanisms defined by physical or sequential patterns (queuing as arrival order, property as exclusion) do not exhibit this ambiguity.

---

## 7. Detailed Hypotheses and Reasoning

### 7.1 Price/Market Signals → Repurpose (H1)

**Scarcity function:** Price encodes relative scarcity, directing producers toward what to supply more of and consumers toward what to conserve.

**Post-scarcity fate:** Prices for material goods converge to zero — there is no scarcity signal to transmit. However, remaining scarce goods still require allocation: attention, social status, desirable locations, unique experiences, access to particular individuals or communities.

**Reasoning:** Empirical precursors to this repurposing are already observable. Real estate pricing in desirable locations, auction-based access to exclusive experiences, and advertising rate-setting (the attention economy's implicit pricing structure) all demonstrate that market mechanisms can operate on non-material goods without requiring material scarcity as a substrate. The mechanism is robust enough to coordinate any rivalrous good; its function is not inherently tied to material production.

**Testable claim (H1):** When material scarcity is removed from a simulation, agents will spontaneously develop pricing behaviors for remaining scarce goods — status markers, location access, attention — within N interaction cycles, not through design but through emergent coordination need.

### 7.2 Money → Collapse (H2)

**Scarcity function:** Universal exchange medium, store of value, and unit of account.

**Post-scarcity fate:** All three functions fail. The store-of-value function collapses when future consumption is guaranteed. The exchange medium weakens when most goods are freely available. The unit-of-account function loses meaning when most things carry no price.

**Reasoning:** The most prominent counter-argument holds that reputation tokens, cryptographic assets, or social credits become a new form of money. This conflates behavioral similarity with functional equivalence. Money's defining features are fungibility (any unit is interchangeable with any other), universal acceptance, and stable value storage across time. Post-scarcity coordination tokens — reputation scores, attention metrics, access rights — fail all three tests. They are domain-specific, non-fungible, and cannot be saved or lent at interest. They constitute new coordination tools, not money in a new form.

The Bitcoin counter-argument does not resolve this. Cryptocurrency's value derives from artificial supply caps within a context of material scarcity — people need to convert cryptocurrency to acquire material goods. Remove material scarcity and the demand side collapses. Artificial scarcity without a broader scarcity context produces a collectible, not money.

**Testable claim (H2):** In post-scarcity simulations, no single fungible token will emerge as a universal exchange medium. Agents will develop multiple domain-specific coordination tokens — one for status, one for attention, one for access — that cannot be meaningfully exchanged for each other. No functional money equivalent will emerge.

### 7.3 Property Rights → Repurpose (H3)

**Scarcity function:** Defines who controls what. Enforced because goods are rivalrous — one agent's use excludes another's.

**Post-scarcity fate:** Ownership claims over abundant material goods become vacuous; no agent asserts property rights over air. But locational scarcity persists — desirable places remain rivalrous — and new property domains emerge: personal data ownership, digital identity, unique creative works, and reputation (which is "owned" in the sense that only the agent who built it can destroy or leverage it).

**Reasoning:** The concept of exclusive control does not depend on material scarcity specifically — it depends on *any* scarcity, including social and informational scarcity. Property rights are abstract enough to migrate: from "I own this land" to "I own this identity, this creative work, this data about myself." The mechanism transfers; the subject matter changes.

**Testable claim (H3):** Agents in post-scarcity simulations will develop and enforce ownership claims over non-material goods — identity markers, creative outputs, location access — at rates comparable to material property right enforcement under scarcity conditions. The behavioral mechanism is conserved across domain shift.

### 7.4 Employment/Contracts → Collapse (H4)

**Scarcity function:** Coordinates labor allocation. The employment bargain: an agent gives their time and receives money that buys scarce goods.

**Post-scarcity fate:** Remove scarce goods and the bargain has no foundation. There is no reason to trade time for money when money cannot purchase anything not freely available.

**Reasoning:** Agents will continue to engage in productive activity under post-scarcity — creative work, community service, exploration, mentoring. But this is voluntarism, not employment. The defining features of employment are compulsion (survival requires income), compensation (time exchanged for money), and contract (enforceable obligations under conditions of need). All three features dissolve under material abundance. The activity persists; the coordination mechanism does not.

The "purpose employment" objection — that agents will create pseudo-jobs for structure and meaning — does not survive scrutiny. A voluntary role that can be abandoned at any time with no material consequence is a vocation or hobby. The employment mechanism is specifically constituted by the binding of labor to compensation under scarcity pressure; remove the pressure and the binding loses its force.

**Testable claim (H4):** Agents modeled with employment-seeking behavior will abandon it within N cycles of material abundance arriving. Agents with pre-existing non-work identity structures will adapt fastest. No stable employer-employee coordination pattern will emerge voluntarily under post-scarcity conditions.

### 7.5 Taxation/Redistribution → Collapse (H5)

**Scarcity function:** Enables transfer from surplus to deficit — funding public goods, supporting those without sufficient access to scarce resources.

**Post-scarcity fate:** Universal material access eliminates the deficit that redistribution targets. Zero-marginal-cost goods do not require public funding.

**Reasoning:** Taxation fundamentally requires two conditions: (1) an unequal distribution worth equalizing, and (2) a transferable resource to redistribute. Social status is relative and non-transferable — one cannot tax reputation and award it to another agent. Attention is zero-sum and non-fungible across agents. Locational value may remain taxable (a land value tax mechanism survives in narrow form), but this represents a residual case, not a functioning coordination system for the economy as a whole.

Governance structures persist under post-scarcity — collective decision-making, conflict resolution, and commons management remain necessary. The fiscal mechanism specifically — collecting and redistributing material resources — loses its object.

**Testable claim (H5):** In post-scarcity simulations, redistributive mechanisms will be abandoned as agents recognize there is nothing material to redistribute. Governance structures that persist will coordinate through reputation, consensus, and access management rather than resource collection and allocation.

### 7.6 Reputation/Reciprocity → Repurpose (H6)

**Scarcity function:** Informal mutual aid and coordination without formal systems, functioning on a supplementary basis alongside material exchange mechanisms.

**Post-scarcity fate:** The material basis for reciprocity vanishes, but reputation is fundamentally social rather than material. It predates markets, money, and property rights. Under post-scarcity, the mechanism does not merely survive — it undergoes a role transformation from supplementary to primary.

**Reasoning:** The persistence hypothesis (mere continuation at roughly current scale) would be incorrect. Reputation undergoes a qualitative shift: from one coordination mechanism among many, relevant mainly to informal settings, to the dominant system for allocating everything that remains scarce. When material differentiators disappear, social standing determines access to attention from interesting people, membership in selective communities, and participation in unique experiences. Reputation moves from side channel to main channel. Its adoption rate grows not because it is new but because competing mechanisms have collapsed.

**Testable claim (H6):** Reputation-based coordination will show the highest adoption rate of any mechanism in post-scarcity steady state. Its relative share of coordination activity will increase by an order of magnitude compared to the scarcity baseline, driven by the collapse of competing mechanisms rather than by any intrinsic change to reputation itself.

### 7.7 Queuing → Collapse (H7)

**Scarcity function:** First-come-first-served allocation when demand exceeds supply — the simplest and most mechanical coordination mechanism.

**Post-scarcity fate:** When supply meets or exceeds demand, there is nothing to queue for. The mechanism has no deeper social function to draw on when its material premise is removed.

**Reasoning:** The most persistent apparent counter-example is the waitlist: exclusive restaurants, selective communities, limited-enrollment programs. However, a waitlist for an exclusive experience is a status mechanism in queue form, not genuine queuing. The binding constraint is not supply — the restaurant could accommodate more patrons — but exclusivity as a deliberate feature. The "queue" functions as a reputation or status filter. True queuing (standing in line because supply is genuinely insufficient for all claimants) disappears when supply becomes adequate.

**Testable claim (H7):** First-come-first-served allocation will approach zero adoption in post-scarcity simulations. Any apparent queuing behavior that persists will correlate with status-signaling metrics, identifying it as a reputation mechanism rather than genuine supply-constrained queuing.

---

## 8. Literature Review

### 8.1 The Gap This Research Fills

Existing literature on post-scarcity falls into three categories that this research does not occupy:

1. **Prescriptive policy literature** — UBI, public ownership of automation, and universal basic dividend proposals (Korinek & Stiglitz, 2018; Varoufakis). These prescribe institutional responses without studying how coordination mechanisms evolve dynamically as scarcity parameters change.
2. **Philosophical and theoretical social theory** — post-capitalism and post-work social theory (Mason, 2015; Srnicek & Williams, 2015; Rifkin, 2014). Rich on why mechanisms might fail; lacks empirical or simulation methodology.
3. **Static agent-based models** — the ACE literature studies coordination emergence but within fixed scarcity assumptions. No published ABM study parametrically transitions from scarcity to abundance and measures mechanism fate.

The contribution of the present paper is an empirical simulation methodology applied to mechanism evolution across a parametric scarcity-to-abundance transition, using AI-driven abundance as the explicit causal pathway and the Frame A to Frame B sequence as the theoretical frame. No existing paper treats Frame A's outcomes as Frame B's enabling conditions.

| Gap in existing literature | This paper's contribution |
|---------------------------|--------------------------|
| Prescriptive post-work theory — no mechanism dynamics | Empirical simulation of mechanism evolution across scarcity-to-abundance transition |
| ABM in economics — static scarcity assumptions | Parametric scarcity coefficient that drops from 1.0 to 0.0 across simulation phases |
| Post-scarcity theory — no falsification criteria | Seven falsifiable hypotheses, each with explicit falsification condition and simulation measurement protocol |
| Frame A or Frame B treated as alternatives | Frame A to Frame B as sequential causal chain; Frame A output constitutes Frame B input condition |
| UBI experiments as post-work proxy | AI-driven abundance simulation as direct study of full scarcity collapse, not partial reduction |

---

### 8.2 Strand 1: Post-Work Social Theory

**Srnicek & Williams (2015)** — *Inventing the Future: Postcapitalism and a World Without Work.* The defining text of the post-work imaginary. Argues automation enables a post-scarcity economy via full automation, reduced working hours, and universal basic income. Key claim: for the majority of people, work offers no inherent meaning, fulfillment, or redemption. Limitation for the present research: the work is prescriptive (what should happen) rather than analytical (what mechanisms will actually do under transition pressure), and does not offer falsifiable predictions or simulation methodology (Srnicek & Williams, 2015).

**Rifkin (2014)** — *The Zero Marginal Cost Society.* Argues that the convergence of the Internet of Things, renewable energy, and distributed manufacturing will drive the marginal cost of most goods toward zero, undermining the logic of capitalist exchange. Directly relevant to the money-collapses hypothesis: if most things approach zero marginal cost, the exchange medium loses its function. Limitation: technology-optimistic framing underweights transitional coordination failures (Rifkin, 2014).

**Mason (2015)** — *PostCapitalism.* Argues that information goods — zero marginal cost, non-rivalrous — are already undermining the price mechanism, not as a future event but as an ongoing process. Relevant to hypothesis H1 (price signals repurpose): Mason's argument that price mechanisms cannot handle non-rivalrous goods is consistent with the hypothesis that pricing migrates toward remaining genuinely scarce goods (Mason, 2015).

**Jacobin (2018)** — "Why Post-Work Doesn't Work." Argues that post-work theorists make their case from a position of political weakness, proposing labor abolition when workers have no power to enact it. Methodologically, the political economy objection is orthogonal to the coordination mechanism question: whether post-work is achievable does not affect what happens to mechanisms when it arrives. This distinction is important for framing the present research's claims (Jacobin, 2018).

---

### 8.3 Strand 2: Automation and Labor Displacement

**Goldman Sachs Research (2023)** — Estimates 300 million jobs globally are exposed to automation. Effects are currently concentrated in entry-level positions; senior roles remain largely stable. Adjustment is occurring through task reallocation rather than mass displacement (Goldman Sachs, 2023).

**Yale Budget Lab (2024)** — Unemployment among 20-to-30-year-olds in highly AI-exposed occupations has increased approximately 3 percentage points since early 2024. This represents the first cohort-level displacement signal observed in the employment data (Yale Budget Lab, 2024).

**World Economic Forum Future of Jobs Report (2025)** — 85 million jobs displaced and 97 million new roles created by 2025; net positive globally, but 77% of new AI-adjacent roles require postgraduate credentials — a structural skills mismatch that the aggregate numbers obscure (WEF, 2025).

**GDPEval dataset, OpenAI (2024)** — 220 tasks across 44 occupations, benchmarking AI performance against real professional work. Provides empirical grounding for simulation Phase 1 baseline calibration: which occupations and task types are already AI-completable, and which still require human capability. Critical for parameterizing transition speed variables (OpenAI, 2024).

**Korinek & Stiglitz (2018)** — Automation technology concentrated in a small segment of ownership generates extreme inequality absent redistributive counterbalancing. Relevant to hypothesis H5 (taxation/redistribution collapses): if the redistributive mechanism is already underperforming before post-scarcity arrives, the transition accelerates its failure rather than causing it (Korinek & Stiglitz, 2018).

---

### 8.4 Strand 3: Universal Basic Income Experiments as Empirical Proxies

UBI experiments are not post-scarcity, but they constitute the closest available empirical analog — they partially decouple survival from employment and allow observation of coordination behavior under reduced material scarcity pressure.

**Finland UBI Experiment (2017–2018)** — 2,000 unemployed recipients received €560 per month unconditionally for two years. Results: marginal employment increase (~6 additional working days in year 2), with significant improvements in mental health, stress reduction, and social connectedness. Implication for simulation calibration: removing survival pressure does not collapse work-seeking behavior — it relaxes it. Agents with work as identity do not immediately abandon employment-seeking when material scarcity is reduced (WEF, 2019).

**Kenya GiveDirectly Experiment (2017–2029, ongoing)** — Long-term UBI across approximately 200 rural villages. Results show substantial economic expansion with labor shifting from wage employment toward self-employment rather than away from work entirely. Short-term transfers produced smaller economic impacts than long-term ones despite equivalent capital transfer. Implication for simulation: transition speed affects behavioral adaptation; long-run certainty changes behavior more than short-run income does (IPA, 2023; GiveDirectly, 2023).

**Synthesis:** Both experiments support the simulation hypothesis that fast versus slow transition produces qualitatively different behavioral outcomes. Agents adapt differently to a permanent post-scarcity landscape than to a temporary income supplement. This motivates the parameterization of transition speed as a primary independent variable.

---

### 8.5 Strand 4: Agent-Based Computational Economics

**Tesfatsion & Judd (2006)** — *Handbook of Computational Economics, Vol. 2.* The standard methodological reference for ACE. Key definition: "ACE studies economic processes as dynamic systems of interacting agents." The theoretical assumption of rational optimization is replaced by bounded rationality and adaptive behavior. The present simulation is ACE applied to a scenario — parametric scarcity reduction — that existing ACE models have not explored (Tesfatsion & Judd, 2006).

**Axelrod (1997)** — *The Complexity of Cooperation.* The foundational work on ABM of social norms and cooperation. Directly relevant to hypothesis H6 (reputation repurposes): Axelrod's tournaments demonstrated that cooperation emerges reliably when agents interact repeatedly, regardless of material incentives. Under post-scarcity, this suggests reputation mechanisms do not require material scarcity as a substrate — they are grounded in repeated interaction, which persists (Axelrod, 1997).

**Recent ACE literature (2023–2024)** — ABM has been applied to circular economy modeling, post-disaster recovery, and large-scale macroeconomic simulations involving millions of households across multiple regions. No published ABM study has parametrically modeled scarcity-to-abundance transitions. This constitutes the methodological gap the present paper addresses (Glasgow Eprints, 2024).

---

### 8.6 Strand 5: Post-Scarcity Economics (2024–2025)

A cluster of recent work is directly adjacent to this research but none provides simulation methodology or falsifiable hypotheses.

**"Designing Post-Scarcity Economic Systems in the Age of AI" (Preprints.org, 2025)** — Proposes a framework for post-scarcity economic design including reputation-governed competition for innovation and creative production. Key overlap: independently proposes reputation as the dominant post-scarcity coordination mechanism — consistent with hypothesis H6. The claim is not tested via simulation (Preprints.org, 2025a).

**"Post-Labor Economics: A Systematic Review" (Preprints.org, 2025)** — Systematic review of existing post-labor economic theory. Confirms that positional goods — status, attention, influence — remain contested resources requiring coordination even under material abundance. Validates the "inherently scarce goods" category in this simulation's environment model (Preprints.org, 2025b).

**"Scarcity in an Age of AI Abundance" (SSRN, 2025)** — Argues post-scarcity does not eliminate scarcity but reorganizes it: scarcity shifts from material goods to infrastructure, capabilities, institutions, and jurisdictions. Provides direct theoretical support for the repurpose hypothesis cluster in the mechanism matrix (SSRN, 2025).

**Shared methodological gap:** None of these papers employs agent-based simulation with parametric scarcity transitions. All remain theoretical. The present paper provides the empirical methodology.

---

## References

Axelrod, R. (1997). *The Complexity of Cooperation: Agent-Based Models of Competition and Collaboration.* Princeton University Press.

GiveDirectly. (2023). *2023 UBI Results.* https://www.givedirectly.org/2023-ubi-results/

Glasgow Eprints. (2024). *Agent-Based Modeling in Economics: Recent Applications.* https://eprints.gla.ac.uk/324487/1/324487.pdf

Goldman Sachs Research. (2023). *The Potentially Large Effects of Artificial Intelligence on Economic Growth.* https://www.goldmansachs.com/insights/articles/how-will-ai-affect-the-global-workforce

IPA (Innovations for Poverty Action). (2023). *Effects of Universal Basic Income: Kenya.* https://poverty-action.org/effects-universal-basic-income-kenya

Jacobin. (2018, November). *Why Post-Work Doesn't Work.* https://jacobin.com/2018/11/post-work-ubi-nick-srnicek-alex-williams

Korinek, A., & Stiglitz, J. E. (2018). *Artificial Intelligence and Its Implications for Income Distribution and Unemployment.* NBER Working Paper No. 24174. National Bureau of Economic Research.

Mason, P. (2015). *PostCapitalism: A Guide to Our Future.* Allen Lane.

OpenAI. (2024). *GDPEval Dataset.* HuggingFace. https://huggingface.co/datasets/openai/gdpval

Preprints.org. (2025a). *Designing Post-Scarcity Economic Systems in the Age of AI.* https://www.preprints.org/manuscript/202506.0414

Preprints.org. (2025b). *Post-Labor Economics: A Systematic Review.* https://www.preprints.org/frontend/manuscript/de8c22c65b97091cda8bc8c472705a5e/download_pub

Rifkin, J. (2014). *The Zero Marginal Cost Society: The Internet of Things, the Collaborative Commons, and the Eclipse of Capitalism.* Palgrave Macmillan.

Srnicek, N., & Williams, A. (2015). *Inventing the Future: Postcapitalism and a World Without Work.* Verso.

SSRN. (2025). *Scarcity in an Age of AI Abundance.* https://papers.ssrn.com/sol3/Delivery.cfm/5924462.pdf?abstractid=5924462&mirid=1

Tesfatsion, L., & Judd, K. L. (Eds.). (2006). *Handbook of Computational Economics, Vol. 2: Agent-Based Computational Economics.* Elsevier. https://www.sciencedirect.com/science/article/pii/S1574002105020162

WEF (World Economic Forum). (2019, February). *The Results of Finland's Universal Basic Income Experiment Are In: Is It Working?* https://www.weforum.org/stories/2019/02/the-results-finlands-universal-basic-income-experiment-are-in-is-it-working/

WEF (World Economic Forum). (2025). *Future of Jobs Report 2025.* World Economic Forum.

Yale Budget Lab. (2024). *Evaluating the Impact of AI on the Labor Market: Current State of Affairs.* https://budgetlab.yale.edu/research/evaluating-impact-ai-labor-market-current-state-affairs
