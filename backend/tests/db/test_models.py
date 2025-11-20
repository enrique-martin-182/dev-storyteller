import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.db.database import Base
from src.db.models import AnalysisResult, Repository, User
from src.core.enums import AnalysisStatus

# Setup in-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(name="session")
def session_fixture():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def test_user_model(session):
    user = User(username="testuser", hashed_password="hashedpassword")
    session.add(user)
    session.commit()
    session.refresh(user)

    assert user.id is not None
    assert user.username == "testuser"
    assert user.hashed_password == "hashedpassword"


def test_repository_model(session):
    user = User(username="testuser", hashed_password="hashedpassword")
    session.add(user)
    session.commit()
    session.refresh(user)

    repository = Repository(url="https://github.com/test/repo", name="test/repo", owner_id=user.id)
    session.add(repository)
    session.commit()
    session.refresh(repository)

    assert repository.id is not None
    assert repository.url == "https://github.com/test/repo"
    assert repository.name == "test/repo"
    assert repository.owner_id == user.id
    assert repository.status == AnalysisStatus.PENDING
    assert repository.created_at is not None
    assert repository.owner.username == "testuser"


def test_analysis_result_model(session):
    user = User(username="testuser", hashed_password="hashedpassword")
    session.add(user)
    session.commit()
    session.refresh(user)

    repository = Repository(url="https://github.com/test/repo", name="test/repo", owner_id=user.id)
    session.add(repository)
    session.commit()
    session.refresh(repository)

    analysis_result = AnalysisResult(
        repository_id=repository.id,
        summary="Test summary",
        narrative="Test narrative",
        open_issues_count=5,
        open_pull_requests_count=2,
        contributors=[{"name": "test", "contributions": 10}],
        file_count=100,
        total_lines=1000,
        commit_count=50,
        languages={"Python": 100},
        tech_stack=["Python", "FastAPI"],
        report_url="http://example.com/report",
        status=AnalysisStatus.COMPLETED
    )
    session.add(analysis_result)
    session.commit()
    session.refresh(analysis_result)

    assert analysis_result.id is not None
    assert analysis_result.repository_id == repository.id
    assert analysis_result.summary == "Test summary"
    assert analysis_result.narrative == "Test narrative"
    assert analysis_result.open_issues_count == 5
    assert analysis_result.open_pull_requests_count == 2
    assert analysis_result.contributors == [{"name": "test", "contributions": 10}]
    assert analysis_result.file_count == 100
    assert analysis_result.total_lines == 1000
    assert analysis_result.commit_count == 50
    assert analysis_result.languages == {"Python": 100}
    assert analysis_result.tech_stack == ["Python", "FastAPI"]
    assert analysis_result.report_url == "http://example.com/report"
    assert analysis_result.status == AnalysisStatus.COMPLETED
    assert analysis_result.created_at is not None
    assert analysis_result.repository.name == "test/repo"