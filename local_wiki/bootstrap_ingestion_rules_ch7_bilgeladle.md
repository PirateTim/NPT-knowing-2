---
artifact_id: bootstrap_ingestion_rules_ch7
agent: bilgeladle
skill: structural_extraction
source_bronze_uri: manuscript_draft_ch7
timestamp: 2026-06-30T13:43:46.105249
---

# INGESTION RULES: HISTORY IS SHRINKING

This document outlines the structural rules and definitions extracted from Chapter 7, detailing the transition from polite web protocols to predatory ingestion, digital decay, and the death of digital ownership.

## 1. Structural Rules (XML Schema)

```xml
<ruleset name="HistoryIsShrinking">
    <!-- Rule 1: The Ingestion Flip -->
    <rule id="ingestion_flip">
        <trigger>
            <event type="crawler_evolution">
                <from>Discovery Mechanism (Discovery for Access)</from>
                <to>Digestion Mechanism (Direct Answer Generation)</to>
            </event>
        </trigger>
        <consequence>
            <effect type="economic_loop_break">
                <description>AI models consume web content to answer user queries directly, starving the original content creators of traffic and revenue.</description>
            </effect>
            <effect type="protocol_collapse">
                <description>The polite 'robots.txt' handshake is bypassed or ignored by high-capital AI operators.</description>
            </effect>
        </consequence>
    </rule>

    <!-- Rule 2: Presentist Bias via SEO Arson -->
    <rule id="presentist_bias_seo">
        <trigger>
            <event type="content_liquidation">
                <operator>private_equity_or_publisher</operator>
                <cutoff_date>2014</cutoff_date>
                <justification>Crawl Budget Optimization</justification>
            </event>
        </trigger>
        <consequence>
            <effect type="historical_lobotomy">
                <description>The primary source records of the early, optimistic web are deleted, leaving only post-2014 polarized content.</description>
            </effect>
            <effect type="model_trauma">
                <description>AI models trained on this truncated dataset develop severe Presentist Bias, lacking any historical reference point for a world before systemic polarization.</description>
            </effect>
        </consequence>
    </rule>

    <!-- Rule 3: The Dependency Model and Revocable Access -->
    <rule id="dependency_model_licensing">
        <trigger>
            <event type="product_transition">
                <from>Physical/Digital Ownership</from>
                <to>Revocable Access License</to>
            </event>
            <event type="server_shutdown">
                <operator>corporate_owner</operator>
                <target>always_online_product</target>
            </event>
        </trigger>
        <consequence>
            <effect type="property_destruction">
                <description>The physical discs and digital downloads are rendered completely inert, proving that the consumer owns nothing.</description>
                <outcome>The transition of the digital library from a public utility to a landlord-controlled subscription window.</outcome>
            </effect>
        </consequence>
    </rule>
</ruleset>
```

## 2. Extracted Glossary Terms

The following terms have been successfully ingested and updated in the system glossary:

*   **Ingestion Flip**: The structural shift in the web's economic contract from 'Discovery for Access' (where search crawlers direct users to a site) to 'Digestion' (where AI models ingest content to answer queries directly, bypassing and starving the original source).
*   **Crawl Budget**: The finite computational attention and resources that search engine indexers allocate to a specific website, which SEO consultants mistakenly use to justify deleting legacy content.
*   **Presentist Bias**: The cognitive and historical distortion in AI models caused by deleting pre-2014 web archives, trapping the machine's memory in a highly polarized, post-truth era with no reference point for the early, optimistic web.
*   **Dependency Model**: An information architecture where independent publishers, archives, and products are consolidated into centralized corporate monopolies, replacing ownership with revocable, subscription-based access licenses.
*   **Revocable Access License**: A legal and technical paradigm where consumers do not own digital goods (books, games, software) but merely rent temporary access, allowing corporate owners to brick or delete the product at will.
