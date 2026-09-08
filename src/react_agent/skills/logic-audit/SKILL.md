---
name: logic-audit
description: Structural Logic Audit & Fallacy Scan. Audits causal claims, logical fallacies, and evidentiary validity to inform Sail Locker classification.
agents: [cutlass, grog, bilgeladle, pegleg]
---

# SKILL: Structural Logic Audit & Fallacy Scan

## Overview
This skill governs the structural audit of argument logic, causal claims, and evidentiary validity across incoming assets. It provides Cutlass and Grog with a rigorous framework for identifying logical fallacies, unsupported assertions, and structural paradoxes.

---

## Audit Framework

### 1. Causal Claim Verification
- **Explicit Claims**: Extract the core 'If X, then Y' assertions.
- **Evidentiary Base**: Verify if claims are backed by physical data, primary citations, or raw empirical observation.
- **Unsupported Assertions**: Flag assertions lacking data as `UNSUPPORTED`.

### 2. Classical Fallacy Scan
- **False Dilemma**: Forcing a choice between two extreme options while ignoring alternatives.
- **Strawman**: Distorting an opposing position to simplify critique.
- **Appeal to False Authority**: Citing credentialed actors outside their domain of expertise.
- **Texture Hacking**: Using dense formatting, press releases, or legalistic jargon to simulate rigor.
- **Self-Licking Loop**: Citing a media story that originally drew from the actor's own unverified leak.

### 3. Integration with Sail Locker
Logical validity feeds directly into Cutlass's Sail Locker decision:
- High logical validity + verifiable data $\rightarrow$ `MAINSAIL`
- Structurally invalid / deceitful / pastiche $\rightarrow$ `BILGE` (Valuable as evidence of logic failure)
- Unclear / unanchored premises $\rightarrow$ `DOLDRUMS`
