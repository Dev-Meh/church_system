from django import forms
from django.utils import timezone
from .models import Sermon, SermonSeries, SermonCategory
from members.models import ChurchUser

class SermonSeriesForm(forms.ModelForm):
    class Meta:
        model = SermonSeries
        fields = ['title', 'description', 'speaker', 'start_date', 'end_date', 'cover_image', 'is_active']
        widgets = {
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['speaker'].queryset = ChurchUser.objects.filter(
            role__in=['pastor', 'elder', 'deacon']
        )

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if end_date and start_date and end_date < start_date:
            raise forms.ValidationError("End date must be after start date.")

        return cleaned_data

class SermonForm(forms.ModelForm):
    class Meta:
        model = Sermon
        fields = [
            'title', 'description', 'speaker', 'series', 'sermon_date', 'sermon_type',
            'bible_references', 'audio_file', 'video_file', 'transcript', 'notes',
            'slides', 'thumbnail', 'duration', 'is_published', 'is_featured'
        ]
        widgets = {
            'sermon_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'bible_references': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'transcript': forms.Textarea(attrs={'rows': 6, 'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'duration': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['speaker'].queryset = ChurchUser.objects.filter(
            role__in=['pastor', 'elder', 'deacon']
        )
        self.fields['series'].queryset = SermonSeries.objects.filter(is_active=True)

    def clean(self):
        cleaned_data = super().clean()
        audio_file = cleaned_data.get('audio_file')
        video_file = cleaned_data.get('video_file')

        if not audio_file and not video_file:
            raise forms.ValidationError("Either audio file or video file is required.")

        return cleaned_data

class SermonCategoryForm(forms.ModelForm):
    class Meta:
        model = SermonCategory
        fields = ['name', 'description', 'color', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
        }

class SermonSearchForm(forms.Form):
    query = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search sermons...'
        })
    )
    speaker = forms.ModelChoiceField(
        queryset=ChurchUser.objects.filter(role__in=['pastor', 'elder', 'deacon']),
        required=False,
        empty_label="All Speakers",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    series = forms.ModelChoiceField(
        queryset=SermonSeries.objects.filter(is_active=True),
        required=False,
        empty_label="All Series",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    category = forms.ModelChoiceField(
        queryset=SermonCategory.objects.filter(is_active=True),
        required=False,
        empty_label="All Categories",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    sermon_type = forms.ChoiceField(
        choices=[('', 'All Types')] + Sermon.SERMON_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
