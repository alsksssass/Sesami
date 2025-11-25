from config import settings
from fastapi import Depends
from sqlalchemy.orm import Session
import boto3

from common.database import get_db
from config import settings

from .analysis_service import AnalysisService

_boto3_client = None

def get_analysis_service(db: Session = Depends(get_db)):
    global _boto3_client
    if _boto3_client is None:
        _boto3_client = boto3.client('batch', region_name=settings.AWS_REGION)
    return AnalysisService(db, _boto3_client)