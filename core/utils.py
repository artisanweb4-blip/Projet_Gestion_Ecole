import csv
from django.http import HttpResponse

def export_queryset_to_csv(queryset, field_names, filename="export.csv"):
    """
    Exporte un queryset Django au format CSV pour les relevés de présence ou financières.
    """
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    response.write(u'\ufeff'.encode('utf8')) # BOM UTF-8 pour Excel

    writer = csv.writer(response)
    writer.writerow(field_names)

    for obj in queryset:
        row = []
        for field in field_names:
            val = getattr(obj, field, '')
            if callable(val):
                val = val()
            row.append(str(val))
        writer.writerow(row)

    return response
