from pydantic import BaseModel
import typing as t

class LoginRequest(BaseModel):
    addresses: t.List[str]


class LoginRequestWebResponse(BaseModel):
    address: str
    signingMessage: str
    tokenUrl: str


class LoginRequestMobileResponse(BaseModel):
    address: str
    verificationId: str
    signingRequestUrl: str


class ErgoAuthRequest(BaseModel):
    address: str
    signingMessage: str
    sigmaBoolean: str
    userMessage: str = "sign this message using your wallet to approve authenticate paideia.im"
    messageSeverity: str = "INFORMATION"
    replyTo: str


class ErgoAuthResponse(BaseModel):
    signedMessage: str
    proof: str
