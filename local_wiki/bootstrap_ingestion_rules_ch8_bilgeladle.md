---
artifact_id: bootstrap_ingestion_rules_ch8
agent: bilgeladle
skill: structural_extraction
source_bronze_uri: manuscript_draft_ch8
timestamp: 2026-06-30T13:44:39.666407
---

# INGESTION RULES: CAN YOU STILL OPEN THIS FILE

This document outlines the structural rules and definitions extracted from Chapter 8, detailing the transition from passive persistence to the architected kill-switches of the dependency model.

## 1. Structural Rules (XML Schema)

```xml
<ruleset name="CanYouStillOpenThisFile">
    <!-- Rule 1: The Dependency Model Inversion -->
    <rule id="dependency_model_inversion">
        <trigger>
            <event type="preservation_shift">
                <from>Passive Persistence (Autonomous, Zero-Energy)</from>
                <to>Dependency Model (Active Maintenance, High-Energy)</to>
            </event>
        </trigger>
        <consequence>
            <effect type="epistemic_fragility">
                <description>The survival of human memory is decoupled from its physical existence and tied directly to continuous institutional funding and server maintenance.</description>
            </effect>
            <effect type="first_sale_death">
                <description>The legal and technical ability to own, preserve, and transfer digital property is systematically eliminated.</description>
            </effect>
        </consequence>
    </rule>

    <!-- Rule 2: Defective by Design (The Kill-Switch) -->
    <rule id="defective_by_design">
        <trigger>
            <event type="technological_restriction">
                <mechanism>Digital Rights Management (DRM)</mechanism>
                <mechanism>Remote Server Handshake</mechanism>
            </event>
        </trigger>
        <consequence>
            <effect type="remote_revocation">
                <description>Corporate actors retain the power to brick local files, delete libraries, and track user engagement, preventing independent archiving.</description>
                <outcome>The creation of a 'Vaporized Present' where only algorithmically profitable facts are maintained.</outcome>
            </effect>
        </consequence>
    </rule>

    <!-- Rule 3: Optimization-Driven Liquidation -->
    <rule id="optimization_driven_liquidation">
        <trigger>
            <event type="cost_reduction">
                <target>technical_debt</target>
                <target>server_costs</target>
                <action>pull_the_plug</action>
            </event>
        </trigger>
        <consequence>
            <effect type="archival_erasure">
                <description>Legacy reports, investigative series, and historical data are deleted or made inaccessible, leaving broken URLs and empty search snippets.</description>
            </effect>
        </consequence>
    </rule>
</ruleset>
```

## 2. Extracted Glossary Terms

The following terms have been successfully ingested and updated in the system glossary:

*   **Passive Persistence**: The historical preservation model where physical records (such as clay tablets, vellum scrolls, or printed books) require zero active energy input or continuous maintenance to remain legible, autonomous, and verifiable over centuries.
*   **Active Maintenance**: The digital preservation requirement where a record's survival is contingent upon continuous energy input, software updates, hardware compatibility, and active institutional funding, rendering the record a 'performance' rather than an object.
*   **Vaporized Present**: An epistemic state where historical and contemporary facts are systematically erased or made inaccessible because they are no longer deemed profitable or algorithmically relevant to maintain, leaving only a highly curated, present-focused narrative.
*   **Defective by Design**: The deliberate engineering of technological restrictions (such as DRM or remote kill-switches) into digital media and information systems to prevent independent ownership, archiving, or verification.
*   **Optimization-Driven Liquidation**: The systematic deletion or decommissioning of digital archives, records, or platforms by corporate or institutional actors to reduce technical debt, server costs, and legal liabilities.
