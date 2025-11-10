from common.task_service import ITaskService, LocalTaskService
from config import settings


def get_task_service() -> ITaskService:
    """환경에 따라 적절한 TaskService 반환

    로컬 환경: LocalTaskService (Redis + Celery)
    AWS 환경: AwsTaskService (SQS + Batch) - 추후 구현
    """
    if settings.TASK_SERVICE_TYPE == "aws":
        # TODO: AWS 환경 구현
        # from common.task_service.aws_service import AwsTaskService
        # return AwsTaskService(...)
        raise NotImplementedError("AWS TaskService is not implemented yet")
    else:
        # 로컬 환경: Celery 앱 import
        from worker.celery_app import celery_app
        return LocalTaskService(celery_app=celery_app)
