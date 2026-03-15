from django.db import models

class Medicine(models.Model):
    # Existing fields
    name              = models.CharField(max_length=200)
    name_hebrew       = models.CharField(max_length=200, blank=True, null=True)
    quantity          = models.PositiveIntegerField(default=0)

    # New fields
    expiry_date       = models.DateField(blank=True, null=True)
    min_age           = models.PositiveIntegerField(blank=True, null=True)
    suitable_pregnant = models.BooleanField(default=False)

    def __str__(self):
        if self.name_hebrew:
            return f"{self.name} | {self.name_hebrew} — {self.quantity} units"
        return f"{self.name} — {self.quantity} units"

    def is_available(self):
        return self.quantity > 0

    def is_expired(self):
        from django.utils import timezone
        if self.expiry_date:
            return self.expiry_date < timezone.now().date()
        return False


class Visitor(models.Model):
    phone      = models.CharField(max_length=50, unique=True)
    first_seen = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.phone


class MissedRequest(models.Model):
    medicine_searched = models.CharField(max_length=200)
    requester_phone   = models.CharField(max_length=50)
    date              = models.DateTimeField(auto_now_add=True)
    suggestion_given  = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return f"{self.medicine_searched} — {self.requester_phone} — {self.date.strftime('%d/%m/%Y %H:%M')}"

    class Meta:
        ordering = ['-date']