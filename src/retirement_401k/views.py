from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from decimal import Decimal
from shared.handle_get import *
from .models import Account401K, Transaction401K
from shared.utils import *
from goal.goal_helper import get_goal_id_name_mapping_for_user
from django.http import HttpResponseRedirect
from django.views.generic import DeleteView
from .helper import reconcile_401k, create_nav_file, remove_nav_file
# Create your views here.


def add_account(request):
    template_name = 'retirement_401k/account_create.html'
    if request.method == 'POST':
        print(request.POST)
        company = request.POST['company']
        start_date = get_date_or_none_from_string(request.POST['start_date'])
        end_date = get_date_or_none_from_string(request.POST['end_date'])
        user = request.POST['user']
        goal = request.POST['goal']
        notes = request.POST['notes']
        if goal != '':
            goal_id = Decimal(goal)
        else:
            goal_id = None
        account = Account401K.objects.create(
                company=company,
                start_date=start_date,
                end_date=end_date,
                user=user,
                goal=goal_id,
                notes=notes
            )
        create_nav_file(account.id)

    users = get_all_users()
    context = {'users':users}
    return render(request, template_name, context)

def update_account(request, id):
    template_name = 'retirement_401k/account_update.html'
    account = get_object_or_404(Account401K, id=id)
    if request.method == 'POST':
        print(request.POST)
        company = request.POST['company']
        start_date = get_date_or_none_from_string(request.POST['start_date'])
        end_date = get_date_or_none_from_string(request.POST['end_date'])
        #user = request.POST['user']
        goal = request.POST['goal']
        notes = request.POST['notes']
        if goal != '':
            goal_id = Decimal(goal)
        else:
            goal_id = None
        account.company = company
        account.start_date = start_date
        account.end_date = end_date
        account.notes = notes
        account.goal = goal_id
        account.save()
    else:
        acct = dict()
        acct['id'] = account.id
        acct['company'] = account.company
        acct['start_date'] = account.start_date.strftime("%Y-%m-%d")
        if account.end_date:
            acct['end_date'] = account.end_date.strftime("%Y-%m-%d")
        acct['notes'] = account.notes
        goals = get_goal_id_name_mapping_for_user(account.user)
        acct['goal'] = account.goal
        acct['goals'] = goals
        acct['user'] = account.user
        print(f'context {acct}')
        return render(request, template_name, acct)

    return HttpResponseRedirect(reverse('retirement_401k:account-list'))

def get_accounts(request):
    template_name = 'retirement_401k/account_list.html'
    accounts = Account401K.objects.all()
    context = dict()
    context['accounts'] = list()
    for account in accounts:
        acct = dict()
        acct['id'] = account.id
        acct['company'] = account.company
        acct['start_date'] = account.start_date
        acct['end_date'] = account.end_date
        acct['employee_contribution'] = account.employee_contribution
        acct['employer_contribution'] = account.employer_contribution
        acct['notes'] = account.notes
        acct['as_on_date'] = account.nav_date
        acct['latest_value'] = account.latest_value
        if account.goal:
            acct['goal'] = get_goal_name_from_id(account.goal)
        acct['user'] = get_user_name_from_id(account.user)
        acct['total'] = account.total
        acct['roi'] = account.roi
        context['accounts'].append(acct)
    return render(request, template_name, context)

def account_detail(request, id):
    template_name = 'retirement_401k/account_detail.html'
    account = get_object_or_404(Account401K, id=id)
    acct = dict()
    acct['id'] = account.id
    acct['company'] = account.company
    acct['start_date'] = account.start_date
    acct['end_date'] = account.end_date
    acct['employee_contribution'] = account.employee_contribution
    acct['employer_contribution'] = account.employer_contribution
    acct['total'] = account.total
    acct['notes'] = account.notes
    acct['as_on_date'] = account.nav_date
    acct['latest_value'] = account.latest_value
    if account.goal:
        acct['goal'] = get_goal_name_from_id(account.goal)
    acct['user'] = get_user_name_from_id(account.user)
    acct['roi'] = account.roi
    return render(request, template_name, acct)

def get_transactions(request, id):
    template_name = 'retirement_401k/transactions_list.html'
    account = Account401K.objects.get(id=id)
    context = dict()
    context['id'] = id
    context['company'] = account.company
    context['trans_list'] = list()
    for transaction in Transaction401K.objects.filter(account=account):
        trans = dict()
        trans['id'] = transaction.id
        trans['trans_date'] = transaction.trans_date
        trans['employee_contribution'] = transaction.employee_contribution
        trans['employer_contribution'] = transaction.employer_contribution
        trans['notes'] = transaction.notes
        trans['units'] = transaction.units
        context['trans_list'].append(trans)
    return render(request, template_name, context)

def add_transaction(request, id):
    template_name = 'retirement_401k/add_transaction.html'
    account = Account401K.objects.get(id=id)
    if request.method == 'POST':
        print(request.POST)
        trans_date = get_date_or_none_from_string(request.POST['trans_date'])
        employee_contribution = get_float_or_none_from_string(request.POST['employee_contribution'])
        employer_contribution = get_float_or_none_from_string(request.POST['employee_contribution'])
        notes = request.POST['notes']
        units = get_float_or_none_from_string(request.POST['units'])
        Transaction401K.objects.create(
            account=account,
            trans_date=trans_date,
            employee_contribution=employee_contribution,
            employer_contribution=employer_contribution,
            units=units,
            notes=notes
        )
        reconcile_401k()
    context = {'company':account.company, 'id':account.id, 'operation':'Add'}
    return render(request, template_name, context)

def edit_transaction(request, id):
    template_name = 'retirement_401k/add_transaction.html'
    transaction = Transaction401K.objects.get(id=id)
    if request.method == 'POST':
        print(request.POST)
        trans_date = get_date_or_none_from_string(request.POST['trans_date'])
        employee_contribution = get_float_or_none_from_string(request.POST['employee_contribution'])
        employer_contribution = get_float_or_none_from_string(request.POST['employee_contribution'])
        notes = request.POST['notes']
        units = get_float_or_none_from_string(request.POST['units'])
        transaction.trans_date=trans_date
        transaction.employee_contribution=employee_contribution
        transaction.employer_contribution=employer_contribution
        transaction.units = units
        transaction.notes=notes
        transaction.save()
        reconcile_401k()
        return HttpResponseRedirect(reverse('retirement_401k:transaction-list', args=(transaction.account.id,)))
    context = {'company':transaction.account.company, 'id':transaction.account.id}
    context['trans_date'] = transaction.trans_date.strftime("%Y-%m-%d")
    context['employee_contribution'] = transaction.employee_contribution
    context['employer_contribution'] = transaction.employer_contribution
    context['notes'] = transaction.notes
    context['units'] = transaction.units
    context['operation'] = 'Edit'
    return render(request, template_name, context)

class TransactionDeleteView(DeleteView):
    def get_object(self):
        id_ = self.kwargs.get("id")
        return get_object_or_404(Transaction401K, id=id_)

    def get_success_url(self):
        id_ = self.kwargs.get("id")
        trans = get_object_or_404(Transaction401K, id=id_)
        return reverse('retirement_401k:transaction-list', args=(trans.account.id,))
    
    def delete(self, request, *args, **kwargs):
        #response = super(TransactionDeleteView, self).delete(request, *args, **kwargs)
        #return response
        self.object = self.get_object()
        success_url = self.get_success_url()
        print(f'******success url {success_url}')
        self.object.delete()
        reconcile_401k()
        return HttpResponseRedirect(success_url)

    def get(self, *args, **kwargs):
        return self.post(*args, **kwargs)

class AccountDeleteView(DeleteView):
    def get_object(self):
        id_ = self.kwargs.get("id")
        return get_object_or_404(Account401K, id=id_)

    def get_success_url(self):
        return reverse('retirement_401k:account-list')

    def delete(self, request, *args, **kwargs):
        id_ = self.kwargs.get("id")
        remove_nav_file(id_)
        self.object = self.get_object()
        success_url = self.get_success_url()
        self.object.delete()
        return HttpResponseRedirect(success_url)
    
    def get(self, *args, **kwargs):
        return self.post(*args, **kwargs)