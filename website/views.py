"""
Pages publiques : landing page et inscription d'une école.
"""
from django import forms
from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods
from django.utils import timezone as dj_timezone

from accounts.models import School, User
from accounts.utils import unique_username
from classes.models import Class
from students.models import Student
from teachers.models import Teacher

from .forms import SchoolRegistrationForm


def landing(request):
    """Page d'accueil publique de la plateforme (avec formulaire de contact)."""
    if request.method == 'POST':
        from .forms import ContactMessageForm
        form = ContactMessageForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('/?sent=1#contact')
    else:
        from .forms import ContactMessageForm
        form = ContactMessageForm()

    if request.user.is_authenticated:
        return redirect('dashboard')

    # Une installation mono-école existante doit aussi être comptée :
    # la table School ne recense que les établissements inscrits en ligne.
    nb_schools = School.objects.filter(is_active=True).count()
    if nb_schools == 0:
        from school_settings.models import SchoolSetting
        nb_schools = 1 if SchoolSetting.objects.exists() else 0

    # Informations de l'établissement (Paramètres → École) pour le pied de page
    from school_settings.models import SchoolSetting
    footer_school = (
        SchoolSetting.objects.exclude(school_name__isnull=True)
        .exclude(school_name='').first()
    )

    # Téléphones affichés (plusieurs numéros séparés par « / »), avec lien
    # tel: normalisé — les numéros locaux maliens reçoivent l'indicatif +223.
    contact_phones = []
    if footer_school and footer_school.phone:
        for raw in footer_school.phone.split('/'):
            display = raw.strip()
            if not display:
                continue
            digits = ''.join(c for c in display if c.isdigit() or c == '+')
            if not digits:
                continue
            if not digits.startswith('+'):
                digits = '+223' + digits.lstrip('0')
            contact_phones.append({'display': display, 'href': digits})

    # Formules d'abonnement annuelles (affichage type « Tarification »)
    from accounts.models import SubscriptionPlan
    pricing_plans = []
    for p in SubscriptionPlan.objects.filter(is_active=True).order_by('price'):
        price = int(p.price) if p.price else 0
        if p.duration_days == 15 and price == 0:
            duration_label = "15 jours d'essai gratuit"
            show_monthly = False
            cta = "Essayer gratuitement"
        elif p.duration_days == 365:
            duration_label = "pour 12 mois"
            show_monthly = True
            cta = "Choisir cette offre"
        else:
            duration_label = f"pour {p.duration_days} jours"
            show_monthly = price > 0
            cta = "Choisir cette offre"
        pricing_plans.append({
            'plan': p,
            'price_display': f"{price:,}".replace(',', ' '),
            'monthly_display': f"{price // 12:,}".replace(',', ' ') if price else '0',
            'duration_label': duration_label,
            'show_monthly': show_monthly,
            'cta': cta,
            'features': p.features.splitlines() if p.features else [],
            'highlighted': p.code == 'pro',
        })

    context = {
        'nb_schools': nb_schools,
        'nb_students': Student.objects.filter(is_active=True).count(),
        'nb_teachers': Teacher.objects.filter(is_active=True).count(),
        'nb_classes': Class.objects.count(),
        'footer_school': footer_school,
        'contact_phones': contact_phones,
        'form': form,
        'contact_sent': request.GET.get('sent') == '1',
        'pricing_plans': pricing_plans,
    }
    return render(request, 'website/landing.html', context)


from django.contrib.auth.decorators import login_required


@login_required
def subscription_page(request):
    """Page « Mon abonnement » : formule actuelle de l'école + formules disponibles."""
    from accounts.models import PlatformSetting, SubscriptionPayment, SubscriptionPlan
    from website import saspay

    school = getattr(request.user, 'school', None)
    current = school.subscription if school and school.subscription_id else None
    days_left = None
    expired = False
    if school and school.subscription_until:
        delta = (school.subscription_until - dj_timezone.localdate()).days
        days_left = max(delta, 0)
        expired = delta < 0

    plans_items = []
    for p in SubscriptionPlan.objects.filter(is_active=True).order_by('price'):
        price = int(p.price) if p.price else 0
        if p.duration_days == 15 and price == 0:
            duration_label = "15 jours"
        elif p.duration_days == 365:
            duration_label = "12 mois"
        else:
            duration_label = f"{p.duration_days} jours"
        plans_items.append({
            'plan': p,
            'price_display': f"{price:,}".replace(',', ' '),
            'duration_label': duration_label,
            'features': p.features.splitlines() if p.features else [],
            'is_current': current == p,
        })

    return render(request, 'website/subscription.html', {
        'school': school,
        'current': current,
        'days_left': days_left,
        'expired': expired,
        'plans_items': plans_items,
        'saspay_ready': saspay.is_configured(),
        'pending_payments': (
            SubscriptionPayment.objects.filter(
                school=school,
                status=SubscriptionPayment.STATUS_PENDING,
            ).select_related('plan')[:5] if school else []),
    })


@require_http_methods(['GET', 'POST'])
def register_school(request):
    """Inscription publique d'une école : école + compte administrateur."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    from accounts.models import PlatformSetting
    setting = PlatformSetting.load()
    if not setting.public_registration_enabled:
        messages.error(
            request,
            "Les inscriptions d'écoles sont actuellement fermées. "
            "Merci de contacter le support de la plateforme."
        )
        return redirect('login')

    form = SchoolRegistrationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        school = form.save(commit=False)
        school.email = school.email or form.cleaned_data['admin_email']
        school.save()

        admin = User.objects.create_user(
            email=form.cleaned_data['admin_email'],
            username=unique_username(form.cleaned_data['admin_email']),
            password=form.cleaned_data['admin_password'],
            first_name=form.cleaned_data['admin_first_name'],
            last_name=form.cleaned_data['admin_last_name'],
            role='ADMIN',
        )
        admin.school = school
        admin.is_staff = True
        admin.save()

        # Abonnement par défaut configuré côté plateforme
        # Période d'essai de 15 jours par défaut (toutes fonctionnalités)
        default_plan = setting.default_plan
        if default_plan is None:
            from accounts.models import SubscriptionPlan
            default_plan = SubscriptionPlan.objects.filter(
                code='essai', is_active=True).first()
        if default_plan:
            from datetime import timedelta
            from django.utils import timezone
            school.subscription = default_plan
            school.subscription_until = timezone.localdate() + timedelta(
                days=default_plan.duration_days)
            school.save(update_fields=['subscription', 'subscription_until'])

        # Paramètres de l'établissement dédiés à cette nouvelle école
        from school_settings.models import SchoolSetting
        SchoolSetting.objects.get_or_create(
            school=school,
            defaults={
                'school_name': school.name,
                'address': school.address, 'phone': school.phone,
                'email': school.email,
            },
        )

        auth_login(request, admin)
        messages.success(
            request,
            f"Bienvenue ! L'école « {school.name} » a été créée. "
            "Votre compte administrateur est prêt."
        )
        return redirect('dashboard')

    return render(request, 'website/register_school.html', {'form': form})
