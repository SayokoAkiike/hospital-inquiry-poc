import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr

from app.models.user import UserRole


class UserCreate(BaseModel):
    """
    自己登録（POST /auth/register）用スキーマ。

    意図的に role フィールドを持たない。
    一般ユーザーが自分でADMIN/NURSE/DOCTORを名乗れてしまう
    権限昇格（role escalation）を防ぐため。
    register エンドポイントでは常に UserRole.PATIENT を割り当てる。
    医療スタッフ・管理者アカウントは、別途管理者が作成する運用を想定。
    """
    email: EmailStr
    password: str
    full_name: str


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
