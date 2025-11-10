"""
데이터베이스 사용 예시
"""
from sqlalchemy.orm import Session
from fastapi import Depends

from common.database import get_db, db_manager, Base
from sqlalchemy import Column, Integer, String


# ============================================
# 1. 모델 정의 예시
# ============================================
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String)


# ============================================
# 2. FastAPI 라우터에서 사용 (권장)
# ============================================
from fastapi import APIRouter

router = APIRouter()


@router.get("/users")
async def get_users(db: Session = Depends(get_db)):
    """의존성 주입 방식 - FastAPI에서 권장"""
    users = db.query(User).all()
    return users


@router.post("/users")
async def create_user(username: str, email: str, db: Session = Depends(get_db)):
    """자동으로 commit/rollback 처리됨"""
    user = User(username=username, email=email)
    db.add(user)
    # db.commit()은 get_db()에서 자동 처리
    db.refresh(user)  # ID 등 새로고침
    return user


# ============================================
# 3. Service/Worker에서 직접 사용
# ============================================
def process_user_data(user_id: int):
    """Worker나 백그라운드 작업에서 사용"""
    with db_manager.session() as db:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.email = "updated@example.com"
            # with 블록 종료시 자동 commit


# ============================================
# 4. 트랜잭션 수동 제어
# ============================================
def manual_transaction_example():
    """수동으로 트랜잭션 제어가 필요한 경우"""
    session = db_manager.session_factory()
    try:
        user1 = User(username="user1", email="user1@example.com")
        user2 = User(username="user2", email="user2@example.com")

        session.add(user1)
        session.add(user2)
        session.commit()

        print("✅ Users created")
    except Exception as e:
        session.rollback()
        print(f"❌ Error: {e}")
    finally:
        session.close()


# ============================================
# 5. 헬스체크
# ============================================
def check_database_connection():
    """데이터베이스 연결 상태 확인"""
    is_healthy = db_manager.health_check()
    if is_healthy:
        print("✅ Database is healthy")
    else:
        print("❌ Database is not responding")


# ============================================
# 6. 테이블 관리 (개발/테스트용)
# ============================================
def init_database():
    """모든 테이블 생성"""
    db_manager.create_all_tables()


def reset_database():
    """모든 테이블 삭제 후 재생성 (주의!)"""
    db_manager.drop_all_tables()
    db_manager.create_all_tables()


# ============================================
# 7. 복잡한 쿼리 예시
# ============================================
@router.get("/users/search")
async def search_users(keyword: str, db: Session = Depends(get_db)):
    """검색 쿼리 예시"""
    users = (
        db.query(User)
        .filter(User.username.contains(keyword))
        .order_by(User.id.desc())
        .limit(10)
        .all()
    )
    return users


@router.get("/users/{user_id}")
async def get_user(user_id: int, db: Session = Depends(get_db)):
    """단일 레코드 조회"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        from common.exceptions import NotFoundException
        raise NotFoundException(f"User {user_id} not found")
    return user


# ============================================
# 8. 벌크 작업
# ============================================
@router.post("/users/bulk")
async def create_bulk_users(usernames: list[str], db: Session = Depends(get_db)):
    """여러 레코드 한번에 생성"""
    users = [User(username=name, email=f"{name}@example.com") for name in usernames]
    db.bulk_save_objects(users)
    # 자동 commit
    return {"created": len(users)}


# ============================================
# 9. Raw SQL 실행
# ============================================
@router.get("/stats")
async def get_stats(db: Session = Depends(get_db)):
    """Raw SQL 쿼리 실행"""
    result = db.execute("SELECT COUNT(*) as total FROM users")
    row = result.fetchone()
    return {"total_users": row.total}
