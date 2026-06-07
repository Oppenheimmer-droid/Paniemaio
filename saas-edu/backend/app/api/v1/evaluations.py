"""
API Endpoints de Evaluaciones.
"""

from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, CurrentUser, require_teacher
from app.services.evaluation_service import EvaluationService
from app.schemas.schemas import (
    EvaluationCreate,
    EvaluationResponse,
    EvaluationDetailResponse,
    QuestionResponse,
    StartAttemptResponse,
    SubmitAttemptRequest,
    AttemptResultResponse,
    ErrorResponse,
)
from app.workers.tasks import generate_evaluation_task, grade_evaluation_task


router = APIRouter(prefix="/evaluations", tags=["Evaluaciones"])


def get_evaluation_service(db: AsyncSession = Depends(get_db)) -> EvaluationService:
    return EvaluationService(db)


@router.post(
    "",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Crear evaluación",
    description="Crea una nueva evaluación y encola la generación de preguntas."
)
async def create_evaluation(
    request: EvaluationCreate,
    current_user: CurrentUser = Depends(require_teacher),
    eval_service: EvaluationService = Depends(get_evaluation_service)
):
    """Endpoint para crear evaluaciones."""
    evaluation = await eval_service.create_evaluation(
        tenant_id=current_user.tenant_id,
        document_id=request.document_id,
        created_by=current_user.id,
        title=request.title,
        description=request.description,
        evaluation_type=request.evaluation_type,
        question_count=request.question_count,
        difficulty=request.difficulty,
        time_limit_minutes=request.time_limit_minutes,
        passing_score=request.passing_score
    )
    
    # Encolar generación de preguntas
    generate_evaluation_task.delay(
        evaluation_id=evaluation.id,
        tenant_id=current_user.tenant_id
    )
    
    return {
        "id": evaluation.id,
        "title": evaluation.title,
        "status": "generating",
        "message": "Evaluación encolada para generación"
    }


@router.get(
    "",
    summary="Listar evaluaciones",
    description="Lista las evaluaciones del tenant."
)
async def list_evaluations(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_user),
    eval_service: EvaluationService = Depends(get_evaluation_service)
):
    """Endpoint para listar evaluaciones."""
    # Students solo ven publicadas, teachers ven todas
    include_unpublished = current_user.role in ["admin", "teacher"]
    
    evaluations, total = await eval_service.list_evaluations(
        tenant_id=current_user.tenant_id,
        page=page,
        page_size=page_size,
        include_unpublished=include_unpublished
    )
    
    return {
        "items": [EvaluationResponse.model_validate(e) for e in evaluations],
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get(
    "/{evaluation_id}",
    summary="Obtener evaluación",
    description="Obtiene detalles de una evaluación con preguntas."
)
async def get_evaluation(
    evaluation_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    eval_service: EvaluationService = Depends(get_evaluation_service)
):
    """Endpoint para obtener evaluación."""
    evaluation = await eval_service.get_evaluation(evaluation_id, current_user.tenant_id)
    
    if not evaluation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "EVALUATION_NOT_FOUND", "message": "Evaluación no encontrada"}
        )
    
    # Check visibility
    if not evaluation.is_published and current_user.role == "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "NOT_PUBLISHED", "message": "Evaluación no publicada"}
        )
    
    # Get questions
    from sqlalchemy import select
    from app.models import Question
    
    result = await eval_service.db.execute(
        select(Question).where(Question.evaluation_id == evaluation_id)
    )
    questions = result.scalars().all()
    
    # Hide correct_answer for students
    questions_response = []
    for q in questions:
        q_data = QuestionResponse.model_validate(q)
        if current_user.role == "student":
            q_data.options = []  # Hide options too
            if hasattr(q, 'correct_answer'):
                q_data = q_data.model_copy(deep=True)
                # Don't expose correct_answer
        questions_response.append(q_data)
    
    return EvaluationDetailResponse(
        evaluation=EvaluationResponse.model_validate(evaluation),
        questions=questions_response
    )


@router.patch(
    "/{evaluation_id}/publish",
    summary="Publicar evaluación",
    description="Publica una evaluación para que esté disponible."
)
async def publish_evaluation(
    evaluation_id: str,
    current_user: CurrentUser = Depends(require_teacher),
    eval_service: EvaluationService = Depends(get_evaluation_service)
):
    """Endpoint para publicar evaluación."""
    success = await eval_service.publish_evaluation(evaluation_id, current_user.tenant_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "EVALUATION_NOT_FOUND", "message": "Evaluación no encontrada"}
        )
    
    return {"status": "published"}


@router.post(
    "/{evaluation_id}/attempts",
    response_model=StartAttemptResponse,
    summary="Iniciar intento",
    description="Inicia un nuevo intento de evaluación."
)
async def start_attempt(
    evaluation_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    eval_service: EvaluationService = Depends(get_evaluation_service)
):
    """Endpoint para iniciar intento."""
    try:
        attempt = await eval_service.start_attempt(
            evaluation_id=evaluation_id,
            user_id=current_user.id,
            tenant_id=current_user.tenant_id
        )
        
        # Get evaluation for time limit
        evaluation = await eval_service.get_evaluation(evaluation_id, current_user.tenant_id)
        
        return StartAttemptResponse(
            attempt_id=attempt.id,
            evaluation_id=attempt.evaluation_id,
            started_at=attempt.started_at,
            time_limit_minutes=evaluation.time_limit_minutes if evaluation else 30
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "EVALUATION_NOT_AVAILABLE", "message": str(e)}
        )


@router.post(
    "/attempts/{attempt_id}/submit",
    summary="Enviar respuestas",
    description="Envía las respuestas de un intento y obtiene el resultado."
)
async def submit_attempt(
    attempt_id: str,
    request: SubmitAttemptRequest,
    current_user: CurrentUser = Depends(get_current_user),
    eval_service: EvaluationService = Depends(get_evaluation_service)
):
    """Endpoint para submit attempt."""
    from sqlalchemy import select, and_
    from app.models import EvaluationAttempt, Answer, Question
    import uuid
    
    # Get attempt
    result = await eval_service.db.execute(
        select(EvaluationAttempt).where(
            and_(
                EvaluationAttempt.id == attempt_id,
                EvaluationAttempt.user_id == current_user.id,
                EvaluationAttempt.tenant_id == current_user.tenant_id
            )
        )
    )
    attempt = result.scalar_one_or_none()
    
    if not attempt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "ATTEMPT_NOT_FOUND", "message": "Intento no encontrado"}
        )
    
    # Process answers
    total_points = 0
    earned_points = 0
    
    for ans in request.answers:
        # Get question
        q_result = await eval_service.db.execute(
            select(Question).where(Question.id == ans.question_id)
        )
        question = q_result.scalar_one_or_none()
        
        if not question:
            continue
        
        total_points += question.points
        
        # Check answer
        is_correct = False
        points_earned = 0
        
        # Multiple choice: compare index
        if question.question_type == "multiple_choice":
            correct_idx = question.correct_answer.get("index", 0) if isinstance(question.correct_answer, dict) else 0
            try:
                user_idx = int(ans.answer_text)
                if user_idx == correct_idx:
                    is_correct = True
                    points_earned = question.points
            except:
                pass
        
        # Create answer record
        answer = Answer(
            id=str(uuid.uuid4()),
            attempt_id=attempt_id,
            question_id=ans.question_id,
            answer_text=ans.answer_text,
            is_correct=is_correct,
            points_earned=points_earned
        )
        eval_service.db.add(answer)
        earned_points += points_earned
    
    await eval_service.db.flush()
    
    # Calculate score
    score = (earned_points / total_points * 100) if total_points > 0 else 0
    passed = score >= 60  # Assuming 60% passing
    
    # Update attempt
    attempt.score = score
    attempt.passed = passed
    attempt.completed_at = datetime.utcnow()
    attempt.time_spent_seconds = int((datetime.utcnow() - attempt.started_at).total_seconds())
    
    await eval_service.db.commit()
    
    # Get answers for response
    answers_result = await eval_service.db.execute(
        select(Answer).where(Answer.attempt_id == attempt_id)
    )
    answers = answers_result.scalars().all()
    
    return AttemptResultResponse(
        attempt_id=attempt.id,
        evaluation_id=attempt.evaluation_id,
        score=score,
        passed=passed,
        total_points=total_points,
        earned_points=earned_points,
        time_spent_seconds=attempt.time_spent_seconds,
        completed_at=attempt.completed_at,
        answers=[{
            "question_id": a.question_id,
            "answer_text": a.answer_text,
            "is_correct": a.is_correct,
            "points_earned": a.points_earned,
            "ai_grade_feedback": a.ai_grade_feedback
        } for a in answers]
    )


@router.get(
    "/attempts/{attempt_id}/result",
    summary="Obtener resultado",
    description="Obtiene el resultado de un intento."
)
async def get_attempt_result(
    attempt_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    eval_service: EvaluationService = Depends(get_evaluation_service)
):
    """Endpoint para obtener resultado."""
    from sqlalchemy import select, and_
    from app.models import EvaluationAttempt, Answer, Question
    
    result = await eval_service.db.execute(
        select(EvaluationAttempt).where(
            and_(
                EvaluationAttempt.id == attempt_id,
                EvaluationAttempt.tenant_id == current_user.tenant_id
            )
        )
    )
    attempt = result.scalar_one_or_none()
    
    if not attempt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "ATTEMPT_NOT_FOUND", "message": "Intento no encontrado"}
        )
    
    # Check ownership (students only see their own)
    if current_user.role == "student" and attempt.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "NOT_AUTHORIZED", "message": "No tienes acceso"}
        )
    
    # Get answers
    answers_result = await eval_service.db.execute(
        select(Answer).where(Answer.attempt_id == attempt_id)
    )
    answers = answers_result.scalars().all()
    
    # Get total points
    questions_result = await eval_service.db.execute(
        select(Question).where(Question.evaluation_id == attempt.evaluation_id)
    )
    questions = questions_result.scalars().all()
    total_points = sum(q.points for q in questions)
    
    return AttemptResultResponse(
        attempt_id=attempt.id,
        evaluation_id=attempt.evaluation_id,
        score=attempt.score,
        passed=attempt.passed,
        total_points=total_points,
        earned_points=int(attempt.score * total_points / 100),
        time_spent_seconds=attempt.time_spent_seconds,
        completed_at=attempt.completed_at,
        answers=[{
            "question_id": a.question_id,
            "answer_text": a.answer_text,
            "is_correct": a.is_correct,
            "points_earned": a.points_earned,
            "ai_grade_feedback": a.ai_grade_feedback
        } for a in answers]
    )