from abc import ABC, abstractmethod


class EmailProvider(ABC):
    @abstractmethod
    async def send_otp(self, email: str, code: str) -> bool:
        """Sends a 6-digit numeric OTP to the recipient email."""
        pass
