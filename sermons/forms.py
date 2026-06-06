from django import forms
from django.utils import timezone

from members.models import ChurchUser

from .models import Sermon, SermonSeries, SermonCategory


class SermonSeriesForm(forms.ModelForm):
    class Meta:
        model = SermonSeries
        fields = [
            'title', 'description', 'speaker', 'start_date', 'end_date',
            'cover_image', 'is_active',
        ]
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['speaker'].queryset = ChurchUser.objects.filter(
            role__in=['pastor', 'admin', 'elder', 'deacon']
        )
        self._style_fields()

    def _style_fields(self):
        for field in self.fields.values():
            css = field.widget.attrs.get('class', '')
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = f'{css} form-check-input'.strip()
            else:
                field.widget.attrs['class'] = f'{css} form-control'.strip()

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if end_date and start_date and end_date < start_date:
            raise forms.ValidationError('Tarehe ya mwisho lazima iwe baada ya tarehe ya kuanza.')

        return cleaned_data


class SermonForm(forms.ModelForm):
    class Meta:
        model = Sermon
        fields = [
            'title',
            'description',
            'bible_references',
            'notes',
            'sermon_date',
            'audio_file',
            'video_file',
            'slides',
            'thumbnail',
            'is_published',
            'is_featured',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 6}),
            'bible_references': forms.Textarea(attrs={'rows': 2}),
            'notes': forms.Textarea(attrs={'rows': 4}),
            'sermon_date': forms.DateTimeInput(
                attrs={'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M',
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['title'].widget.attrs['placeholder'] = 'Mfano: Nguvu ya Maombi ya Asubuhi'
        self.fields['description'].widget.attrs['placeholder'] = (
            'Andika mahubiri mafupi kwa lugha rahisi na inayoeleweka kwa waumini wote.'
        )
        self.fields['notes'].widget.attrs['placeholder'] = (
            'Hitimisho au ujumbe wa kuchukua nyumbani (hiari).'
        )
        self.fields['audio_file'].required = False
        self.fields['audio_file'].widget.attrs['accept'] = 'audio/*,.webm,.ogg,.mp3,.wav,.m4a'
        self.fields['video_file'].required = False
        self.fields['video_file'].widget.attrs['accept'] = 'video/*,.mp4,.webm,.mov,.mkv'
        self.fields['slides'].required = False
        self.fields['thumbnail'].required = False

        if not self.instance.pk:
            self.fields['is_published'].initial = True
            self.fields['sermon_date'].initial = timezone.localtime().strftime('%Y-%m-%dT%H:%M')

        self.fields['sermon_date'].input_formats = [
            '%Y-%m-%dT%H:%M',
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d %H:%M',
        ]

        self._style_fields()

    def _style_fields(self):
        for name, field in self.fields.items():
            css = field.widget.attrs.get('class', '')
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = f'{css} form-check-input'.strip()
            elif isinstance(field.widget, forms.ClearableFileInput):
                field.widget.attrs['class'] = f'{css} form-control'.strip()
            else:
                field.widget.attrs['class'] = f'{css} form-control'.strip()

    def clean_description(self):
        description = (self.cleaned_data.get('description') or '').strip()
        if not description:
            raise forms.ValidationError('Maelezo ya hubo yanahitajika.')
        if len(description) > 12000:
            raise forms.ValidationError('Mahubiri ni marefu sana — fupisha kidogo.')
        return description

    def clean_bible_references(self):
        return (self.cleaned_data.get('bible_references') or '').strip()


class SermonCategoryForm(forms.ModelForm):
    class Meta:
        model = SermonCategory
        fields = ['name', 'description', 'color', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'color': forms.TextInput(attrs={'type': 'color'}),
        }


class SermonSearchForm(forms.Form):
    query = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Tafuta mahubiri...',
        }),
    )
    speaker = forms.ModelChoiceField(
        queryset=ChurchUser.objects.filter(role__in=['pastor', 'elder', 'deacon', 'admin']),
        required=False,
        empty_label='Wahubiri wote',
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    series = forms.ModelChoiceField(
        queryset=SermonSeries.objects.filter(is_active=True),
        required=False,
        empty_label='Mfululizo wote',
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    category = forms.ModelChoiceField(
        queryset=SermonCategory.objects.filter(is_active=True),
        required=False,
        empty_label='Kategoria zote',
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    sermon_type = forms.ChoiceField(
        choices=[('', 'Aina zote')] + Sermon.SERMON_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
    )
