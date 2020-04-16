import datetime
import logging

from dateutil import parser
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.utils import timezone
from django.utils.timezone import make_aware

from babylog.models import Event


def get_latest_event(baby_name, event_type):
    event_list = Event.objects.filter(baby_name=baby_name).filter(event_type=event_type).order_by('-dt')
    latest_event = event_list[0] if event_list else None
    return latest_event


def get_poop_type(poop_event):
    if not poop_event:
        return 'PoopBW'
    time_from_poop = poop_event.dt + datetime.timedelta(hours=6)
    return 'PoopBW' if time_from_poop < timezone.now() else 'PoopColor'


def vitamin_today(baby_name):
    today = timezone.now()
    midnight_today = datetime.datetime(today.year, today.month, today.day, tzinfo=today.tzinfo)
    if Event.objects.filter(baby_name=baby_name).filter(event_subtype='vitamin').filter(dt__gte=midnight_today):
        return 'got vitamin', 'MedicineColor'
    else:
        return 'no vitamin', 'MedicineBW'


def latest_medicine(baby_name):
    date_from = timezone.now() - datetime.timedelta(days=1)
    med_list = Event.objects.filter(baby_name=baby_name).filter(event_type='medicine').filter(dt__gte=date_from).exclude(event_subtype='vitamin').order_by('-dt')
    return med_list[0] if med_list else ' '


def get_bottle_text(baby_name):
    e = get_latest_event(baby_name, 'feed')
    if not e:
        return None, '', ''
    dt = e.dt
    date_from = dt - datetime.timedelta(hours=1)
    last_feeds = Event.objects.filter(baby_name=baby_name).filter(event_type='feed').filter(dt__gte=date_from).order_by('-dt')
    subtype = ''
    value = ''
    for e in last_feeds:
        subtype += e.event_subtype + ' + '
        if e.event_subtype == 'breastfeed':
            if e.value == 1:
                value += u"קצרה"+' + '
            if e.value == 2:
                value += u"רגילה" + ' + '
        else:
            value += str(e.value) + ' +  '

    subtype = subtype[:-3]
    value = value[:-3]
    subtype = subtype.replace('bottle', u"סימילאק").\
        replace('breastfeed', u"הנקה").\
        replace('moms_milk', u"חלב אם").\
        replace('veg', u"ירקות").\
        replace('fruit', u"פירות")
    return dt, subtype, value


def collect_stats(baby_name, start_date, end_date):
    stats = {'total_feeds': 0, 'measurable_feeds': 0, 'food_amount': 0, 'total_poop': 0, 'average_meal': 0,
             'average_feeds_per_day': 0}
    last_feed_time = timezone.now()+datetime.timedelta(hours=5)
    for event in Event.objects.filter(baby_name=baby_name).filter(dt__gte=start_date).filter(dt__lte=end_date).order_by('-dt'):
        if event.event_type == 'feed':
            if not event.event_subtype == 'breastfeed':
                stats['food_amount'] += event.value
            if event.dt < last_feed_time-datetime.timedelta(hours=1):
                # combine feeds within one hour
                last_feed_time = event.dt
                stats['total_feeds'] += 1
                if not event.event_subtype == 'breastfeed':
                    stats['measurable_feeds'] += 1
        elif event.event_subtype == 'poop':
            stats['total_poop'] += 1
    try:
        stats['average_meal'] = stats['food_amount']/stats['measurable_feeds']
        stats['average_feeds_per_day'] = "{0:.1f}".format(float(stats['total_feeds'])/(end_date-start_date).days)
    except Exception:
        pass
    return stats


def save_entry(baby_name, event_type, event_subtype, value, dt):
    same_event = Event.objects.filter(baby_name=baby_name, event_type=event_type, event_subtype=event_subtype, value=value, dt=dt)
    if not same_event:
        new_entry = Event(baby_name=baby_name, event_type=event_type, event_subtype=event_subtype, value=value, dt=dt)
        new_entry.save()
    else:
        logging.warning(f"Same event exists in the db. Not adding a duplicate {same_event}")

    return HttpResponseRedirect("/babylog/")


class BabyConsts(object):
    b1_name = 'Omri'
    b2_name = 'Shaked'
    b1_name_hebrew = 'עומרי'
    b2_name_hebrew = 'שקד'
    b1_background_color = 'DarkCyan'
    b2_background_color = 'MediumPurple'


def index(request):
    b1_name = BabyConsts.b1_name
    b2_name = BabyConsts.b2_name
    b1_name_hebrew = BabyConsts.b1_name_hebrew
    b2_name_hebrew = BabyConsts.b2_name_hebrew
    b1_background_color = BabyConsts.b1_background_color
    b2_background_color = BabyConsts.b2_background_color
    p1 = get_latest_event(b1_name, 'poop')
    p2 = get_latest_event(b2_name, 'poop')
    poop1_type = get_poop_type(p1)
    poop2_type = get_poop_type(p2)
    b1_dt, b1_subtype, b1_value = get_bottle_text(b1_name)
    b2_dt, b2_subtype, b2_value = get_bottle_text(b2_name)
    b1_v, medicine1_type = vitamin_today(b1_name)
    b2_v, medicine2_type = vitamin_today(b2_name)
    b1_m = latest_medicine(b1_name)
    b2_m = latest_medicine(b2_name)
    return render(request, 'babylog/front_page.html', locals())


def feed(request, baby_name):
    min_feed_amount = 10
    max_feed_amount = 200
    feed_jump_amount = 5
    default_feed_amount = 80
    amount = [i for i in range(min_feed_amount, max_feed_amount, feed_jump_amount)]
    background = BabyConsts.b1_background_color if baby_name == BabyConsts.b1_name else BabyConsts.b2_background_color
    return render(request, 'babylog/feed.html', locals())


def history(request, baby_name):
    today = timezone.now()
    midnight_today = datetime.datetime(today.year, today.month, today.day, tzinfo=today.tzinfo)
    stats_d = collect_stats(baby_name, midnight_today-datetime.timedelta(days=1), midnight_today)
    stats_w = collect_stats(baby_name, midnight_today-datetime.timedelta(days=7), midnight_today)
    stats_m = collect_stats(baby_name, midnight_today-datetime.timedelta(days=30), midnight_today)
    event_list = Event.objects.filter(baby_name=baby_name).order_by('-dt')
    return render(request, 'babylog/history.html', locals())


def poop(_, baby_name):
    return save_entry(baby_name=baby_name, event_type='poop', event_subtype='poop', value='1',
                      dt=timezone.now())


def medicine(_, baby_name):
    return save_entry(baby_name=baby_name, event_type='medicine', event_subtype='vitamin', value='1',
                      dt=timezone.now())
    # TODO To be used when there is more than one vitamin
    # background = BabyConsts.b1_background_color if baby_name == BabyConsts.b1_name else BabyConsts.b2_background_color
    # return render(request, 'babylog/medicine.html', locals())


def edit(request, db_id):
    return render(request, 'babylog/edit.html', locals())


def action(request, baby_name):
    return save_entry(baby_name=baby_name, event_type=request.POST['type'], event_subtype=request.POST['subtype'], value=request.POST['value'],
                      dt=make_aware(parser.parse(request.POST['date'])))


def delete(_, db_id):
    instance = Event.objects.get(id=db_id)
    instance.delete()
    return HttpResponseRedirect("/babylog/")
