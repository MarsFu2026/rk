# Design Doc: Design Doc Review Agent

> **[TEST DOCUMENT]** This document is intentionally incomplete for testing the Design Doc Review Agent. Most sections are missing or underdeveloped.

**Version**: v0.1 (stub)  
**Date**: 2026-05-20

---

## 1. Overview

A GitHub Actions CI check that uses Claude to review pull requests.

When a PR is opened, the agent fetches linked documents and scores alignment from 0–10.

---

## 2. Trigger

Runs on `pull_request` events (opened, synchronize).

---

<!-- INTENTIONALLY MISSING:
  - Section 3: Document fetching logic
  - Section 4: AI prompt design and scoring criteria
  - Section 5: PR comment format
  - Section 6: CI pass/fail behavior and threshold config
  - Section 7: Security / secrets management
  - Section 8: Error handling and fallback behavior
  - Section 9: Non-functional requirements (latency, token limits)
  - Section 10: Architecture diagram
-->
