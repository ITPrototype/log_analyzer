from django.db import models

# Create your models here.
class Source(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name
    

class LogEntry(models.Model):
    source = models.ForeignKey(Source,on_delete=models.SET_NULL,null=True,blank=True)
    remote_addr = models.CharField(max_length=45)  # Supports IPv6
    remote_user = models.CharField(max_length=200, blank=True,null=True)
    timestamp = models.DateTimeField()
    request_method = models.CharField(max_length=10,blank=True,null=True)
    request_path = models.TextField(blank=True)
    protocol = models.CharField(max_length=20, blank=True,null=True)
    status = models.PositiveBigIntegerField()
    body_bytes_sent = models.PositiveBigIntegerField(null=True,blank=True)
    referer = models.TextField(blank=True,null=True)
    user_agent = models.TextField(blank=True,null=True)
    raw_line = models.TextField(blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['remote_addr']),
            models.Index(fields=['status']),
            models.Index(fields=['timestamp']),
        ]
    
    def __str__(self):
        return f"{self.remote_addr} - {self.request_method} {self.request_path} [{self.timestamp}] {self.status}"
    

class UploadedLog(models.Model):
    source = models.ForeignKey(Source, on_delete=models.CASCADE)
    file = models.FileField(upload_to='media/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)
    total_imported = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.file.name} ({'processed' if self.processed else 'pending'})"
