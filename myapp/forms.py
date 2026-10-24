from django import forms

from .models import ForumPost


class ForumPostForm(forms.ModelForm):
    class Meta:
        model = ForumPost
        fields = ["title", "content"]
        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": (
                        "block w-full rounded-lg border border-slate-300 px-3 py-2 "
                        "text-sm focus:border-brand-500 focus:outline-none "
                        "focus:ring-1 focus:ring-brand-500"
                    ),
                    "placeholder": "Give your discussion a title",
                    "maxlength": 200,
                }
            ),
            "content": forms.Textarea(
                attrs={
                    "class": (
                        "block w-full rounded-lg border border-slate-300 px-3 py-2 "
                        "text-sm focus:border-brand-500 focus:outline-none "
                        "focus:ring-1 focus:ring-brand-500"
                    ),
                    "placeholder": "What would you like to discuss?",
                    "rows": 5,
                }
            ),
        }
