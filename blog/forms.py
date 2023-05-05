from django import forms


class ContactUsForm(forms.Form):
    name = forms.CharField(max_length=50, required=True)
    email = forms.EmailField(required=True)
    subject = forms.CharField(max_length=150, required=True)
    text = forms.CharField(widget=forms.Textarea, max_length=1000, required=True)
