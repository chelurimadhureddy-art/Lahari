from django.db import models

class Room(models.Model):
    room_number = models.CharField(max_length=10, unique=True)
    capacity = models.PositiveIntegerField()
    available_slots = models.PositiveIntegerField()

    def __str__(self):
        return self.room_number

    def save(self, *args, **kwargs):
        if self.available_slots > self.capacity:
            self.available_slots = self.capacity
        super().save(*args, **kwargs)
