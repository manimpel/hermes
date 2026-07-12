from datetime import datetime, date, timedelta, time as dt_time
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, text
from app.database import get_db
from app.models.models import (
    User, Project, ProjectStatus, TimelineUnit,
    FreelancerProfile, DailyMatchBatch, Swipe,
    RevisionRequest, Payment, PaymentType, PaymentStatus,
)
from app.schemas.schemas import (
    ProjectCreate, ProjectUpdate, ProjectOut,
    RevisionRequestCreate,
)
from app.services.auth import get_current_user
from app.services.notifications import notify
from app.services.payments import create_upi_order, create_payment_record, release_payout
from app.agent.matcher import hermes_match_freelancers
from app.agent.audio_transcriber import transcribe_audio_brief

router = APIRouter(prefix="/projects", tags=["projects"])


# ─── CRUD ───────────────────────────────────────────────────

@router.post("/", response_model=ProjectOut)
async def create_project(
    data: ProjectCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    project = Project(client_id=user.id, **data.model_dump(exclude_unset=True))
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project


@router.put("/{project_id}", response_model=ProjectOut)
async def update_project(
    project_id: str,
    data: ProjectUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(404, "Project not found")
    if str(project.client_id) != str(user.id):
        raise HTTPException(403, "Not your project")
    if project.status != ProjectStatus.DRAFT:
        raise HTTPException(400, "Can only edit DRAFT projects")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(project, field, value)

    await db.commit()
    await db.refresh(project)
    return project


@router.get("/{project_id}", response_model=ProjectOut)
async def get_project(project_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(404, "Project not found")
    return project


@router.get("/", response_model=list[ProjectOut])
async def list_projects(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Project).where(Project.client_id == user.id).order_by(Project.created_at.desc())
    )
    return result.scalars().all()


# ─── File uploads ───────────────────────────────────────────

@router.post("/{project_id}/upload-samples")
async def upload_samples(
    project_id: str,
    files: list[UploadFile] = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if len(files) > 5:
        raise HTTPException(400, "Maximum 5 work sample files")

    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project or str(project.client_id) != str(user.id):
        raise HTTPException(403, "Not your project")

    # In production, upload to S3/Cloudinary and store URLs
    urls = []
    for f in files:
        # Stub: save locally
        content = await f.read()
        path = f"/tmp/hermes_samples/{project_id}/{f.filename}"
        import os
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as out:
            out.write(content)
        urls.append(path)

    project.work_samples = (project.work_samples or []) + urls
    await db.commit()
    return {"message": f"{len(urls)} files uploaded", "urls": urls}


@router.post("/{project_id}/upload-audio")
async def upload_audio(
    project_id: str,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project or str(project.client_id) != str(user.id):
        raise HTTPException(403, "Not your project")

    content = await file.read()
    import os
    path = f"/tmp/hermes_audio/{project_id}/{file.filename}"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as out:
        out.write(content)

    project.audio_brief_url = path
    await db.commit()

    # Transcribe in background
    async def _transcribe():
        transcript = await transcribe_audio_brief(path)
        async with db.begin():
            if not project.written_brief:
                project.written_brief = transcript
            else:
                project.written_brief += f"\n\n[Audio Brief Transcription]:\n{transcript}"
            await db.commit()

    background_tasks.add_task(_transcribe)
    return {"message": "Audio uploaded, transcription in progress"}


# ─── Publish → triggers matching ────────────────────────────

@router.post("/{project_id}/publish")
async def publish_project(
    project_id: str,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project or str(project.client_id) != str(user.id):
        raise HTTPException(403, "Not your project")
    if project.status != ProjectStatus.DRAFT:
        raise HTTPException(400, "Only DRAFT projects can be published")

    project.status = ProjectStatus.MATCHING
    await db.commit()

    background_tasks.add_task(generate_daily_batch, str(project.id), str(user.id), db)
    return {"message": "Project published. Generating matches..."}


# ─── Daily batch generation ─────────────────────────────────

async def generate_daily_batch(project_id: str, client_id: str, db: AsyncSession):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        return

    # Hard filter: available, recent login, not on a project, not already swiped
    two_days_ago = datetime.utcnow() - timedelta(days=2)
    query = (
        select(FreelancerProfile)
        .join(User, FreelancerProfile.user_id == User.id)
        .where(
            FreelancerProfile.availability == True,
            User.last_login >= two_days_ago,
            FreelancerProfile.current_project_id.is_(None),
            FreelancerProfile.user_id.notin_(
                select(Swipe.freelancer_id).where(
                    Swipe.client_id == client_id,
                    Swipe.project_id == project_id,
                )
            ),
        )
    )
    result = await db.execute(query)
    candidates = result.scalars().all()

    if not candidates:
        await notify(client_id, "No new matches today. Check back tomorrow.", db)
        return

    candidate_dicts = [
        {
            "user_id": str(c.user_id),
            "headline": c.headline,
            "skills": c.skills or [],
            "interest_areas": c.interest_areas or [],
            "summary": c.summary,
        }
        for c in candidates
    ]

    project_dict = {
        "title": project.title,
        "category": project.category,
        "description": project.description,
        "timeline_value": project.timeline_value,
        "timeline_unit": project.timeline_unit.value if project.timeline_unit else "",
        "written_brief": project.written_brief,
    }

    ranked_ids = await hermes_match_freelancers(project_dict, candidate_dicts, n=10)

    batch = DailyMatchBatch(
        client_id=client_id,
        project_id=project_id,
        batch_date=date.today(),
        freelancer_ids=ranked_ids,
        swiped_ids=[],
        expires_at=datetime.combine(date.today() + timedelta(days=1), dt_time.min),
    )
    db.add(batch)
    await db.commit()

    await notify(client_id, f"Your {len(ranked_ids)} new matches are ready. Start swiping.", db)


# ─── Project status transitions ─────────────────────────────

@router.post("/{project_id}/mark-near-complete")
async def mark_near_complete(
    project_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(404, "Project not found")
    if str(project.assigned_freelancer_id) != str(user.id):
        raise HTTPException(403, "Not your project")
    if project.status != ProjectStatus.IN_PROGRESS:
        raise HTTPException(400, "Project must be IN_PROGRESS")

    project.status = ProjectStatus.NEAR_COMPLETION_REQUESTED
    await db.commit()

    await notify(
        str(project.client_id),
        f"'{project.title}' has been marked near completion. Review and approve or reject.",
        db,
    )
    return {"status": "NEAR_COMPLETION_REQUESTED"}


@router.post("/{project_id}/approve-near-complete")
async def approve_near_complete(
    project_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(404, "Project not found")
    if str(project.client_id) != str(user.id):
        raise HTTPException(403, "Not your project")
    if project.status != ProjectStatus.NEAR_COMPLETION_REQUESTED:
        raise HTTPException(400, "No near-completion request pending")

    project.status = ProjectStatus.NEAR_COMPLETION_APPROVED
    await db.commit()

    await release_payout(
        str(project.assigned_freelancer_id),
        float(project.budget) * 0.5 if project.budget else 0,
        project_id,
        "ADVANCE",
        db,
    )

    await notify(
        str(project.assigned_freelancer_id),
        "Near-completion approved. 50% payment released. Complete and submit final delivery.",
        db,
    )
    return {"status": "NEAR_COMPLETION_APPROVED"}


@router.post("/{project_id}/reject-near-complete")
async def reject_near_complete(
    project_id: str,
    reason: str = "",
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(404)
    if str(project.client_id) != str(user.id):
        raise HTTPException(403)
    if project.status != ProjectStatus.NEAR_COMPLETION_REQUESTED:
        raise HTTPException(400)

    project.status = ProjectStatus.IN_PROGRESS
    await db.commit()

    await notify(
        str(project.assigned_freelancer_id),
        f"Near-completion rejected. Reason: {reason}. Continue working and resubmit.",
        db,
    )
    return {"status": "IN_PROGRESS"}


@router.post("/{project_id}/mark-complete")
async def mark_complete(
    project_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(404)
    if str(project.assigned_freelancer_id) != str(user.id):
        raise HTTPException(403)
    if project.status != ProjectStatus.NEAR_COMPLETION_APPROVED:
        raise HTTPException(400, "Near-completion must be approved first")

    project.status = ProjectStatus.COMPLETED_REQUESTED
    project.revision_window_expires = datetime.utcnow() + timedelta(hours=48)
    await db.commit()

    await notify(
        str(project.client_id),
        f"'{project.title}' is marked complete. You have 48 hours to approve or request changes.",
        db,
    )
    return {"status": "COMPLETED_REQUESTED", "window_expires": str(project.revision_window_expires)}


@router.post("/{project_id}/request-revision")
async def request_revision(
    project_id: str,
    data: RevisionRequestCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(404)
    if str(project.client_id) != str(user.id):
        raise HTTPException(403)

    if project.revision_window_expires and datetime.utcnow() > project.revision_window_expires:
        raise HTTPException(400, "48-hour revision window has expired")
    if project.revision_count >= 3:
        raise HTTPException(400, "Maximum 3 revisions allowed")

    project.revision_count += 1
    project.status = ProjectStatus(f"REVISION_{project.revision_count}")

    revision = RevisionRequest(
        project_id=project_id,
        request_number=project.revision_count,
        note=data.note,
    )
    db.add(revision)
    await db.commit()

    await notify(
        str(project.assigned_freelancer_id),
        f"Revision {project.revision_count}/3 requested: {data.note}",
        db,
    )
    return {"status": project.status.value, "revisions_remaining": 3 - project.revision_count}


@router.post("/{project_id}/approve-complete")
async def approve_complete(
    project_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(404)
    if str(project.client_id) != str(user.id):
        raise HTTPException(403)

    project.status = ProjectStatus.COMPLETED
    await db.commit()

    order, amount = create_upi_order(project, "FINAL")
    await create_payment_record(project_id, "FINAL", amount, order["id"], db)

    await notify(
        str(project.assigned_freelancer_id),
        "Project approved! Final payment is being processed.",
        db,
    )
    return {"order": order}
