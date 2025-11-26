from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from common.database import get_db
from common.exceptions import UnauthorizedException
from common.graph_service import IGraphService, LocalGraphService
from common.vector_service import IVectorService, LocalVectorService
from common.task_service import ITaskService, LocalTaskService
from config import settings

# OAuth2 Bearer 스킴
security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    현재 로그인한 사용자 가져오기

    JWT 토큰을 검증하고 해당 사용자를 반환합니다.

    Args:
        credentials: HTTP Bearer 토큰
        db: 데이터베이스 세션

    Returns:
        User: 인증된 사용자 객체

    Raises:
        UnauthorizedException: 토큰이 유효하지 않거나 사용자가 존재하지 않음
    """
    # 순환 import 방지를 위해 함수 내부에서 import
    from features.v1.auth.jwt_service import JWTService
    from features.v1.auth.models import User

    # JWT 토큰에서 사용자 ID 추출
    token = credentials.credentials
    user_id = JWTService.get_user_id_from_token(token)

    # 데이터베이스에서 사용자 조회
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise UnauthorizedException("User not found")

    return user


def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False)),
    db: Session = Depends(get_db)
):
    """
    선택적 인증 (토큰이 없어도 통과)

    Args:
        credentials: HTTP Bearer 토큰 (선택사항)
        db: 데이터베이스 세션

    Returns:
        User | None: 인증된 사용자 또는 None
    """
    if credentials is None:
        return None

    try:
        return get_current_user(credentials, db)
    except Exception:
        return None


def require_admin(current_user=Depends(get_current_user)):
    """
    관리자 권한 필요

    Args:
        current_user: 현재 사용자

    Raises:
        HTTPException: 관리자 권한이 없음

    TODO: User 모델에 is_admin 필드 추가 후 구현
    """
    # TODO: 관리자 권한 검증 로직 추가
    # if not current_user.is_admin:
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="Admin access required"
    #     )
    pass


# Graph Service 싱글톤 인스턴스
_graph_service: IGraphService = None


# def get_graph_service() -> IGraphService:
#     """환경에 따라 적절한 GraphService 반환

#     로컬 환경: LocalGraphService (Neo4j Community)
#     AWS 환경: AwsGraphService (Neo4j AuraDB 또는 Neptune) - 추후 구현

#     Returns:
#         IGraphService: 그래프 데이터베이스 서비스 인스턴스
#     """
#     global _graph_service

#     if _graph_service is None:
#         if settings.TASK_SERVICE_IMPL == "AWS_BATCH":
#             # TODO: AWS 환경 구현 (Phase 3)
#             # from common.graph_service.aws_service import AwsGraphService
#             # _graph_service = AwsGraphService(...)
#             raise NotImplementedError("AWS GraphService is not implemented yet")
#         else:
#             # 로컬 환경: Neo4j Community
#             _graph_service = LocalGraphService(
#                 uri=settings.NEO4J_URI,
#                 user=settings.NEO4J_USER,
#                 password=settings.NEO4J_PASSWORD
#             )

#     return _graph_service


# # Vector Service 싱글톤 인스턴스
# _vector_service: IVectorService = None


# def get_vector_service() -> IVectorService:
#     """환경에 따라 적절한 VectorService 반환

#     로컬 환경: LocalVectorService (OpenSearch)
#     AWS 환경: AwsVectorService (OpenSearch Serverless) - 추후 구현

#     Returns:
#         IVectorService: 벡터 데이터베이스 서비스 인스턴스
#     """
#     global _vector_service

#     if _vector_service is None:
#         if settings.TASK_SERVICE_IMPL == "AWS_BATCH":
#             # TODO: AWS 환경 구현 (Phase 3)
#             # from common.vector_service.aws_service import AwsVectorService
#             # _vector_service = AwsVectorService(...)
#             raise NotImplementedError("AWS VectorService is not implemented yet")
#         else:
#             # 로컬 환경: OpenSearch
#             _vector_service = LocalVectorService(
#                 endpoint=settings.OPENSEARCH_ENDPOINT,
#                 user=settings.OPENSEARCH_USER,
#                 password=settings.OPENSEARCH_PASSWORD,
#                 default_index=settings.OPENSEARCH_INDEX_NAME
#             )

#     return _vector_service


# # Task Service 싱글톤 인스턴스
# _task_service: ITaskService = None


# def get_task_service() -> ITaskService:
#     """환경에 따라 적절한 TaskService 반환

#     로컬 환경: LocalTaskService (Celery + Redis)
#     AWS 환경: AwsBatchTaskService (Step Functions + SQS + Batch)

#     Returns:
#         ITaskService: 작업 큐 서비스 인스턴스
#     """
#     global _task_service

#     if _task_service is None:
#         if settings.TASK_SERVICE_IMPL == "AWS_BATCH":
#             # AWS 환경: Step Functions + Batch
#             from common.task_service.aws_batch_service import AwsBatchTaskService
#             _task_service = AwsBatchTaskService()
#         else:
#             # 로컬 환경: Celery + Redis
#             _task_service = LocalTaskService(
#                 broker_url=settings.CELERY_BROKER_URL,
#                 result_backend=settings.CELERY_RESULT_BACKEND
#             )

#     return _task_service
