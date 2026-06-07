"""
Servicio de evaluaciones y quizzes.
Generación de preguntas y calificación.
"""

import uuid
import json
from typing import Optional, List, Tuple, Dict, Any
from datetime import datetime

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Evaluation, Question, EvaluationAttempt, Answer,
    EvaluationType, QuestionType, Document
)
from app.rag.vector_store import retrieval_pipeline
from app.core.config import settings


class EvaluationService:
    """Servicio para gestión de evaluaciones."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_evaluation(
        self,
        tenant_id: str,
        document_id: str,
        created_by: str,
        title: str,
        evaluation_type: str = "quiz",
        question_count: int = 5,
        difficulty: int = 3,
        time_limit_minutes: int = 30,
        passing_score: int = 60,
        description: Optional[str] = None
    ) -> Evaluation:
        """Crea una nueva evaluación."""
        evaluation = Evaluation(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            document_id=document_id,
            created_by=created_by,
            title=title,
            description=description,
            evaluation_type=evaluation_type,
            question_count=question_count,
            difficulty=difficulty,
            time_limit_minutes=time_limit_minutes,
            passing_score=passing_score,
            is_published=False,
            total_attempts=0,
            avg_score=None
        )
        
        self.db.add(evaluation)
        await self.db.flush()
        
        return evaluation
    
    async def get_evaluation(
        self,
        evaluation_id: str,
        tenant_id: str
    ) -> Optional[Evaluation]:
        """Obtiene una evaluación."""
        result = await self.db.execute(
            select(Evaluation).where(
                and_(
                    Evaluation.id == evaluation_id,
                    Evaluation.tenant_id == tenant_id
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def list_evaluations(
        self,
        tenant_id: str,
        page: int = 1,
        page_size: int = 20,
        include_unpublished: bool = False
    ) -> Tuple[List[Evaluation], int]:
        """Lista evaluaciones de un tenant."""
        query = select(Evaluation).where(Evaluation.tenant_id == tenant_id)
        
        if not include_unpublished:
            query = query.where(Evaluation.is_published == True)
        
        query = query.order_by(Evaluation.created_at.desc())
        
        # Count
        from sqlalchemy import func
        count_query = select(func.count(Evaluation.id)).where(Evaluation.tenant_id == tenant_id)
        if not include_unpublished:
            count_query = count_query.where(Evaluation.is_published == True)
        
        count_result = await self.db.execute(count_query)
        total = count_result.scalar()
        
        # Paginate
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        
        result = await self.db.execute(query)
        evaluations = result.scalars().all()
        
        return list(evaluations), total
    
    async def publish_evaluation(self, evaluation_id: str, tenant_id: str) -> bool:
        """Publica una evaluación."""
        evaluation = await self.get_evaluation(evaluation_id, tenant_id)
        if not evaluation:
            return False
        
        evaluation.is_published = True
        evaluation.published_at = datetime.utcnow()
        await self.db.flush()
        
        return True
    
    async def generate_questions(
        self,
        evaluation_id: str,
        tenant_id: str
    ) -> int:
        """
        Genera preguntas para una evaluación usando Groq.
        
        Returns:
            Número de preguntas generadas
        """
        evaluation = await self.get_evaluation(evaluation_id, tenant_id)
        if not evaluation:
            raise ValueError(f"Evaluación no encontrada: {evaluation_id}")
        
        # Obtener chunks del documento
        chunks = retrieval_pipeline.retrieve_for_evaluation(
            tenant_id=tenant_id,
            document_id=evaluation.document_id,
            count=evaluation.question_count
        )
        
        if not chunks:
            raise ValueError("No se encontraron chunks para generar preguntas")
        
        # Construir contexto
        context = "\n\n".join([f"[{i+1}] {chunk}" for i, chunk in enumerate(chunks)])
        
        # Generar preguntas con Groq
        questions_data = await self._generate_questions_with_llm(
            context=context,
            count=evaluation.question_count,
            difficulty=evaluation.difficulty
        )
        
        # Guardar preguntas
        for i, q_data in enumerate(questions_data):
            question = Question(
                id=str(uuid.uuid4()),
                evaluation_id=evaluation_id,
                question_text=q_data["question"],
                question_type=q_data.get("type", "multiple_choice"),
                options=q_data.get("options", []),
                correct_answer=q_data.get("correct_answer", {"index": 0}),
                explanation=q_data.get("explanation"),
                difficulty=q_data.get("difficulty", evaluation.difficulty),
                points=q_data.get("points", 1),
                order_index=i
            )
            self.db.add(question)
        
        await self.db.flush()
        
        return len(questions_data)
    
    async def _generate_questions_with_llm(
        self,
        context: str,
        count: int,
        difficulty: int
    ) -> List[Dict[str, Any]]:
        """Genera preguntas usando Groq LLM."""
        try:
            from groq import Groq
            
            client = Groq(api_key=settings.GROQ_API_KEY)
            
            prompt = f"""Eres un profesor que crea quizzes educativos.

Basado en el siguiente contenido educativo, genera {count} preguntas de opción múltiple.

CONTENIDO:
{context}

DIFICULTAD: {difficulty}/5

INSTRUCCIONES:
- Cada pregunta debe tener 4 opciones (A, B, C, D)
- Solo una opción es correcta
- Incluir una explicación de la respuesta correcta
- Distribuye la dificultad entre {difficulty}/5

Responde ÚNICAMENTE con un array JSON válido, sin texto adicional ni markdown:
[
  {{
    "question": "texto de la pregunta",
    "type": "multiple_choice",
    "options": ["Opción A", "Opción B", "Opción C", "Opción D"],
    "correct_answer": {{"index": 0}},
    "explanation": "explicación de por qué la respuesta correcta es la A",
    "difficulty": {difficulty},
    "points": 1
  }}
]

SOLO JSON, sin markdown ni texto adicional:"""
            
            response = client.chat.completions.create(
                model=settings.GROQ_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=4000
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Limpiar markdown si existe
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
                response_text = response_text.strip()
            
            questions = json.loads(response_text)
            return questions
            
        except Exception as e:
            print(f"Error generando preguntas con LLM: {e}")
            # Return dummy questions for testing
            return self._generate_dummy_questions(count, difficulty)
    
    def _generate_dummy_questions(self, count: int, difficulty: int) -> List[Dict]:
        """Genera preguntas dummy para testing."""
        questions = []
        for i in range(count):
            questions.append({
                "question": f"Pregunta de ejemplo {i+1} sobre el contenido",
                "type": "multiple_choice",
                "options": ["Opción A", "Opción B", "Opción C", "Opción D"],
                "correct_answer": {"index": i % 4},
                "explanation": "Esta es una pregunta de ejemplo.",
                "difficulty": difficulty,
                "points": 1
            })
        return questions
    
    async def start_attempt(
        self,
        evaluation_id: str,
        user_id: str,
        tenant_id: str
    ) -> EvaluationAttempt:
        """Inicia un intento de evaluación."""
        evaluation = await self.get_evaluation(evaluation_id, tenant_id)
        if not evaluation or not evaluation.is_published:
            raise ValueError("Evaluación no disponible")
        
        attempt = EvaluationAttempt(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            evaluation_id=evaluation_id,
            user_id=user_id,
            started_at=datetime.utcnow()
        )
        
        self.db.add(attempt)
        
        # Update stats
        evaluation.total_attempts += 1
        
        await self.db.flush()
        
        return attempt
    
    async def grade_attempt(
        self,
        attempt_id: str,
        tenant_id: str
    ) -> Dict[str, Any]:
        """Califica un intento de evaluación."""
        result = await self.db.execute(
            select(EvaluationAttempt).where(
                and_(
                    EvaluationAttempt.id == attempt_id,
                    EvaluationAttempt.tenant_id == tenant_id
                )
            )
        )
        attempt = result.scalar_one_or_none()
        
        if not attempt:
            raise ValueError(f"Intento no encontrado: {attempt_id}")
        
        # Get all answers for this attempt
        answers_result = await self.db.execute(
            select(Answer).where(Answer.attempt_id == attempt_id)
        )
        answers = answers_result.scalars().all()
        
        # Calculate score
        total_points = 0
        earned_points = 0
        
        for answer in answers:
            if answer.is_correct:
                earned_points += answer.points_earned
        
        # Get questions to calculate total
        questions_result = await self.db.execute(
            select(Question).where(Question.evaluation_id == attempt.evaluation_id)
        )
        questions = questions_result.scalars().all()
        
        for q in questions:
            total_points += q.points
        
        # Calculate percentage
        score = (earned_points / total_points * 100) if total_points > 0 else 0
        
        # Update attempt
        attempt.score = score
        attempt.passed = score >= 60  # Assuming 60% passing score
        attempt.completed_at = datetime.utcnow()
        
        # Update evaluation avg_score
        eval_result = await self.db.execute(
            select(Evaluation).where(Evaluation.id == attempt.evaluation_id)
        )
        evaluation = eval_result.scalar_one_or_none()
        
        if evaluation:
            if evaluation.avg_score is None:
                evaluation.avg_score = score
            else:
                evaluation.avg_score = (evaluation.avg_score * (evaluation.total_attempts - 1) + score) / evaluation.total_attempts
        
        await self.db.flush()
        
        return {
            "score": score,
            "passed": attempt.passed,
            "total_points": total_points,
            "earned_points": earned_points
        }