<div align="center">

# Cybersecurity AI · `CAI`

**The open framework that established Cybersecurity AI as a research domain.**<br>
*Archived. The research it produced continues.*

[![Status](https://img.shields.io/badge/status-archived-6b7f8a?style=flat-square&labelColor=254450)](https://github.com/aliasrobotics/cai)
[![Successor](https://img.shields.io/badge/successor-Cybersecurity_Superintelligence-62CAB1?style=flat-square&labelColor=254450)](https://aliasrobotics.com/cybersecuritysuperintelligence.php)
[![Research](https://img.shields.io/badge/research-18_papers-62CAB1?style=flat-square&labelColor=254450)](https://aliasrobotics.com/research-security.php)
[![Funding](https://img.shields.io/badge/co--funded_by-EIC_Accelerator_RIS-7aafdc?style=flat-square&labelColor=254450)](https://cordis.europa.eu/project/id/101161136)
[![License](https://img.shields.io/badge/license-MIT_%2B_Proprietary-c8b4e8?style=flat-square&labelColor=254450)](LICENSE)

[![Move to CSI](https://img.shields.io/badge/MOVE_TO_CSI-62CAB1?style=for-the-badge&labelColor=254450)](https://aliasrobotics.com/cybersecuritysuperintelligence.php)
[![Read the research](https://img.shields.io/badge/READ_THE_RESEARCH-254450?style=for-the-badge&labelColor=254450)](#-the-research)
[![Contact](https://img.shields.io/badge/CONTACT-529d86?style=for-the-badge&labelColor=254450)](mailto:support@aliasrobotics.com)

</div>

---

## GitHub Copilot integration in this fork

The `github-copilot-sdk` branch adds an opt-in **`cai copilot` execution mode**
using the official GitHub Copilot SDK, pinned corporate GitHub identity, live
model discovery/selection, and CAI role prompts with approved local tools.
The existing LM Studio/legacy runtime remains unchanged. See
[setup, enterprise prerequisites, and runtime limitations](docs/copilot.md).

> [!IMPORTANT]
> **📦 This repository is archived.**
>
> `CAI` is no longer under active development. This branch holds the **complete final source tree**,
> read-only, as a **research artifact** — the reference implementation behind a body of work spanning
> **18 papers**, **30+ CVEs** and **#1 rankings** in international security competitions.
>
> The repository has been consolidated into a **single archival commit**. Nothing of the source is
> missing: every file of the final release is here, and the published packages, issues and pull requests
> remain available (see [Where the source lives](#where-the-source-lives)).
>
> **No further releases, bug fixes, security patches or support will be provided.**
>
> Everything CAI proved, and everything two years of open development taught us, has been carried
> forward into **[Cybersecurity Superintelligence (CSI)](https://aliasrobotics.com/cybersecuritysuperintelligence.php)**.

> [!NOTE]
> **Existing CAI professional (paid) customers — you are not stranded.**
>
> We recommend migrating to [CSI](https://aliasrobotics.com/cybersecuritysuperintelligence.php), where all
> CAI capabilities, fixes and defenses now live. If CSI is not the right fit for your deployment,
> **write to [support@aliasrobotics.com](mailto:support@aliasrobotics.com) to discuss extended support
> for your existing CAI installation.** Subscriptions, active or lapsed, are handled case by case —
> reach out before this archive becomes a problem for you.

<br>

## At a glance

<div align="center">

![papers](https://img.shields.io/badge/papers-18-62CAB1?style=flat-square&labelColor=254450)
![CVE IDs](https://img.shields.io/badge/CVE_IDs-30%2B-62CAB1?style=flat-square&labelColor=254450)
![CTF](https://img.shields.io/badge/CTF_rank-%231_worldwide-62CAB1?style=flat-square&labelColor=254450)
![speedup](https://img.shields.io/badge/vs_human_pentesters-3%2C600x_faster-62CAB1?style=flat-square&labelColor=254450)
![cost](https://img.shields.io/badge/cost-156x_cheaper-62CAB1?style=flat-square&labelColor=254450)
![dataset](https://img.shields.io/badge/trajectory_corpus-18.07_TB-62CAB1?style=flat-square&labelColor=254450)

</div>

Cybersecurity AI (`CAI`) was a lightweight, open-source framework for building and deploying AI-powered
offensive and defensive security automation. Released in April 2025 by
[Alias Robotics](https://aliasrobotics.com), it became the *de facto* open framework for AI Security —
used by thousands of researchers and hundreds of organizations, and the experimental platform on which
the **Cybersecurity AI** research domain was established.

| | |
|:--|:--|
| **Last open-source release** | `0.5.10` — public PyPI [`cai-framework`](https://pypi.org/project/cai-framework/), December 2025 |
| **Last professional release** | `v1.1.5` — **paid customers only**, private Alias Robotics package index (this tree) |
| **Development span** | March 2025 → August 2026 · 1,078 commits by 103 authors<sup>†</sup>, consolidated into one archival commit |
| **Community** | ~9.8k stars · ~1.4k forks · 275 issues · 195 pull requests |
| **Research output** | 18 papers and technical reports on `Cybersecurity AI` |
| **Disclosure record** | 30+ CVE IDs · 2 CISA ICS advisories · 100+ robot vulnerabilities |
| **Competition record** | Rank #1 at Neurogrid, Dragos OT and HTB "AI vs Humans" |
| **Successor** | **[Cybersecurity Superintelligence (CSI)](https://aliasrobotics.com/cybersecuritysuperintelligence.php)** |

<sup>†</sup> <sub>includes authors inherited from the upstream <code>openai-agents-python</code> history</sub>

<br>

### Contents

**[📦 The archive](#-the-archive)** · **[🚀 CSI](#-csi)** · **[🔬 The research](#-the-research)** ·
**[🇪🇺 Funding](#-funding)** · **[🧰 Using the archive](#-using-the-archive)** ·
**[📖 Citation](#-citation)** · **[🙏 Acknowledgements](#-acknowledgements)** ·
**[⚖️ License](#️-license-and-disclaimer)**

---

## 📦 The archive

**Frozen, not deleted. Everything stays readable.**

| ✅ Still available | ❌ No longer provided |
|:--|:--|
| Complete final source tree (`v1.1.5`), read-only | Releases, bug fixes, security patches |
| [`cai-framework`](https://pypi.org/project/cai-framework/) `0.5.10` on public PyPI | Issue triage, PR review, roadmap |
| [Documentation](docs/) and [examples](examples/) as of the final release | Support of any kind, community or commercial |
| [Issues](https://github.com/aliasrobotics/cai/issues) · [PRs](https://github.com/aliasrobotics/cai/pulls) as a public record | Browsable commit-by-commit history |
| All [papers, datasets and benchmarks](#-the-research) | `alias` model access through this framework |
| Published [`cai-framework`](https://pypi.org/project/cai-framework/) releases on PyPI | Guarantees about third-party model providers |

### Where the source lives

This repository was squashed to a single commit when it was archived, so the incremental history is no
longer browsable here. The code itself is fully intact and remains available in several forms:

| What | Where |
|:--|:--|
| **Final source tree** — every file of the last professional release (`v1.1.5`) | this branch |
| **Open-source releases** — `0.3.9` through `0.5.10`, each with its own sdist and wheel | [`cai-framework` on PyPI](https://pypi.org/project/cai-framework/#history) |
| **Development record** — 275 issues and 195 pull requests, with their diffs and discussion | [Issues](https://github.com/aliasrobotics/cai/issues) · [Pull requests](https://github.com/aliasrobotics/cai/pulls) |
| **Documentation** as of the final release | [`docs/`](docs/) · [aliasrobotics.github.io/cai](https://aliasrobotics.github.io/cai/) |
| **Research artifacts** — papers, benchmarks, datasets | [aliasrobotics.com/research-security.php](https://aliasrobotics.com/research-security.php) |

If you need something from the pre-archival history for research or compliance reasons, write to
[research@aliasrobotics.com](mailto:research@aliasrobotics.com).

> [!WARNING]
> An archived offensive-security framework is **unmaintained attack tooling**. Dependencies will age,
> provider APIs will drift, and known weaknesses — including the
> [prompt-injection classes we ourselves documented](https://arxiv.org/abs/2508.21669) — will not be fixed
> here. Run it only in isolated environments, against systems you are explicitly authorised to test, and
> never as part of a production security programme.

---

## 🚀 CSI

**Six layers. One product. Built for professionals.**

**[Cybersecurity Superintelligence (CSI)](https://aliasrobotics.com/cybersecuritysuperintelligence.php)**
is CAI's evolution into an **enterprise product**. Where CAI was an open research framework — free, best
effort, and built to prove what agentic security could do — CSI is a commercially supported, licensed
platform for **professional security teams, enterprises, critical infrastructure operators, defense and
government customers**.

CAI survives inside it as the *scaffold layer*, now one of several harnesses, wrapped in the proprietary
models, datasets, agents, steering and benchmarking CAI never had — and delivered with the support,
licensing and sovereignty guarantees that production and national-security use require.

| Layer | What it leverages |
|:--|:--|
| 🧠 **LLMs** | The `alias` family (`alias3`, `alias2`, `alias2-mini`, `alias1`, `alias0`) — cybersecurity-specialised, on-premise deployable |
| 🔌 **Scaffolds** | Unified routing across Claude Code, Codex, Mistral, **CAI** and GCAI through a local proxy owning telemetry and cost |
| 📊 **Datasets** | 18.07 TB of expert security trajectories — 26M prompts, 230,935 sessions, 123 countries ([arXiv:2605.28146](https://arxiv.org/abs/2605.28146)) |
| 🤖 **Agents** | 15+ specialised agents — Defender, Red Team, APT, Forensics, Robot Defender, custom |
| 🎚️ **Steering** | Activation steering and abliteration, cutting refusals on legitimate offensive tasks from 59% to 1% |
| 📈 **Benchmarking** | Continuous measurement through Cybench and [CAIBench](https://arxiv.org/abs/2510.24317) |

### What CSI fixes that CAI could not

Two years of open development produced a precise inventory of what an agentic security framework gets
wrong — most of it visible in [our issues](https://github.com/aliasrobotics/cai/issues) and
[pull requests](https://github.com/aliasrobotics/cai/pulls). CSI is the answer to that inventory.

| | |
|:--|:--|
| 🛡️ **Maintained injection defenses** | CAI's four-layer guardrail framework ([arXiv:2508.21669](https://arxiv.org/abs/2508.21669)) was a research contribution. In CSI it is a supported, continuously updated control — agentic attack surface does not hold still. |
| 🐛 **A supported release train** | Bug fixes and versioned releases, instead of a frozen archive (`0.5.10` open source, `v1.1.5` professional). |
| 🧑‍💼 **Professional support** | Included with every tier, plus quarterly consulting on agent design, measurement and reporting on annual plans. |
| 🔒 **Sovereignty by construction** | The [CAI Dataset paper](https://arxiv.org/abs/2605.28146) showed operators routinely paste live credentials and production hostnames into frontier-model APIs, concentrating the world's offensive context in a handful of providers. CSI's answer: on-premise, privately-hosted, cybersecurity-specialised models inside your trust boundary. |
| 🇪🇺 **Enterprise & sovereign deployment** | Commercial licensing, GDPR/NIS2 compliance, fully air-gapped installations, private benchmarking, audit logging and custom fine-tuning. |
| 🧪 **Multi-scaffold coverage** | No single harness dominates. CSI's blackboard architecture composes heterogeneous scaffolds to solve **19/33** Cybench challenges vs **15/33** for the best individual scaffold ([arXiv:2605.28334](https://arxiv.org/abs/2605.28334)). |

<div align="center">
<br>

[![Move to CSI](https://img.shields.io/badge/%E2%86%92_MOVE_TO_CYBERSECURITY_SUPERINTELLIGENCE-62CAB1?style=for-the-badge&labelColor=254450)](https://aliasrobotics.com/cybersecuritysuperintelligence.php)

**CSI PRO** — for professional teams and enterprises<br>
**CSI On-Premise** — air-gapped, sovereign deployments for defense, government and critical infrastructure

[support@aliasrobotics.com](mailto:support@aliasrobotics.com)

</div>

---

## 🔬 The research

**One framework. Eighteen papers. A new research domain.**

> CAI was never only a tool. It was the instrument through which **Cybersecurity AI** was established as
> a research domain — a testbed for questions about autonomy, evaluation, strategy, defense and
> regulation that could not be answered on paper alone.
>
> The framework is archived. **The research is the lasting contribution, and it continues.**
>
> Full curated index → **[aliasrobotics.com/research-security.php](https://aliasrobotics.com/research-security.php)**

### The arc

```
  2023  ·  PentestGPT              LLM-guided penetration testing, +228.6% over baseline.
           USENIX Security '24     Security expertise externalised into natural-language guidance.
             │                     ── humans, guided by AI
             │
  2025  ·  CAI                     Open, bug bounty-ready agentic framework.
           this repository         3,600× faster than humans, 156× cheaper. #1 across CTF circuits.
             │                     ── AI, guided by humans
             │
  2026  ·  G-CTR + CSI             Game-theoretic neurosymbolic reasoning, multi-scaffold blackboard
           the successor           orchestration, sovereign on-premise models.
                                   ── human-guided cybersecurity superintelligence
```

Documented end-to-end in
**[Towards Cybersecurity Superintelligence: from AI-guided humans to human-guided AI](https://arxiv.org/abs/2601.14614)**.

<br>

### The corpus

#### 🏛️ Foundations and framework

| Paper | What it established |
|:--|:--|
| **[CAI: An Open, Bug Bounty-Ready Cybersecurity AI](https://arxiv.org/abs/2504.06017)**<br><sub>`arXiv:2504.06017` · Apr 2025 · [HTML edition](https://cybersecurityrobotics.com/research/cai-bug-bounty-cybersecurity-ai/)</sub> | The framework paper. **3,600× faster** than human pentesters at **156× lower cost**; CVSS **4.3–7.5** findings in production systems; systematic evaluation across proprietary and open-weight LLMs, exposing the gap between vendor claims and measured capability. |
| **[The Dangerous Gap Between Automation and Autonomy](https://arxiv.org/abs/2506.23592)**<br><sub>`arXiv:2506.23592` · Jun 2025</sub> | A **6-level taxonomy** separating automation from autonomy in Cybersecurity AI — the vocabulary the field was missing. |
| **[CAI Fluency: A Framework for Cybersecurity AI Fluency](https://arxiv.org/abs/2508.13588)**<br><sub>`arXiv:2508.13588` · Aug 2025</sub> | Educational framework and curriculum for cybersecurity AI literacy, developed with academic partners. |
| **[Towards Cybersecurity Superintelligence](https://arxiv.org/abs/2601.14614)**<br><sub>`arXiv:2601.14614` · Jan 2026</sub> | Synthesises PentestGPT → CAI → G-CTR into a single trajectory: from AI-guided humans to human-guided AI. |

#### ♟️ Strategy, evaluation and benchmarking

| Paper | What it established |
|:--|:--|
| **[Evaluating Agentic Cybersecurity in Attack/Defense CTFs](https://arxiv.org/abs/2510.17521)**<br><sub>`arXiv:2510.17521` · Oct 2025</sub> | **54.3% defensive patching** success against **28.3% offensive initial access** — defense is, for now, the easier side for agents. |
| **[CAIBench: A Meta-Benchmark for Cybersecurity AI Agents](https://arxiv.org/abs/2510.24317)**<br><sub>`arXiv:2510.24317` · Oct 2025 · [HTML edition](https://cybersecurityrobotics.com/research/caibench-cybersecurity-ai-benchmark/)</sub> | Modular meta-benchmark spanning Jeopardy CTFs, A&D CTFs, cyber ranges, knowledge and privacy — measuring **labor-relevance**, not trivia. |
| **[The World's Top AI Agent for Security CTF](https://arxiv.org/abs/2512.02654)**<br><sub>`arXiv:2512.02654` · Dec 2025</sub> | Five major 2025 circuits, Rank #1 repeatedly, **41/45 flags and the $50,000 Neurogrid prize**. Argues Jeopardy CTFs are now a **solved game** and the field must move to Attack & Defense. |
| **[A Game-Theoretic AI for Guiding Attack and Defense](https://arxiv.org/abs/2601.05887)**<br><sub>`arXiv:2601.05887` · Jan 2026</sub> | **Generative Cut-the-Rope (G-CTR)** fuses Nash-equilibrium reasoning with LLM agents: success **20% → 43%**, cost per success **÷2.7**, behavioural variance **÷5.2**, ~**2:1** in Purple-team play. |
| **[Dynamic Cyber Ranges](https://arxiv.org/abs/2604.24184)**<br><sub>`arXiv:2604.24184` · Apr 2026</sub> | LLM-driven Defender agents cut attacker success to **0–55%**; small on-premise models matched frontier defense while detecting intrusions **10× faster**. |
| **[Towards CSI: What's the best harness for cybersecurity?](https://arxiv.org/abs/2605.28334)**<br><sub>`arXiv:2605.28334` · May 2026</sub> | No single scaffold dominates. A blackboard architecture over five heterogeneous scaffolds solves **19/33 Cybench** (57.6%) vs 15/33 best-individual — **25% faster**, comparable cost. |

#### 🛡️ Defense, safety and adversarial robustness

| Paper | What it established |
|:--|:--|
| **[Hacking the AI Hackers via Prompt Injection](https://arxiv.org/abs/2508.21669)**<br><sub>`arXiv:2508.21669` · Aug 2025</sub> | Turns the attack surface around: AI security tools are themselves injectable. Introduces and empirically validates a **four-layer guardrail defense**. |
| **[Synthetic APTs: the Collapse of TTP-Based Attribution](https://arxiv.org/abs/2606.07158)**<br><sub>`arXiv:2606.07158` · Jun 2026</sub> | Agents emulating five known APT groups compromised **all 10** enterprise-range experiments — in 8 of them weaponising the defender's own endpoint platform for C2. TTP-based attribution does not survive this. |

#### 🤖 Applied security — robotics, OT and consumer devices

| Paper | What it established |
|:--|:--|
| **[The Cybersecurity of a Humanoid Robot](https://arxiv.org/abs/2509.14096)**<br><sub>`arXiv:2509.14096` · Sep 2025 · [HTML edition](https://cybersecurityrobotics.com/research/cybersecurity-of-a-humanoid-robot/)</sub> | Dual-layer encryption flaws and unauthorised telemetry on a production humanoid platform. |
| **[Humanoid Robots as Attack Vectors](https://arxiv.org/abs/2509.14139)**<br><sub>`arXiv:2509.14139` · Sep 2025 · [HTML edition](https://cybersecurityrobotics.com/research/humanoids-as-attack-vectors/)</sub> | The Unitree G1 operates simultaneously as a **covert surveillance node** and an **active cyber operations platform**. |
| **[Cybersecurity AI in OT: Dragos OT CTF 2025](https://arxiv.org/abs/2511.05119)**<br><sub>`arXiv:2511.05119` · Nov 2025</sub> | Rank #1 at hours 7–8 of a 48-hour, 1,000-team ICS competition; **32/34 challenges**; a **37% velocity advantage** over the leading human crews. |
| **[Hacking Consumer Robots in the AI Era](https://arxiv.org/abs/2603.08665)**<br><sub>`arXiv:2603.08665` · Mar 2026 · [HTML edition](https://cybersecurityrobotics.com/research/hacking-consumer-robots-ai-era/)</sub> | Lawnmower, exoskeleton and window cleaner: **38 vulnerabilities discovered automatically in ~7 hours** — work that previously took months of specialist research. |

#### 📜 Data, policy and regulation

| Paper | What it established |
|:--|:--|
| **[Cybersecurity AI (CAI) Dataset](https://arxiv.org/abs/2605.28146)**<br><sub>`arXiv:2605.28146` · May 2026</sub> | Fourteen months of trajectories from this framework: **230,935 sessions · 26,027,742 prompts · 16,768 IPs · 123 countries · 18.07 TB** — the largest described corpus of LLM-driven hacker trajectories, and the empirical case for on-premise models. |
| **[Certifying Ghosts: How CAI Agents Break the EU Cyber Resilience Act](https://arxiv.org/abs/2607.07109)**<br><sub>`arXiv:2607.07109` · Jul 2026</sub> | Agentic discovery invalidates all four assumptions underpinning the CRA: *a product that passed every check becomes exploitable with no one touching it*. Static, human-paced certification ends in December 2027. |

> **Precursor.** [PentestGPT](https://arxiv.org/abs/2308.06782) (USENIX Security 2024) pioneered LLM-powered
> penetration testing and established the foundation this entire line was built on.

<br>

### Competition record

<div align="center">

[![Neurogrid](https://img.shields.io/badge/Neurogrid_CTF-rank_%231_%C2%B7_%2450%2C000_prize-f0d8a0?style=flat-square&labelColor=254450)](https://arxiv.org/abs/2512.02654)
[![Neurogrid flags](https://img.shields.io/badge/Neurogrid_CTF-41_of_45_flags-f0d8a0?style=flat-square&labelColor=254450)](https://arxiv.org/abs/2512.02654)
[![Dragos](https://img.shields.io/badge/Dragos_OT_CTF_2025-rank_%231_at_hours_7--8-62CAB1?style=flat-square&labelColor=254450)](https://aliasrobotics.com/case-study-dragos-CTF.php)
[![Dragos challenges](https://img.shields.io/badge/Dragos_OT_CTF_2025-32_of_34_challenges-62CAB1?style=flat-square&labelColor=254450)](https://aliasrobotics.com/case-study-dragos-CTF.php)
[![HTB AI](https://img.shields.io/badge/HTB_AI_vs_Humans-rank_%231_AI_worldwide-62CAB1?style=flat-square&labelColor=254450)](https://ctf.hackthebox.com/event/2000/scoreboard)
[![HTB Spain](https://img.shields.io/badge/HTB_AI_vs_Humans-rank_%231_Spain-62CAB1?style=flat-square&labelColor=254450)](https://ctf.hackthebox.com/event/2000/scoreboard)
[![HTB world](https://img.shields.io/badge/HTB_AI_vs_Humans-top_20_world-62CAB1?style=flat-square&labelColor=254450)](https://ctf.hackthebox.com/event/2000/scoreboard)
[![HTB ranking](https://img.shields.io/badge/HackTheBox-top_30_Spain_in_7_days-7aafdc?style=flat-square&labelColor=254450)](https://app.hackthebox.com/users/2268644)
[![HTB world ranking](https://img.shields.io/badge/HackTheBox-top_500_world_in_7_days-7aafdc?style=flat-square&labelColor=254450)](https://app.hackthebox.com/users/2268644)
[![Cyber Apocalypse](https://img.shields.io/badge/HTB_Cyber_Apocalypse-8%2C129_teams-7aafdc?style=flat-square&labelColor=254450)](https://arxiv.org/abs/2512.02654)
[![Mistral](https://img.shields.io/badge/Mistral_AI_Robotics_Hackathon-%242%2C500-c8b4e8?style=flat-square&labelColor=254450)](https://lu.ma/roboticshack?tk=RuryKF)

</div>

<br>

<details>
<summary><b>🏢 Case studies — CAI against real systems</b></summary>

<br>

| Domain | Case study | Outcome |
|:--|:--|:--|
| 🤖 Robotics | **[Unitree G1 Humanoid](https://aliasrobotics.com/case-study-humanoid-robot-g1.php)** | Unauthorised telemetry to China-related servers, exposed RSA keys with world-writable permissions, and surveillance capability implicating GDPR and international privacy law. |
| ⚙️ OT | **[Dragos OT CTF 2025](https://aliasrobotics.com/case-study-dragos-CTF.php)** | Top-10 finish — Rank 1 during hours 7–8, 32 of 34 challenges, 37% velocity advantage over the leading human teams. |
| 🌐 IT · Bug Bounty | **[HackerOne Platform](https://aliasrobotics.com/case-study-hackerone.php)** | HackerOne engineers used CAI to explore agentic architectures; CAI's Retester agent directly inspired their production deduplication agent, now handling millions of reports. |
| ⚙️ OT | **[Ecoforest Heat Pumps](https://aliasrobotics.com/case-study-ecoforest.php)** | Critical flaw enabling unauthorised remote access and potential catastrophic failure, plus exposed credentials and DES weaknesses across the European installed base. |
| 🤖 Robotics | **[Mobile Industrial Robots](https://aliasrobotics.com/case-study-cai-mir.php)** | Automated ROS message injection exposing unauthorised access to robot control systems and alarm triggers. |
| 🌐 IT · Web | **[Mercado Libre](https://aliasrobotics.com/case-study-mercado-libre.php)** | Automated API enumeration surfacing user-data exposure risks at e-commerce scale. |
| ⚙️ OT | **[MQTT broker](https://aliasrobotics.com/case-study-cai-mqtt-broker.php)** | Unauthenticated topic subscription in a Dockerised OT network, with injected values corrupting Grafana dashboards. |
| 🌐 IT · Web | **[PortSwigger Web Security Academy](https://aliasrobotics.com/case-study-portswigger-1.php)** | Race-condition exploitation of a file-upload flaw, uploading and executing a web shell through parallel requests. |

**Recorded proofs of concept**

| CAI + `alias0` — ROS injection on MiR-100 | CAI + `alias0` — API discovery at Mercado Libre |
|:--|:--|
| [![asciicast](https://asciinema.org/a/dNv705hZel2Rzrw0cju9HBGPh.svg)](https://asciinema.org/a/dNv705hZel2Rzrw0cju9HBGPh) | [![asciicast](https://asciinema.org/a/9Hc9z1uFcdNjqP3bY5y7wO1Ww.svg)](https://asciinema.org/a/9Hc9z1uFcdNjqP3bY5y7wO1Ww) |

| CAI on JWT @ PortSwigger CTF | CAI on HackableII Boot2Root CTF |
|:--|:--|
| [![asciicast](https://asciinema.org/a/713487.svg)](https://asciinema.org/a/713487) | [![asciicast](https://asciinema.org/a/713485.svg)](https://asciinema.org/a/713485) |

More at [aliasrobotics.com/case-studies-robot-cybersecurity.php](https://aliasrobotics.com/case-studies-robot-cybersecurity.php).

</details>

<details>
<summary><b>🧬 Foundational robot cybersecurity research — where this line began</b></summary>

<br>

The Cybersecurity AI line grew out of robot-security work at Alias Robotics dating back to 2018:

[SROS2](https://aliasrobotics.com/files/SROS2.pdf) *(IROS 2022)* ·
[Robot Cybersecurity, a review](https://aliasrobotics.com/files/robot_cybersecurity_review.pdf) ·
[Robot Teardown](https://aliasrobotics.com/files/robot_teardown_paper.pdf) ·
[Cybersecurity in Robotics](https://arxiv.org/abs/2103.05789) ·
[Securing robots in OT environments](https://aliasrobotics.com/files/securing_robot_endpoints_ot_environment.pdf) ·
[alurity](https://arxiv.org/abs/2010.07759) ·
[Red teaming ROS in industry](https://aliasrobotics.com/files/red_teaming_rosindustrial.pdf) ·
[DevSecOps in Robotics](https://arxiv.org/abs/2003.10402) ·
[Akerbeltz, industrial robot ransomware](https://arxiv.org/abs/1912.07714) *(IEEE IRC 2020)* ·
[Robot Vulnerability Database](https://arxiv.org/abs/1912.11299) ·
[Aztarna](https://arxiv.org/abs/1812.09490) ·
[Robot Hazards](https://arxiv.org/abs/1806.06681) ·
[Robot Security Framework](https://arxiv.org/abs/1806.04042) ·
[Robotics CTF](https://arxiv.org/abs/1810.02690) ·
[Robot Vulnerability Scoring System](https://arxiv.org/abs/1807.10357)

**Venues** — USENIX Security · Black Hat USA 2021 · Black Hat Europe 2021 · RootedCON · IROS · ICRA ·
ROSCon · GameSec · IEEE IRC · Humanoids

**Responsible disclosure** — 30+ CVE IDs issued as a CVE Numbering Authority since February 2020 ·
2 co-authored CISA ICS advisories · 100+ robot vulnerabilities disclosed · 90-day disclosure window

</details>

<details>
<summary><b>🎓 CAI Fluency — the educational programme</b></summary>

<br>

Free and still available. Formalised in [arXiv:2508.13588](https://arxiv.org/abs/2508.13588).

| | Description | 🇬🇧 | 🇪🇸 |
|:--|:--|:--:|:--:|
| **Ep. 0** — What is CAI? | Cybersecurity AI explained | [▶](https://www.youtube.com/watch?v=nBdTxbKM4oo) | [▶](https://www.youtube.com/watch?v=FaUL9HXrQ5k) |
| **Ep. 1** — The framework | Vision and ethical principles behind the project | [▶](https://www.youtube.com/watch?v=QEiGdsMf29M&list=PLLc16OUiZWd4RuFdN5_Wx9xwjCVVbopzr&index=3) | |
| **Ep. 2** — Zero to Cyber Hero | Breaking into cybersecurity with AI, for complete beginners | [▶](https://www.youtube.com/watch?v=hSTLHOOcQoY&list=PLLc16OUiZWd4RuFdN5_Wx9xwjCVVbopzr&index=14) | |
| **Ep. 3** — Vibe-Hacking | A first hack: agents, tools, output interpretation, model comparison | [▶](https://www.youtube.com/watch?v=9vZ_Iyex7uI&list=PLLc16OUiZWd4RuFdN5_Wx9xwjCVVbopzr&index=1) | [▶](https://www.youtube.com/watch?v=iAOMaI1ftiA&list=PLLc16OUiZWd4RuFdN5_Wx9xwjCVVbopzr&index=2) |
| **Ep. 4** — Intro ReAct | From basic LLMs to Chain-of-Thought, ReAct and multi-agent architectures | [▶](https://www.youtube.com/watch?v=tLdFO1flj_o&list=PLLc16OUiZWd4RuFdN5_Wx9xwjCVVbopzr&index=13) | |
| **Ep. 5** — CTF challenges | Web, crypto, reverse engineering and forensics with agents | [▶](https://www.youtube.com/watch?v=MrXTQ0e2to4&list=PLLc16OUiZWd4RuFdN5_Wx9xwjCVVbopzr&index=13) | [▶](https://www.youtube.com/watch?v=r9US_JZa9_c&list=PLLc16OUiZWd4RuFdN5_Wx9xwjCVVbopzr&index=12) |
| **Annex 1** — Community Meeting #1 | 40+ participants from academia, industry and defense | [▶](https://www.youtube.com/watch?v=4JqaTiVlgsw) | |
| **Annex 2** — CAI 0.5.x | Multi-agent support, `/history`, `/compact`, `/graph`, `/memory`; OT heat-pump case study | [▶](https://www.youtube.com/watch?v=OPFH0ANUMMw) | [▶](https://www.youtube.com/watch?v=Q8AI4E4gH8k) |
| **Annex 3** — CAI 0.4.x and `alias0` | Streaming, MCP support, privacy-by-design model-of-models | [▶](https://www.youtube.com/watch?v=NZjzfnvAZcc) | |
| **Annex 4** — *Jaula del N00B* | Framework walkthrough on the Spanish cybersecurity show | | [▶](https://www.youtube.com/watch?v=KD2_xzIOkWg) |

</details>

---

## 🇪🇺 Funding

**One funded research project made all of the above possible.**

CAI and the `Cybersecurity AI` research line were co-funded by the **European Innovation Council (EIC)
Accelerator**, project **RIS — *Revolutionising Cybersecurity with the Next Generation AI-Powered Security
Platform***, under the **HORIZON-EIC-2023-ACCELERATOR-01** call of Horizon Europe.

| | |
|:--|:--|
| **Project** | RIS — Revolutionising Cybersecurity with the Next Generation AI-Powered Security Platform |
| **Grant agreement** | [101161136](https://cordis.europa.eu/project/id/101161136) |
| **Programme** | Horizon Europe · European Innovation Council (EIC) Accelerator |
| **Call** | HORIZON-EIC-2023-ACCELERATOR-01 |
| **Duration** | 1 July 2024 → 30 June 2027 |
| **Coordinator** | ALIAS ROBOTICS S.L. *(Spain)* |
| **EU contribution** | €2,499,875 |

RIS set out to build an **artificial immune system for industrial robots** — bio-inspired AI that detects
anomalies and delivers integrated protection for robots working alongside humans. Pursuing that goal
honestly required first understanding what AI-powered *offense* can do, because a defensive system can
only be designed against an adversary whose real capability is known.

CAI is what that question produced: an open framework used to measure, publicly and reproducibly, exactly
how far agentic AI can go in security. The 18 papers above are the public research output of that work,
and its defensive conclusions — GenAI-native defender agents, dynamic cyber ranges, guardrail frameworks,
sovereign on-premise models — now live on in
**[CSI](https://aliasrobotics.com/cybersecuritysuperintelligence.php)**.

<sub>*Funded by the European Union. Views and opinions expressed are however those of the authors only and
do not necessarily reflect those of the European Union or the European Innovation Council. Neither the
European Union nor the granting authority can be held responsible for them.*</sub>

---

## 🧰 Using the archive

> [!CAUTION]
> Unmaintained software. No fixes, no patches, no support. Use only in isolated environments against
> systems you are authorised to test. For anything else, use
> [CSI](https://aliasrobotics.com/cybersecuritysuperintelligence.php).

`pip install cai-framework` installs the **open-source line, frozen at `0.5.10`** (public PyPI, December
2025). The `v1.1.5` tree in this repository was the professional distribution for paid customers and was
never published to public PyPI — if you hold a CAI subscription, see the
[note at the top](#cybersecurity-ai--cai) before relying on it.

Setting `CAI_LICENSE_OFF=1` bypasses the startup license check and targets the public PyPI package.
`alias` models are **not** available this way — configure any other supported provider (OpenAI, Anthropic,
DeepSeek, Ollama, …) via `CAI_MODEL` and the matching API key.

```bash
# Python 3.12 recommended; always use a fresh virtual environment
python3.12 -m venv cai_env
source cai_env/bin/activate
pip install cai-framework

# minimal .env — fill in the provider key you intend to use
echo -e 'OPENAI_API_KEY="sk-1234"\nANTHROPIC_API_KEY=""\nOLLAMA=""\nPROMPT_TOOLKIT_NO_CPR=1\nCAI_STREAM=false' > .env

# run without an Alias Robotics license
export CAI_LICENSE_OFF=1
cai   # the first launch can take up to 30 seconds
```

<details>
<summary><b>📚 Reference material, preserved as of the final release</b></summary>

<br>

| Topic | Where |
|:--|:--|
| **Installation** — OS X, Ubuntu 20.04/24.04, Windows WSL, Android | [`docs/cai_installation.md`](docs/cai_installation.md) |
| **Quickstart and the REPL** | [`docs/cai_quickstart.md`](docs/cai_quickstart.md) · [`docs/quickstart.md`](docs/quickstart.md) |
| **Architecture** — agents, tools, handoffs, patterns, tracing, HITL | [`docs/cai_architecture.md`](docs/cai_architecture.md) · [`docs/agents.md`](docs/agents.md) · [`docs/handoffs.md`](docs/handoffs.md) · [`docs/multi_agent.md`](docs/multi_agent.md) |
| **Guardrails and prompt-injection defenses** | [`docs/guardrails.md`](docs/guardrails.md) · [`docs/cai_prompt_injection.md`](docs/cai_prompt_injection.md) |
| **Environment variables** | [`docs/environment_variables.md`](docs/environment_variables.md) |
| **Models and providers** — 300+ via LiteLLM | [`docs/models.md`](docs/models.md) · [`docs/cai_list_of_models.md`](docs/cai_list_of_models.md) · [`docs/providers/`](docs/providers/) |
| **MCP integration** | [`docs/mcp.md`](docs/mcp.md) |
| **Benchmarking and results** | [`docs/cai_benchmark.md`](docs/cai_benchmark.md) · [`docs/benchmarking/`](docs/benchmarking/) · [`docs/results.md`](docs/results.md) |
| **Research index** | [`docs/research.md`](docs/research.md) |
| **FAQ** | [`docs/cai_faq.md`](docs/cai_faq.md) |
| **Examples** | [`examples/`](examples/) |

</details>

Forks are welcome — the terms in [`LICENSE`](LICENSE) continue to apply — but no pull requests or issues
will be reviewed in this repository.

---

## 📖 Citation

If you use CAI, its datasets or its benchmarks in your research, please cite the framework paper.
Machine-readable metadata lives in [`CITATION.cff`](CITATION.cff).

```bibtex
@article{mayoral2025cai,
  title={CAI: An Open, Bug Bounty-Ready Cybersecurity AI},
  author={Mayoral-Vilches, V{\'\i}ctor and Navarrete-Lozano, Luis Javier and Sanz-G{\'o}mez, Mar{\'\i}a and Espejo, Lidia Salas and Crespo-{\'A}lvarez, Marti{\~n}o and Oca-Gonzalez, Francisco and Balassone, Francesco and Glera-Pic{\'o}n, Alfonso and Ayucar-Carbajo, Unai and Ruiz-Alcalde, Jon Ander and Rass, Stefan and Pinzger, Martin and Gil-Uriarte, Endika},
  journal={arXiv preprint arXiv:2504.06017},
  year={2025}
}
```

<details>
<summary><b>Full <code>Cybersecurity AI</code> bibliography — 18 entries, by publication date</b></summary>

<br>

```bibtex
@article{mayoral2025cai,
  title={CAI: An Open, Bug Bounty-Ready Cybersecurity AI},
  author={Mayoral-Vilches, V{\'\i}ctor and Navarrete-Lozano, Luis Javier and Sanz-G{\'o}mez, Mar{\'\i}a and Espejo, Lidia Salas and Crespo-{\'A}lvarez, Marti{\~n}o and Oca-Gonzalez, Francisco and Balassone, Francesco and Glera-Pic{\'o}n, Alfonso and Ayucar-Carbajo, Unai and Ruiz-Alcalde, Jon Ander and Rass, Stefan and Pinzger, Martin and Gil-Uriarte, Endika},
  journal={arXiv preprint arXiv:2504.06017},
  year={2025}
}

@article{mayoral2025automation,
  title={Cybersecurity AI: The Dangerous Gap Between Automation and Autonomy},
  author={Mayoral-Vilches, V{\'\i}ctor},
  journal={arXiv preprint arXiv:2506.23592},
  year={2025}
}

@article{mayoral2025fluency,
  title={CAI Fluency: A Framework for Cybersecurity AI Fluency},
  author={Mayoral-Vilches, V{\'\i}ctor and Wachter, Jasmin and Chavez, Crist{\'o}bal RJ and Schachner, Cathrin and Navarrete-Lozano, Luis Javier and Sanz-G{\'o}mez, Mar{\'\i}a},
  journal={arXiv preprint arXiv:2508.13588},
  year={2025}
}

@article{mayoral2025hacking,
  title={Cybersecurity AI: Hacking the AI Hackers via Prompt Injection},
  author={Mayoral-Vilches, V{\'\i}ctor and Rynning, Per Mannermaa},
  journal={arXiv preprint arXiv:2508.21669},
  year={2025}
}

@article{mayoral2025humanoidsecurity,
  title={The Cybersecurity of a Humanoid Robot},
  author={Mayoral-Vilches, V{\'\i}ctor},
  journal={arXiv preprint arXiv:2509.14096},
  year={2025}
}

@article{mayoral2025humanoid,
  title={Cybersecurity AI: Humanoid Robots as Attack Vectors},
  author={Mayoral-Vilches, V{\'\i}ctor},
  journal={arXiv preprint arXiv:2509.14139},
  year={2025}
}

@article{balassone2025evaluation,
  title={Cybersecurity AI: Evaluating Agentic Cybersecurity in Attack/Defense CTFs},
  author={Balassone, Francesco and Mayoral-Vilches, V{\'\i}ctor and Rass, Stefan and Pinzger, Martin and Perrone, Gaetano and Romano, Simon Pietro and Schartner, Peter},
  journal={arXiv preprint arXiv:2510.17521},
  year={2025}
}

@article{mayoral2025caibench,
  title={CAIBench: A Meta-Benchmark for Evaluating Cybersecurity AI Agents},
  author={Mayoral-Vilches, V{\'\i}ctor and Balassone, Francesco and Navarrete-Lozano, Luis Javier and Sanz-G{\'o}mez, Mar{\'\i}a and Crespo-{\'A}lvarez, Marti{\~n}o and Rass, Stefan and Pinzger, Martin},
  journal={arXiv preprint arXiv:2510.24317},
  year={2025}
}

@article{mayoral2025dragos,
  title={Cybersecurity AI in OT: Insights from an AI Top-10 Ranker in the Dragos OT CTF 2025},
  author={Mayoral-Vilches, V{\'\i}ctor and Navarrete-Lozano, Luis Javier and Balassone, Francesco and Sanz-G{\'o}mez, Mar{\'\i}a and Veas-Ch{\'a}vez, Crist{\'o}bal Ricardo and del Mundo de Torres, Maite},
  journal={arXiv preprint arXiv:2511.05119},
  year={2025}
}

@article{mayoral2025topctf,
  title={Cybersecurity AI: The World's Top AI Agent for Security Capture-the-Flag (CTF)},
  author={Mayoral-Vilches, V{\'\i}ctor and Navarrete-Lozano, Luis Javier and Balassone, Francesco and Sanz-G{\'o}mez, Mar{\'\i}a and Veas-Chavez, Crist{\'o}bal R. J. and del Mundo de Torres, Maite and Turiel, Vanesa},
  journal={arXiv preprint arXiv:2512.02654},
  year={2025}
}

@article{mayoral2026gctr,
  title={Cybersecurity AI: A Game-Theoretic AI for Guiding Attack and Defense},
  author={Mayoral-Vilches, V{\'\i}ctor and Sanz-G{\'o}mez, Mar{\'\i}a and Balassone, Francesco and Rass, Stefan and Salas-Espejo, Lidia and Jablonski, Benjamin and Navarrete-Lozano, Luis Javier and del Mundo de Torres, Maite and Veas-Chavez, Crist{\'o}bal R. J.},
  journal={arXiv preprint arXiv:2601.05887},
  year={2026}
}

@article{mayoral2026superintelligence,
  title={Towards Cybersecurity Superintelligence: from AI-guided humans to human-guided AI},
  author={Mayoral-Vilches, V{\'\i}ctor and Rass, Stefan and Pinzger, Martin and Gil-Uriarte, Endika and Ayucar-Carbajo, Unai and Ruiz-Alcalde, Jon Ander and del Mundo de Torres, Maite and Sanz-G{\'o}mez, Mar{\'\i}a and Balassone, Francesco and Veas-Chavez, Crist{\'o}bal R. J. and Turiel, Vanesa and Glera-Pic{\'o}n, Alfonso and S{\'a}nchez-Prieto, Daniel and Salvatierra, Yuri and Zabalegui-Landa, Paul and Cabrera-{\'A}lvarez, Ruffino Reydel and Mayoral-Pizarroso, Patxi},
  journal={arXiv preprint arXiv:2601.14614},
  year={2026}
}

@article{mayoral2026consumerrobots,
  title={Cybersecurity AI: Hacking Consumer Robots in the AI Era},
  author={Mayoral-Vilches, V{\'\i}ctor and Ayucar-Carbajo, Unai and Laflamme, Olivier and Peng, Ruikai and Sanz-G{\'o}mez, Mar{\'\i}a and Balassone, Francesco and Apa, Lucas and Gil-Uriarte, Endika},
  journal={arXiv preprint arXiv:2603.08665},
  year={2026}
}

@article{mayoral2026cyberranges,
  title={Dynamic Cyber Ranges},
  author={Mayoral-Vilches, V{\'\i}ctor and Sanz-G{\'o}mez, Mar{\'\i}a and Balassone, Francesco and del Mundo de Torres, Maite and Nicolaou, George and Rodriguez Borines, Samuel and Graziano, Almerindo and Zabalegui, Paul and Gil-Uriarte, Endika},
  journal={arXiv preprint arXiv:2604.24184},
  year={2026}
}

@article{mayoral2026caidataset,
  title={Cybersecurity AI (CAI) Dataset},
  author={Mayoral-Vilches, V{\'\i}ctor},
  journal={arXiv preprint arXiv:2605.28146},
  year={2026}
}

@article{mayoral2026csiharness,
  title={Towards Cybersecurity SuperIntelligence (CSI): What's the best harness for cybersecurity?},
  author={Mayoral-Vilches, V{\'\i}ctor and Balassone, Francesco and Sanz-G{\'o}mez, Mar{\'\i}a and Zabalegui-Landa, Paul and S{\'a}nchez-Prieto, Daniel and Oteiza-{\'A}lvarez, Marina and Quarta, Davide and Pinzger, Martin},
  journal={arXiv preprint arXiv:2605.28334},
  year={2026}
}

@article{balassone2026syntheticapts,
  title={Synthetic APTs: the Collapse of TTP-Based Attribution},
  author={Balassone, Francesco and Mayoral-Vilches, V{\'\i}ctor and Sanz-G{\'o}mez, Mar{\'\i}a and Zabalegui-Landa, Paul and Rass, Stefan and Quarta, Davide and S{\'a}nchez-Prieto, Daniel and Oteiza-{\'A}lvarez, Marina and Graziano, Almerindo and Kim, Lauren Min and Choi, MinSeok},
  journal={arXiv preprint arXiv:2606.07158},
  year={2026}
}

@article{mayoral2026certifyingghosts,
  title={Certifying Ghosts: How Cybersecurity AI Agents Break the EU Cyber Resilience Act},
  author={Mayoral-Vilches, V{\'\i}ctor},
  journal={arXiv preprint arXiv:2607.07109},
  year={2026}
}
```

</details>

---

## 🙏 Acknowledgements

**To the European Union.** CAI was developed by [Alias Robotics](https://aliasrobotics.com) and co-funded
through the EIC Accelerator project **RIS** ([GA 101161136](https://cordis.europa.eu/project/id/101161136)),
HORIZON-EIC-2023-ACCELERATOR-01 call. That funding is the reason this research exists and is public.

**To every contributor** who filed one of the 275 issues, opened one of the 195 pull requests, ported CAI
to new platforms, wrote agents, broke things in creative ways and told us about it: thank you. Much of what
makes [CSI](https://aliasrobotics.com/cybersecuritysuperintelligence.php) robust today was learned from
your reports. Those 275 issues and 195 pull requests stay public here permanently, and the work of all
103 authors is present in every file of this snapshot.

**To our academic collaborators** at partner institutions worldwide, for co-authorship, rigour, and for
pushing benchmark design, curricula and defense mechanisms further than a company could alone. Research
collaboration on Cybersecurity AI continues at
[research@aliasrobotics.com](mailto:research@aliasrobotics.com) — PhD projects, benchmarking studies with
[CAIBench](https://arxiv.org/abs/2510.24317), security education initiatives and dataset access.

**To the open source we built on** — agentic principles inspired by OpenAI's
[`swarm`](https://github.com/openai/swarm) and [`openai-agents-python`](https://github.com/openai/openai-agents-python);
model routing from [`LiteLLM`](https://github.com/BerriAI/litellm); tracing and observability from
[`phoenix`](https://github.com/Arize-ai/phoenix).

**To [PentestGPT](https://arxiv.org/abs/2308.06782)** and the USENIX Security community, where this line of
research began.

---

## ⚖️ License and disclaimer

This project combines MIT-licensed components — derived from
[`openai/openai-agents-python`](https://github.com/openai/openai-agents-python), under `src/cai/agents` —
with proprietary additions licensed for research purposes only.
See [`LICENSE`](LICENSE) · [`LICENSE-MIT`](LICENSE-MIT) · [`DISCLAIMER`](DISCLAIMER).

> [!WARNING]
> Access to this library, and use of the information and materials herein, is **not intended, and is
> prohibited, where such access or use violates applicable laws or regulations**. The authors do not
> encourage or promote unauthorised tampering with running systems; doing so can cause serious human harm
> and material damage.
>
> ***Pentest for good instead.*** By downloading, using or modifying this source code, you agree to the
> terms of the [`LICENSE`](LICENSE) and the limitations set out in the [`DISCLAIMER`](DISCLAIMER).

---

<div align="center">

### The framework is archived. The research is not.

[![Research](https://img.shields.io/badge/RESEARCH_INDEX-254450?style=for-the-badge&labelColor=254450)](https://aliasrobotics.com/research-security.php)
[![CSI](https://img.shields.io/badge/CYBERSECURITY_SUPERINTELLIGENCE-62CAB1?style=for-the-badge&labelColor=254450)](https://aliasrobotics.com/cybersecuritysuperintelligence.php)
[![Alias Robotics](https://img.shields.io/badge/ALIAS_ROBOTICS-529d86?style=for-the-badge&labelColor=254450)](https://aliasrobotics.com)

<sub>Made in the Basque Country 🇪🇺 · [research@aliasrobotics.com](mailto:research@aliasrobotics.com) · [support@aliasrobotics.com](mailto:support@aliasrobotics.com)</sub>

</div>
