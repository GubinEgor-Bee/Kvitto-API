class InvalidTransitionError(Exception):
    """Кастомное исключение для запрещенных переходов статуса."""

    pass


class PaymentService:
    # Матрица разрешенных переходов статусов
    ALLOWED_TRANSITIONS = {
        "pending": {"succeeded", "failed"},
        "succeeded": {"refunded"},
        "failed": set(),
        "refunded": set(),
    }

    @staticmethod
    def calculate_discount_and_amount(
        price: int, promo_code: str | None
    ) -> tuple[int, int]:
        """
        Возвращает кортеж: (сумма_к_оплате, размер_скидки).
        Используется строго целочисленная математика (//).
        """
        if promo_code == "KVITTO10":
            discount = price * 10 // 100  # 10% скидка
            amount = price - discount
            return amount, discount
        return price, 0

    @staticmethod
    def calculate_schedule(amount: int, months: int) -> list[int]:
        """
        Разбивает сумму на равные части.
        Лишние копейки добавляются к первым платежам.
        """
        base_payment = amount // months
        remainder = amount % months

        schedule = []
        for i in range(months):
            if i < remainder:
                schedule.append(base_payment + 1)
            else:
                schedule.append(base_payment)

        return schedule

    @classmethod
    def check_status_transition(cls, current_status: str, new_status: str) -> None:
        """
        Проверяет, возможен ли переход. Если нет — рейзит ошибку.
        """
        if new_status not in cls.ALLOWED_TRANSITIONS.get(current_status, set()):
            raise InvalidTransitionError("invalid_transition")
