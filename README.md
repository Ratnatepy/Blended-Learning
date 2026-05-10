# Blended Learning Recommendation System

A thesis prototype for a **segment-based personalized recommendation system** for blended learning.

The system uses student survey responses, K-Modes clustering, NLP-based recommendation tags, OpenRouter LLM generation, FastAPI, PostgreSQL, and Streamlit to generate personalized blended-learning recommendations.

---

## Project Overview

This project was developed as part of a thesis on personalized recommendations for blended learning.

The system allows students or respondents to submit blended-learning survey responses. The backend assigns a learner segment, extracts recommendation themes from open-ended responses, generates a recommendation report, and stores the result in PostgreSQL.

The project supports:

- ITC student lookup using official ITC student IDs
- Saved record lookup for ITC, demo, and external respondent records
- New student/respondent input
- K-Modes-based learner segmentation
- NLP-based theme and recommendation tag extraction
- OpenRouter LLM-generated recommendation reports
- PostgreSQL database storage
- Streamlit student portal and admin dashboard
- FastAPI backend service

---

## Thesis Purpose

The purpose of this thesis prototype is to demonstrate how student survey data can be used to support personalized blended-learning guidance.

The system is best described as an:

> Exploratory segment-based blended-learning recommendation prototype.

It should not be presented as a fully validated high-stakes prediction system. The learner segments and recommendations are intended for research demonstration and student-support guidance.

Recommended thesis wording:

> The system is a prototype that demonstrates how survey-based learner segmentation and NLP-supported recommendation tags can be combined with LLM generation to produce personalized blended-learning guidance.

Avoid claiming:

> The system accurately predicts each student's learning needs.

Use instead:

> The system provides segment-informed personalized recommendations based on survey responses and open-ended feedback.

---

## Dataset Summary

The original survey dataset contained:

| Item | Value |
|---|---:|
| Raw survey responses | 445 |
| Cleaned valid responses | 420 |
| Excluded responses | 25 |
| Ordinal clustering features | 33 |
| Open-ended response fields | 2 |
| Main clustering method | K-Modes |

The system uses **33 ordinal survey features** for learner segmentation and **2 open-ended response fields** for NLP-based theme extraction and recommendation tag generation.

The two open-ended response fields are:

1. **Strengths / positive aspects of blended learning**
2. **Challenges, suggestions, or improvement needs**

The ordinal features are used by the saved K-Modes model to assign learner segments. The open-ended responses are processed separately to extract themes such as flexibility, interaction, technical issues, learning support, and learning environment needs.

---

## System Architecture

The system follows a three-layer architecture:

```text
Streamlit Frontend
        ↓
FastAPI Backend
        ↓
PostgreSQL Database

## Quick Start

Install dependencies from the project root:

```bash
pip install -r requirements.txt


Start PostgreSQL:

docker compose up -d postgres

Start FastAPI:

uvicorn api.main:app --reload

Start Streamlit:

```bash
streamlit run app/streamlit_app.py