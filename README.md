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

This project is best described as an **exploratory segment-based blended-learning recommendation prototype**. It combines survey-based learner segmentation, NLP-supported recommendation tags, and LLM-generated reports to produce personalized guidance based on structured survey responses and open-ended feedback.

The system is intended for research demonstration and student-support guidance. It should not be interpreted as a fully validated high-stakes prediction system or as a tool that accurately determines each student's learning needs.

In this thesis, the system provides **segment-informed personalized recommendations** based on students' blended-learning experiences, learner profiles, and self-reported challenges.

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

The system follows a full pipeline architecture from survey data collection to recommendation output and dashboard visualization.

```text
Survey Data
    ↓
Preprocessing Pipeline
    ↓
Clustering + NLP
    ↓
Recommendation Engine
    ↓
FastAPI Backend
    ↓
PostgreSQL Database
    ↓
Streamlit Dashboard
```

---

## Screenshots

### Student Portal

![Student Portal](screenshots/student.png)

### Admin Portal

![Admin Portal](screenshots/admin.png)

---

## Ethics and Privacy

Because this project uses student survey data, ethical and privacy considerations are important.

This project follows the following principles:

- Student data is used for educational research purposes only.
- Personally identifiable information is not stored in the recommendation output.
- Student identifiers are used only for lookup and record-matching purposes.
- The system is designed for thesis demonstration and student-support guidance, not for high-stakes academic decision-making.
- Survey participation is based on consent.
- Data anonymization is applied where possible during analysis and reporting.
- The generated recommendation should be interpreted as supportive guidance, not as a final judgment of a student's learning ability or performance.