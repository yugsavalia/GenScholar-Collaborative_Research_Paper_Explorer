from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import PDFFile  
from .tasks import process_pdf_task  # Import our new task

@receiver(post_save, sender=PDFFile) 
def schedule_pdf_processing(sender, instance, created, **kwargs):
    """
    When a new PDFFile is created (on upload),
    schedule the background task to process it.
    """
    if created:
        print(f"New PDFFile created (ID: {instance.id}). Scheduling processing task.")
        # This is the magic: it adds the task to the database queue
        # It will run as soon as 'python manage.py process_tasks' is running
        process_pdf_task(instance.id)