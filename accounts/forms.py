from django import forms


class CustomSignupForm(forms.Form):
    last_name = forms.CharField(max_length=30, required=True)
    first_name = forms.CharField(max_length=30, required=True)
    phone = forms.CharField(max_length=20, required=False)

    def signup(self, request, user):
        user.last_name = self.cleaned_data["last_name"]
        user.first_name = self.cleaned_data["first_name"]
        user.phone = self.cleaned_data.get("phone", "")
        user.save(update_fields=["last_name", "first_name", "phone"])
