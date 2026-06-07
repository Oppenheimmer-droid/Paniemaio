"""
Script para poblar la base de datos con datos de prueba.
Ejecutar: python scripts/seed.py
"""

import asyncio
import uuid
from datetime import datetime

from sqlalchemy import select

from app.core.database import AsyncSessionLocal, engine, Base
from app.core.security import hash_password
from app.models import Tenant, User, Subject, Topic


async def create_tenant(session, name: str, slug: str) -> Tenant:
    """Crea un tenant."""
    tenant = Tenant(
        id=str(uuid.uuid4()),
        name=name,
        slug=slug,
        status="active",
        settings_json="{}"
    )
    session.add(tenant)
    await session.flush()
    return tenant


async def create_user(
    session,
    tenant_id: str,
    email: str,
    password: str,
    first_name: str,
    last_name: str,
    role: str = "student"
) -> User:
    """Crea un usuario."""
    user = User(
        id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        email=email,
        password_hash=hash_password(password),
        first_name=first_name,
        last_name=last_name,
        role=role,
        is_active=True,
        is_verified=True
    )
    session.add(user)
    await session.flush()
    return user


async def create_subject(session, tenant_id: str, name: str, code: str) -> Subject:
    """Crea una materia."""
    subject = Subject(
        id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        name=name,
        code=code,
        description=f"Materia de {name}",
        grade_levels="1-4"
    )
    session.add(subject)
    await session.flush()
    return subject


async def create_topic(session, subject_id: str, name: str, order: int = 0) -> Topic:
    """Crea un tema."""
    topic = Topic(
        id=str(uuid.uuid4()),
        subject_id=subject_id,
        name=name,
        description=f"Tema de {name}",
        difficulty=2,
        order_index=order
    )
    session.add(topic)
    await session.flush()
    return topic


async def seed_database():
    """Puebla la base de datos con datos de prueba."""
    print("🌱 Iniciando seed de base de datos...")
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with AsyncSessionLocal() as session:
        try:
            # Verificar si ya existe el tenant demo
            result = await session.execute(
                select(Tenant).where(Tenant.slug == "demo")
            )
            existing_tenant = result.scalar_one_or_none()
            
            if existing_tenant:
                print("⚠️  El tenant 'demo' ya existe. Saltando seed.")
                return
            
            # Crear Tenant Demo
            print("📦 Creando tenant demo...")
            tenant = await create_tenant(session, "Academia Demo", "demo")
            print(f"  ✅ Tenant creado: {tenant.name} (slug: {tenant.slug})")
            
            # Crear Usuarios
            print("👤 Creando usuarios demo...")
            
            admin = await create_user(
                session, tenant.id,
                "admin@demo.edu", "Demo1234!",
                "Admin", "Demo",
                role="admin"
            )
            print(f"  ✅ Admin: {admin.email}")
            
            teacher = await create_user(
                session, tenant.id,
                "teacher@demo.edu", "Demo1234!",
                "Profesor", "Demo",
                role="teacher"
            )
            print(f"  ✅ Teacher: {teacher.email}")
            
            student = await create_user(
                session, tenant.id,
                "student@demo.edu", "Demo1234!",
                "Alumno", "Demo",
                role="student"
            )
            print(f"  ✅ Student: {student.email}")
            
            # Crear Materias y Temas
            print("📚 Creando materias...")
            
            math = await create_subject(session, tenant.id, "Matemáticas", "MATH101")
            topic1 = await create_topic(session, math.id, "Álgebra Básica", 1)
            topic2 = await create_topic(session, math.id, "Geometría", 2)
            topic3 = await create_topic(session, math.id, "Estadística", 3)
            print(f"  ✅ {math.name} (3 temas)")
            
            science = await create_subject(session, tenant.id, "Ciencias Naturales", "SCI101")
            topic4 = await create_topic(session, science.id, "Biología", 1)
            topic5 = await create_topic(session, science.id, "Química", 2)
            print(f"  ✅ {science.name} (2 temas)")
            
            history = await create_subject(session, tenant.id, "Historia", "HIST101")
            topic6 = await create_topic(session, history.id, "Historia Antigua", 1)
            print(f"  ✅ {history.name} (1 tema)")
            
            language = await create_subject(session, tenant.id, "Lenguaje", "LANG101")
            topic7 = await create_topic(session, language.id, "Gramática", 1)
            topic8 = await create_topic(session, language.id, "Literatura", 2)
            print(f"  ✅ {language.name} (2 temas)")
            
            await session.commit()
            
            print("\n" + "="*50)
            print("✅ SEED COMPLETADO EXITOSAMENTE")
            print("="*50)
            print("\n📋 Credenciales de acceso:")
            print("   Admin:   admin@demo.edu / Demo1234!")
            print("   Teacher: teacher@demo.edu / Demo1234!")
            print("   Student: student@demo.edu / Demo1234!")
            print("\n🌐 Accede a la aplicación en:")
            print("   Frontend: http://localhost:3000")
            print("   API Docs: http://localhost:8000/docs")
            print("="*50)
            
        except Exception as e:
            await session.rollback()
            print(f"❌ Error durante el seed: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(seed_database())