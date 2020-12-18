from django import forms


class FileForm(forms.Form):
    title = forms.CharField(required=False)
    type = forms.IntegerField(required=True)
    file = forms.FileField(required=True)
