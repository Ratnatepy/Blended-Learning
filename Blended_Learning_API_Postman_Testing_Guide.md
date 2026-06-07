# Blended Learning Recommendation API - Postman Testing Guide

## 1. Start the backend

From the project root, start PostgreSQL first if needed:

```bash
docker compose up -d 
```

Then start FastAPI:

```bash
uvicorn api.main:app --reload
```

Default API URL:

```text
http://127.0.0.1:8000
```

## 2. Import into Postman

Import these two files:

1. `Blended_Learning_Recommendation_API_Postman_Collection.json`
2. `Blended_Learning_Local_Postman_Environment.json`

Select the environment named **Blended Learning Local FastAPI Environment**.

## 3. Main endpoints included

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/` | API health check |
| GET | `/openapi.json` | FastAPI OpenAPI schema |
| GET | `/docs` | Swagger UI |
| GET | `/redoc` | ReDoc UI |
| GET | `/students/?limit={limit}` | Get stored recommendation records |
| GET | `/students/summary` | Dashboard summary |
| GET | `/students/recent?limit={limit}` | Recently added records |
| GET | `/students/{student_id}` | Lookup one stored student by ID |
| POST | `/recommendations/generate` | Generate and save a new student recommendation |

## 4. Recommended testing order

Use the folder **Recommended Test Flow** in Postman:

1. Check API is Running
2. Check Dashboard Before Create
3. Create New Demo Recommendation
4. Read Newly Created Student
5. Check Recent Students
6. Check Dashboard After Create

The create request uses a dynamic student ID like:

```text
flow_demo_{$timestamp}
```

After successful creation, the collection test script saves the returned ID into:

```text
{last_student_id}
```

Then the next request can automatically read that newly created student.

## 5. Required request body for `/recommendations/generate`

The backend requires exactly these 33 model features inside `responses`:

```json
{
  "student_id": "demo_active_{{$timestamp}}",
  "responses": {
    "use_lecture_slides": 5,
    "use_video_lectures": 5,
    "use_quizzes": 5,
    "use_articles": 5,
    "use_forums": 5,
    "use_simulations": 5,
    "online_discussion_participation": 5,
    "peer_collaboration": 5,
    "comfort_asking_questions": 5,
    "sense_of_community": 5,
    "integration_quality": 5,
    "overall_understanding": 5,
    "lect_clear_instructions": 5,
    "lect_responsive": 5,
    "lect_diverse_tools": 5,
    "lect_timely_feedback": 5,
    "lect_foster_interaction": 5,
    "self_prioritize_deadlines": 5,
    "self_study_schedule": 5,
    "self_prepare_class": 5,
    "self_responsibility": 5,
    "career_preparation": 5,
    "video_helpfulness": 5,
    "digital_literacy_improvement": 5,
    "tech_issues_freq": 2,
    "lms_usability": 5,
    "overall_satisfaction": 5,
    "benefit_flexibility": 5,
    "benefit_variety": 5,
    "benefit_recorded_access": 5,
    "benefit_self_study_time": 5,
    "benefit_life_balance": 5,
    "benefit_self_directed": 5
  },
  "strengths_positive_aspects": "I like flexible learning and recorded lectures.",
  "challenges_suggestions": "I need clearer instructions and more interaction."
}
```

## 6. Expected negative tests

The collection also includes these error tests:

| Request | Expected result |
|---|---|
| Get Unknown Student | 404 |
| Duplicate ID | 409 after a successful generate request |
| Missing Features | 400 |
| Invalid Numeric Value | currently may return 500 unless backend validation is improved |

## 7. Note for thesis demo

For your thesis demonstration, show this flow:

Frontend/User input → `POST /recommendations/generate` → K-Modes cluster assignment → NLP tag extraction → LLM/rule-based recommendation report → stored in PostgreSQL → retrieved by `/students` endpoints.
