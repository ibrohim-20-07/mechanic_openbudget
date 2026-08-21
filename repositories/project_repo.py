from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.project import Project


async def get_active_project(session: AsyncSession) -> Project | None:
    result = await session.execute(select(Project).where(Project.is_active.is_(True)))
    return result.scalar_one_or_none()


async def list_projects(session: AsyncSession, include_deleted: bool = False) -> list[Project]:
    stmt = select(Project).order_by(Project.queue_order)
    if not include_deleted:
        stmt = stmt.where(Project.is_deleted.is_(False))
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_next_queue_order(session: AsyncSession) -> int:
    result = await session.execute(select(Project.queue_order).order_by(Project.queue_order.desc()))
    last = result.scalars().first()
    return (last or 0) + 1


async def get_by_id_for_update(session: AsyncSession, project_id: int) -> Project | None:
    stmt = select(Project).where(Project.id == project_id).with_for_update()
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_by_id(session: AsyncSession, project_id: int) -> Project | None:
    return await session.get(Project, project_id)


async def get_neighbor(session: AsyncSession, project: Project, direction: str) -> Project | None:
    """direction: 'up' = the project just before it in queue order, 'down' = just after."""
    stmt = select(Project).where(Project.is_deleted.is_(False), Project.id != project.id)
    if direction == "up":
        stmt = stmt.where(Project.queue_order < project.queue_order).order_by(
            Project.queue_order.desc()
        )
    else:
        stmt = stmt.where(Project.queue_order > project.queue_order).order_by(
            Project.queue_order.asc()
        )
    result = await session.execute(stmt.limit(1))
    return result.scalar_one_or_none()


async def get_next_in_queue(session: AsyncSession, exclude_project_id: int) -> Project | None:
    stmt = (
        select(Project)
        .where(
            Project.is_deleted.is_(False),
            Project.is_active.is_(False),
            Project.id != exclude_project_id,
        )
        .order_by(Project.queue_order.asc())
        .limit(1)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()
