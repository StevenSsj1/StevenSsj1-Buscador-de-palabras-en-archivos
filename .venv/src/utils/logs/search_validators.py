from fastapi import status
from .error_handling import AppException

class SearchValidator:
    @staticmethod
    def validate_operator(operator: str):
        if operator.upper() not in ["AND", "OR"]:
            raise AppException(
                message="Operador inválido",
                status_code=status.HTTP_400_BAD_REQUEST,
                extra={"valid_operators": ["AND", "OR"]}
            )

    @staticmethod
    def validate_fuzziness(fuzziness: str):
        if fuzziness not in ["AUTO", "0", "1", "2"]:
            raise AppException(
                message="Valor de fuzziness inválido",
                status_code=status.HTTP_400_BAD_REQUEST,
                extra={"valid_fuzziness": ["AUTO", "0", "1", "2"]}
            )