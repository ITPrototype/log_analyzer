from django import forms
from .models import UploadedLog, Source

class UploadForm(forms.ModelForm):
    class Meta:
        model = UploadedLog
        fields = ['file']
