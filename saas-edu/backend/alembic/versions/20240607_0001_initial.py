"""Initial migration - all tables

Revision ID: 20240607_0001_initial
Revises: 
Create Date: 2024-06-07 00:01:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '20240607_0001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # TENANTS
    op.create_table(
        'tenants',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(100), unique=True, nullable=False),
        sa.Column('status', sa.String(20), default='active'),
        sa.Column('settings_json', sa.Text, default='{}'),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_tenants_slug', 'tenants', ['slug'])

    # USERS
    op.create_table(
        'users',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('tenant_id', sa.String(36), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('role', sa.String(20), default='student'),
        sa.Column('first_name', sa.String(100), nullable=False),
        sa.Column('last_name', sa.String(100), nullable=False),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('is_verified', sa.Boolean, default=False),
        sa.Column('last_login', sa.DateTime, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('ix_users_tenant_id', 'users', ['tenant_id'])
    op.create_index('ix_users_email', 'users', ['email'])

    # REFRESH_TOKENS
    op.create_table(
        'refresh_tokens',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('token_hash', sa.String(255), unique=True, nullable=False),
        sa.Column('expires_at', sa.DateTime, nullable=False),
        sa.Column('is_revoked', sa.Boolean, default=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('ix_refresh_tokens_user_id', 'refresh_tokens', ['user_id'])

    # SUBJECTS
    op.create_table(
        'subjects',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('tenant_id', sa.String(36), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('grade_levels', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('ix_subjects_tenant_id', 'subjects', ['tenant_id'])

    # TOPICS
    op.create_table(
        'topics',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('subject_id', sa.String(36), sa.ForeignKey('subjects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('difficulty', sa.Integer, default=1),
        sa.Column('order_index', sa.Integer, default=0),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('ix_topics_subject_id', 'topics', ['subject_id'])

    # DOCUMENTS
    op.create_table(
        'documents',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('tenant_id', sa.String(36), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('subject_id', sa.String(36), sa.ForeignKey('subjects.id', ondelete='SET NULL'), nullable=True),
        sa.Column('topic_id', sa.String(36), sa.ForeignKey('topics.id', ondelete='SET NULL'), nullable=True),
        sa.Column('uploaded_by', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('file_path', sa.String(512), nullable=False),
        sa.Column('file_size', sa.Integer, default=0),
        sa.Column('mime_type', sa.String(100), default='application/pdf'),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('status', sa.String(20), default='pending'),
        sa.Column('page_count', sa.Integer, default=0),
        sa.Column('chunk_count', sa.Integer, default=0),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('difficulty', sa.Integer, default=1),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('processed_at', sa.DateTime, nullable=True),
    )
    op.create_index('ix_documents_tenant_id', 'documents', ['tenant_id'])
    op.create_index('ix_documents_status', 'documents', ['status'])

    # DOCUMENT_CHUNKS
    op.create_table(
        'document_chunks',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('document_id', sa.String(36), sa.ForeignKey('documents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('tenant_id', sa.String(36), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('chunk_index', sa.Integer, nullable=False),
        sa.Column('page_number', sa.Integer, nullable=True),
        sa.Column('vector_id', sa.String(255), nullable=True),
        sa.Column('start_char', sa.Integer, default=0),
        sa.Column('end_char', sa.Integer, default=0),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('ix_document_chunks_document_id', 'document_chunks', ['document_id'])
    op.create_index('ix_document_chunks_tenant_id', 'document_chunks', ['tenant_id'])

    # CHAT_SESSIONS
    op.create_table(
        'chat_sessions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('tenant_id', sa.String(36), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('document_id', sa.String(36), sa.ForeignKey('documents.id', ondelete='CASCADE'), nullable=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('is_archived', sa.Boolean, default=False),
        sa.Column('message_count', sa.Integer, default=0),
        sa.Column('total_tokens', sa.Integer, default=0),
        sa.Column('last_message_at', sa.DateTime, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('ix_chat_sessions_tenant_id', 'chat_sessions', ['tenant_id'])

    # CHAT_MESSAGES
    op.create_table(
        'chat_messages',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('session_id', sa.String(36), sa.ForeignKey('chat_sessions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role', sa.String(20), nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('citations', sa.JSON, default=list),
        sa.Column('tokens_used', sa.Integer, default=0),
        sa.Column('latency_ms', sa.Integer, nullable=True),
        sa.Column('model', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('ix_chat_messages_session_id', 'chat_messages', ['session_id'])

    # EVALUATIONS
    op.create_table(
        'evaluations',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('tenant_id', sa.String(36), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('document_id', sa.String(36), sa.ForeignKey('documents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('created_by', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('evaluation_type', sa.String(20), default='quiz'),
        sa.Column('question_count', sa.Integer, default=5),
        sa.Column('difficulty', sa.Integer, default=3),
        sa.Column('time_limit_minutes', sa.Integer, default=30),
        sa.Column('passing_score', sa.Integer, default=60),
        sa.Column('is_published', sa.Boolean, default=False),
        sa.Column('total_attempts', sa.Integer, default=0),
        sa.Column('avg_score', sa.Float, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('published_at', sa.DateTime, nullable=True),
    )
    op.create_index('ix_evaluations_tenant_id', 'evaluations', ['tenant_id'])

    # QUESTIONS
    op.create_table(
        'questions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('evaluation_id', sa.String(36), sa.ForeignKey('evaluations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('question_text', sa.Text, nullable=False),
        sa.Column('question_type', sa.String(20), default='multiple_choice'),
        sa.Column('options', sa.JSON, default=list),
        sa.Column('correct_answer', sa.JSON, nullable=False),
        sa.Column('explanation', sa.Text, nullable=True),
        sa.Column('difficulty', sa.Integer, default=3),
        sa.Column('points', sa.Integer, default=1),
        sa.Column('order_index', sa.Integer, default=0),
        sa.Column('source_chunk_id', sa.String(36), nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('ix_questions_evaluation_id', 'questions', ['evaluation_id'])

    # EVALUATION_ATTEMPTS
    op.create_table(
        'evaluation_attempts',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('tenant_id', sa.String(36), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('evaluation_id', sa.String(36), sa.ForeignKey('evaluations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('score', sa.Float, default=0),
        sa.Column('passed', sa.Boolean, default=False),
        sa.Column('started_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime, nullable=True),
        sa.Column('time_spent_seconds', sa.Integer, default=0),
    )
    op.create_index('ix_evaluation_attempts_tenant_id', 'evaluation_attempts', ['tenant_id'])

    # ANSWERS
    op.create_table(
        'answers',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('attempt_id', sa.String(36), sa.ForeignKey('evaluation_attempts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('question_id', sa.String(36), sa.ForeignKey('questions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('answer_text', sa.Text, nullable=False),
        sa.Column('is_correct', sa.Boolean, default=False),
        sa.Column('points_earned', sa.Integer, default=0),
        sa.Column('ai_grade_feedback', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('ix_answers_attempt_id', 'answers', ['attempt_id'])


def downgrade() -> None:
    op.drop_table('answers')
    op.drop_table('evaluation_attempts')
    op.drop_table('questions')
    op.drop_table('evaluations')
    op.drop_table('chat_messages')
    op.drop_table('chat_sessions')
    op.drop_table('document_chunks')
    op.drop_table('documents')
    op.drop_table('topics')
    op.drop_table('subjects')
    op.drop_table('refresh_tokens')
    op.drop_table('users')
    op.drop_table('tenants')
