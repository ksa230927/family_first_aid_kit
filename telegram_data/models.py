from django.db import models


class TelegramMessage(models.Model):
    message_id = models.CharField(max_length=255)
    user_id = models.CharField(max_length=255)
    text = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    # Новые поля для хранения информации о лекарствах
    medicine_name = models.CharField(max_length=255, null=True, blank=True)  # Наименование лекарства
    expiry_date = models.DateField(null=True, blank=True)  # Срок годности лекарства

    def __str__(self):
        return f"Message from {self.user_id} at {self.timestamp} - Medicine: {self.medicine_name or 'N/A'}"


