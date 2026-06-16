import anthropic

from app.core.config import settings
from app.models.ticket import AICategory, TicketPriority


async def classify_ticket(title: str, description: str) -> tuple[AICategory, TicketPriority]:
    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    prompt = f"""以下の病院への問い合わせを分類してください。

タイトル: {title}
内容: {description}

以下のJSON形式のみで回答してください（説明不要）:
{{
  "category": "Appointment|Medication|SideEffect|Billing|Treatment|Other",
  "urgency": "LOW|NORMAL|HIGH|URGENT"
}}

urgencyの基準:
- URGENT: 生命に関わる症状、重篤な副作用
- HIGH: 強い痛み、急な症状悪化
- NORMAL: 一般的な問い合わせ
- LOW: 書類・請求関連"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=100,
        messages=[{"role": "user", "content": prompt}],
    )

    import json
    result = json.loads(message.content[0].text)
    category = AICategory(result["category"])
    urgency = TicketPriority(result["urgency"])
    return category, urgency
