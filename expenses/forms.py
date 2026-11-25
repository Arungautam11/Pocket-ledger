from django import forms
from .models import AppSettings, Category, Transaction


class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ["kind", "description", "amount", "date", "category", "payment_method"]
        widgets = {"date": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, *args, kind=None, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        if kind:
            self.fields["kind"].initial = kind
            self.fields["kind"].widget = forms.HiddenInput()
            self.fields["category"].queryset = Category.objects.filter(kind=kind, user=user)
        else:
            self.fields["category"].queryset = Category.objects.filter(user=user)

    def clean(self):
        cleaned = super().clean()
        category, kind = cleaned.get("category"), cleaned.get("kind")
        if category and kind and category.kind != kind:
            self.add_error("category", "Choose a category for this transaction type.")
        return cleaned


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name", "kind"]

    def clean_name(self):
        name = self.cleaned_data["name"].strip()
        kind = self.data.get("kind", self.instance.kind if self.instance.pk else "expense")
        query = Category.objects.filter(name__iexact=name, kind=kind, user=self.user)
        if self.instance.pk:
            query = query.exclude(pk=self.instance.pk)
        if query.exists():
            raise forms.ValidationError("A category with this name already exists.")
        return name

    def clean_kind(self):
        kind = self.cleaned_data["kind"]
        if self.instance.pk and kind != self.instance.kind and self.instance.transactions.exists():
            raise forms.ValidationError("The type cannot change while this category is used by transactions.")
        return kind

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)


class PreferencesForm(forms.ModelForm):
    class Meta:
        model = AppSettings
        fields = ["currency"]
