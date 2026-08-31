---
name: "临思智训"
description: "面向医学教育的AI标准化病人临床思维训练平台"
colors:
  clinical-ink: "#102326"
  paper-surface: "#fbfefd"
  slate-surface: "#eef6f5"
  teal-core: "#0f766e"
  teal-soft: "#dff3f0"
  orange-risk: "#d97706"
typography:
  display:
    fontFamily: '"Microsoft YaHei UI", "PingFang SC", "Segoe UI", sans-serif'
    fontSize: "clamp(2.8rem, 6.4vw, 5.4rem)"
    fontWeight: 800
    lineHeight: 1
    letterSpacing: "0"
  body:
    fontFamily: '"Microsoft YaHei UI", "PingFang SC", "Segoe UI", sans-serif'
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.72
    letterSpacing: "0"
rounded:
  sm: "10px"
  md: "12px"
  lg: "16px"
spacing:
  sm: "10px"
  md: "16px"
  lg: "32px"
components:
  button-primary:
    backgroundColor: "{colors.teal-core}"
    textColor: "#ffffff"
    rounded: "{rounded.sm}"
    padding: "12px 18px"
---

# Design System: 临思智训

## Overview

**Creative North Star: "Clinical Teaching Workbench"**

The interface is a usable medical education workbench, not a promotional page. The visual system should feel like a clean clinical training room: light surfaces, teal structure, orange risk reminders, compact score panels, and traceable evidence blocks.

Key Characteristics:
- Workbench-first composition with cases, chat, scoring, and missing-point alerts in the first interactive area.
- Blue-green primary color for medical education technology.
- Orange reserved for risk and missing-point reminders.
- Real product states: loading, mock fallback, score progress, citations, teacher metrics, and report sections.

## Colors

The palette uses medical teal as the structural color and orange only for risk reminders.

### Primary
- **Teal Core**: main action, active state, score emphasis, and graph nodes.

### Secondary
- **Orange Risk**: missing reminders and clinical risk attention.

### Neutral
- **Clinical Ink**: primary readable text.
- **Paper Surface**: cards, chat, and knowledge blocks.
- **Slate Surface**: page background.

**The Safety Color Rule.** Orange is not decoration. It only marks risk, missing information, or teaching attention.

## Typography

**Display Font:** Microsoft YaHei UI with PingFang SC and Segoe UI fallbacks.
**Body Font:** Microsoft YaHei UI with PingFang SC and Segoe UI fallbacks.

## Layout

Desktop uses a three-column training grid: case list, patient chat, scoring and missing reminders. Mobile collapses to one column while preserving the same workflow order.

## Elevation & Depth

Depth is subtle and functional. Panels use light shadows and borders to separate workflows. No heavy glow or dark sci-fi treatment.

## Shapes

Panels use 16px corners, controls use 10-12px corners, and role switches use pill shapes because they are compact binary controls.

## Components

### Buttons
Primary buttons use teal fill and white text. Secondary actions use light surfaces and structural borders.

### Training Panels
Panels group one task: case selection, chat, scoring, knowledge, dashboard, or report. Nested cards are avoided except for repeated list items.

### Progress
Progress bars show score and class improvement, with text labels always present.

## Do's and Don'ts

### Do:
- **Do** make the AI standardized patient chat usable immediately.
- **Do** keep citations visible beside feedback.
- **Do** state education-only safety boundaries.

### Don't:
- **Don't** use real patient information.
- **Don't** let the AI patient reveal diagnosis without student reasoning.
- **Don't** turn the site into a static contest explanation page.
