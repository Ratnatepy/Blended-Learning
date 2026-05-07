from fastapi import FastAPI

from api.database import Base, engine, SessionLocal
from api.seed import seed_student_recommendations
from api.routes import students, recommendations

Base.metadata.create_all(bind=engine)

db = SessionLocal()
try:
    seed_student_recommendations(db)
finally:
    db.close()

app = FastAPI(
    title="Blended Learning Recommendation API",
    description="FastAPI backend for student segmentation and personalized recommendation prototype",
    version="1.0.0"
)

app.include_router(students.router, prefix="/students", tags=["Students"])
app.include_router(recommendations.router, prefix="/recommendations", tags=["Recommendations"])


@app.get("/")
def root():
    return {
        "message": "Blended Learning Recommendation API is running",
        "docs": "http://127.0.0.1:8000/docs"
    }