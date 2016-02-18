from django import forms
from django.contrib.auth.models import User
from django.utils.safestring import mark_safe

from django_countries.fields import CountryField
from django_countries.widgets import CountrySelectWidget

from datetime import *
from accounts.models import *

import os

from file_resubmit.admin import AdminResubmitImageWidget, AdminResubmitFileWidget
from django.forms.fields import DateField



IS_PERMANENT_ADDRESS = (
        ('1', 'Same as Current Residence Address'),
        ('2', 'No')
    )


class KYCForm(forms.ModelForm):

	# residence_address = forms.CharField(max_length = 200, label='Current Residence Address')
	# city = forms.CharField(max_length = 50, required=False)
	# pin_code = forms.CharField(max_length = 50, required=False)
	# state = forms.CharField(max_length = 50, required=False)
	# nationality1 = forms.CharField(max_length = 50, required=False, label='Country')

	contact_details_tel = forms.CharField(max_length = 10, required = False)
	contact_details_mobile = forms.CharField(max_length = 13)
	contact_details_fax = forms.CharField(max_length = 50, required=False)
	contact_details_email = forms.CharField(max_length = 50, required=False)

	permanent_address = forms.CharField(max_length = 200, required=False)
	city1 = forms.CharField(max_length = 50, required=False)
	pin_code1 = forms.CharField(max_length = 50, required=False)
	state1 = forms.CharField(max_length = 50, required=False)
	country1 = forms.CharField(max_length = 50, required=False)

	

	class Meta:
		model = KYCInformation
		exclude = ('user', 'status', 'contact_details', 'permanent_address')
		widgets = {
            'dob'							:   forms.DateInput     (format='%d/%m/%Y'),
            'date'							:   forms.DateInput     (format='%d/%m/%Y'),
            'net_word_date'					:	forms.DateInput     (format='%d/%m/%Y'),
            'is_permanent_address'			:	forms.RadioSelect(),
            'first_name'					:	forms.TextInput(attrs={'placeholder': 'First Name'}),
            'middle_name'					:	forms.TextInput(attrs={'placeholder': 'Middle Name'}),
            'last_name'						:	forms.TextInput(attrs={'placeholder': 'Last Name'}),
            'photograph'					:	AdminResubmitImageWidget,
            'pan_card_file'					:	AdminResubmitFileWidget,
            'signature'						:	AdminResubmitFileWidget,
            'proff_identity_file'			:	AdminResubmitFileWidget,
            'address_submitted_for_residece_file': AdminResubmitFileWidget,
            'proof_of_address_non_residence_file': AdminResubmitFileWidget,
            }

	def __init__(self, *args, **kwargs):
		self.user = kwargs.pop('user', None)
		super(KYCForm, self).__init__(*args, **kwargs)
		self.fields['dob'].widget.format = '%d/%m/%Y'
		self.fields['dob'].input_formats = ['%d/%m/%Y']
		self.fields["date"].initial = date.today()
		self.fields['other_occupation'].widget.attrs.update({'placeholder' : 'Add Your Occupation Here'})
		# self.fields['residence_address'].initial = 
		for field_name in self.fields:
			field = self.fields.get(field_name)
			if field:
				field.widget.attrs.update({'class' : 'form-control'})



	def clean_contact_details_mobile(self):
		get_contact_details_mobile = self.cleaned_data['contact_details_mobile']
		if get_contact_details_mobile and len(get_contact_details_mobile) < 13:
			raise forms.ValidationError(u'Please Enter Valid Mobile Phone Number.')
		return get_contact_details_mobile


	def clean_contact_details_tel(self):
		get_contact_details_tel = self.cleaned_data['contact_details_tel']
		if get_contact_details_tel and len(get_contact_details_tel) < 10:
			raise forms.ValidationError(u'Please Enter Valid Phone Number.')
		return get_contact_details_tel	


	def clean_pan_card(self):
		get_pan_card = self.cleaned_data.get('pan_card')

		if get_pan_card:
			# if get_pan_card and KYCInformation.objects.filter(pan_card=get_pan_card).count() > 0:
			# 	raise forms.ValidationError(u'Please Use Different PAN CARD.')

			if len(get_pan_card) < 10:
				raise forms.ValidationError(u'Please Enter Valid PAN Card Digit. (10 character)')

			if not get_pan_card[:4].isalpha():
				raise forms.ValidationError(u'Please Enter Valid PAN Card. ( from 1-5 must be letter)')

			if not get_pan_card[5:8].isdigit():
				raise forms.ValidationError(u'Please Enter Valid PAN Card. ( from 6-9 must be number)')

			if get_pan_card[3] != 'P':
				raise forms.ValidationError(u'Please Enter Valid PAN Card. ( character number 4 must be "P")')

			if not get_pan_card[9].isalpha():
				raise forms.ValidationError(u'Please Enter Valid PAN Card. ( last character must be letter )')

			if get_pan_card and len(get_pan_card) != 10:
				raise forms.ValidationError(u'Please Enter Valid PAN Card Digit.')
		return get_pan_card


	def clean_pan_card_file(self):
		if self.cleaned_data.get('pan_card') and not self.cleaned_data.get('pan_card_file'):
			raise forms.ValidationError(u'Please Insert Your Pan Card Documens.')

		# try:
			if self.cleaned_data.get('pan_card_file') and self.cleaned_data.get('pan_card_file').content_type.split('/')[1] not in ['jpg', 'png', 'pdf']:
				raise forms.ValidationError(u'Please Upload Valid File.')

			if not self.cleaned_data.get('pan_card') and not self.cleaned_data.get('addhar_number') and not self.cleaned_data.get('passport') and not self.cleaned_data.get('vooter_id') and not self.cleaned_data.get('driving_license') and not self.cleaned_data.get('others'):
				raise forms.ValidationError(u'Please Insert PAN Card or others Documens.')
		# except:
			# pass


		return self.cleaned_data.get('pan_card_file')


	def clean_proff_identity_code(self):
		if self.cleaned_data.get('proff_identity') and not self.cleaned_data.get('proff_identity_code'):
			raise forms.ValidationError(u'This Field Required.')
		return self.cleaned_data.get('proff_identity_code')


	def clean_proff_identity_file(self):
		get_file = self.cleaned_data.get('proff_identity_file')
		
		if self.cleaned_data.get('proff_identity') and not get_file:
			raise forms.ValidationError(u'This Field Required.')

		try:
			if get_file.content_type.split('/')[1] not in ['jpg', 'jpeg', 'png', 'pdf']:
				raise forms.ValidationError(u'Please Upload Valid File.')
		except:
			pass
		
		return get_file


	def clean_address_submitted_for_residece_file(self):
		get_file = self.cleaned_data.get('address_submitted_for_residece_file')

		try:
			if get_file.content_type.split('/')[1] not in ['jpg', 'jpeg', 'png', 'pdf']:
				raise forms.ValidationError(u'Please Upload Valid File.')
		except:
			pass
		
		return get_file


	def clean_proof_of_address_non_residence_file(self):
		if self.cleaned_data.get('proof_of_address_non_residence') and not self.cleaned_data.get('proof_of_address_non_residence_file'):
			raise forms.ValidationError(u'Please Insert Your Documens File.')

		if self.cleaned_data.get('proof_of_address_non_residence_file') and self.cleaned_data.get('proof_of_address_non_residence_file').content_type.split('/')[1] not in ['jpg', 'png', 'pdf', 'jpeg']:
			raise forms.ValidationError(u'Please Upload Valid File.')

		return self.cleaned_data.get('proof_of_address_non_residence_file')


	def clean_signature(self):
		try:
			if self.cleaned_data.get('signature') and self.cleaned_data.get('signature').content_type.split('/')[1] not in ['jpg', 'jpeg']:
				raise forms.ValidationError(u'Please Upload Valid File.')
		except:
			pass
		return self.cleaned_data.get('signature')


	def clean_residence_pasport(self):
		get_residence_status = self.cleaned_data.get('residence_status')
		get_residence_passport = self.cleaned_data['residence_pasport']
		if get_residence_status == '3' or get_residence_status == '2' and not get_residence_passport:
			raise forms.ValidationError(u'Please Insert Your Passport or others Documens.')

		elif get_residence_passport and get_residence_passport.content_type.split('/')[1] not in ['jpg', 'jpeg', 'png', 'pdf']:
			raise forms.ValidationError(u'Please Upload Valid File.')

		else:
			pass

		return get_residence_passport


	def clean_permanent_address(self):
		if self.cleaned_data.get('is_permanent_address') == '2' and self.cleaned_data.get('permanent_address') == '':
			raise forms.ValidationError(u'Please Insert Permanent Address.')

		return self.cleaned_data.get('permanent_address')


	# def clean(self):
	# 	cleaned_data = super(KYCForm, self).clean()

	# 	if not self.cleaned_data.get('pan_card') and not self.cleaned_data.get('addhar_number') and not self.cleaned_data.get('passport') and not self.cleaned_data.get('vooter_id') and not self.cleaned_data.get('driving_license') and not self.cleaned_data.get('others'):
	# 		raise forms.ValidationError(u'Please Insert PAN Card or others Documens.')



		return cleaned_data


	def save(self, commit=True):
		obj = super(KYCForm, self).save(commit=False)

		#str residence address
		# get_residence_address = self.cleaned_data['residence_address']

		#str_contact_detail
		get_tel = self.cleaned_data['contact_details_tel']
		get_mobile = self.cleaned_data['contact_details_mobile']
		# get_fax = self.cleaned_data['contact_details_fax']
		get_email = self.cleaned_data['contact_details_email']
		str_contact_detail = get_tel + ', ' + get_mobile + ', ' + get_email

		# #str_permanent_address
		get_permanent_address = self.cleaned_data['permanent_address']
		get_city1 = self.cleaned_data['city1']
		get_pin_code1 = self.cleaned_data['pin_code1']
		get_state1 = self.cleaned_data['state1']
		get_nationality1 = self.cleaned_data['country1']
		str_permanent_address = get_permanent_address + '||' + get_city1 + '||' + get_pin_code1 + '||' + get_state1 + '||' + get_nationality1


		obj.user = self.user
		# obj.residence_address = str_residence
		obj.contact_details = str_contact_detail
		obj.permanent_address = str_permanent_address
		obj.status = False
		if commit:
			obj.save()
		return obj



class CompanySettingForm(forms.ModelForm):
	class Meta:
		model = CompanySettings
		exclude = ('company', )
