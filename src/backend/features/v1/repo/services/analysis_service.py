from sqlalchemy.orm import Session
from fastapi import Depends

from uuid import UUID

from features.v1.repo.schemas import RepositoryAnalysisResponse
from features.v1.repo.models import RepositoryAnalysis

from datetime import datetime

class AnalysisService():
    def __init__(self, db: Session, batch_client):
        self.db = db
        self.client = batch_client
        
    def request_analysis(self, user_id: UUID, urls: list[str], analysis_id: UUID, repo_ids: list[UUID]):
        jobName = 'deep-agents-' + datetime.now().strftime("%Y%m%d-%H%M%S")
        response = self.client.submit_job(jobName=jobName, jobQueue='deep-agents-queue',
            jobDefinition='arn:aws:batch:ap-northeast-2:712111072528:job-definition/deep-agents-job:39',
            containerOverrides={
                'environment': [
                    {
                        'name': 'GIT_URLS',
                        'value': ','.join(urls)
                    },
                    {
                        'name': 'USER_ID',
                        'value': str(user_id)
                    },
                    {
                        'name': 'MAIN_TASK_ID',
                        'value': str(analysis_id)
                    },
                    {
                        'name': 'TASK_IDS',
                        'value': ','.join(str(repo_id) for repo_id in repo_ids)
                    }
                ]
            }
        )
        
        return response