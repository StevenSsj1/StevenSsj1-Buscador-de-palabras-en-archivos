from fastapi import HTTPException, status
from functools import wraps
import logging
import json
import traceback
from datetime import datetime
from typing import Any, Dict, Optional

class CustomLogger:
    def __init__(self, name: str, log_file: str = 'application.log'):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Formato personalizado con información del usuario
        formatter = logging.Formatter(
            '%(asctime)s - [%(levelname)s] - User: %(user)s - %(name)s - %(message)s'
        )
        
        # Handler para archivo
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        # Handler para consola
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

    def _get_extra(self, user: str = "Client") -> Dict[str, Any]:
        return {
            "user": user,
            "timestamp": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        }

    def info(self, message: str, extra: dict = None, user: str = "Client"):
        extra_info = self._get_extra(user)
        if extra:
            extra_info.update(extra)
        self.logger.info(f"{message} - {json.dumps(extra_info)}", extra={"user": user})

    def error(self, message: str, error: Exception = None, user: str = "Client"):
        extra_info = self._get_extra(user)
        if error:
            error_details = {
                "error_type": type(error).__name__,
                "error_message": str(error),
                "traceback": traceback.format_exc()
            }
            extra_info.update(error_details)
        self.logger.error(f"{message} - {json.dumps(extra_info)}", extra={"user": user})

    def warning(self, message: str, extra: dict = None, user: str = "Client"):
        extra_info = self._get_extra(user)
        if extra:
            extra_info.update(extra)
        self.logger.warning(f"{message} - {json.dumps(extra_info)}", extra={"user": user})

class AppException(Exception):
    def __init__(
        self, 
        message: str, 
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        extra: Optional[Dict] = None
    ):
        self.message = message
        self.status_code = status_code
        self.extra = extra or {}
        super().__init__(self.message)

def handle_exceptions(logger: CustomLogger):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except AppException as ae:
                logger.error(
                    f"Error de aplicación: {ae.message}",
                    error=ae,
                )
                raise HTTPException(
                    status_code=ae.status_code,
                    detail={
                        "message": ae.message,
                        "extra": ae.extra
                    }
                )
            except HTTPException as he:
                # Reenviar excepciones HTTP de FastAPI
                raise he
            except Exception as e:
                logger.error(
                    "Error inesperado en la aplicación",
                    error=e,
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Error interno del servidor"
                )
        return wrapper
    return decorator