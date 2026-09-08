# Skill: Orchestrate Silver Section Assembly

## Overview
Pegleg's master orchestration skill controlling Stage 4 of the Silver ETL Pipeline:
- **Stage 4**: Bilgeladle Section-Level File Assembly & Incompleteness Halt Gate

## Target Agent
- **Pegleg** (Master Mission Orchestrator)

## Execution CLI Command
To run Pegleg's full 5-stage Silver ETL pipeline on Chapter 6 from the terminal:

```bash
.venv\Scripts\python.exe src\react_agent\entrypoints\pegleg_runner.py --silver-chapter 6
```

## Author Chat Invocation Prompt
To invoke Pegleg directly in chat:

> `@Pegleg Orchestrate the full 5-stage Silver ETL pipeline for Chapter 6 using your orchestration skills.`
