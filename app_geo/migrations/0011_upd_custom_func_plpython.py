from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('app_geo', '0010_custom_func_plpython'),
    ]

    operations = [
        migrations.RunSQL(
            '''
            CREATE OR REPLACE FUNCTION rrule_list_occurences(
                frequency INTEGER, 
                by_month INTEGER[],
                by_monthday INTEGER[],
                by_weekday INTEGER[], 
                dt_start CHAR DEFAULT NULL,
                dt_end CHAR DEFAULT NULL
            ) 
                RETURNS TIMESTAMPTZ[] AS
            $$
            from dateutil.rrule import rrule
            from dateutil.parser import parse
            
            if frequency is None:
                return []

            kwargs = {}
            if by_weekday:
                kwargs['byweekday']=by_weekday 
            if by_monthday:
                kwargs['bymonthday']=by_monthday 
            if by_month:
                kwargs['bymonth']=by_month 

            if dt_start is not None and dt_end is not None:
                kwargs['dtstart']=parse(dt_start)
                kwargs['until']=parse(dt_end)
            elif dt_start is not None and dt_end is None:
                kwargs['dtstart']=parse(dt_start)
                kwargs['count']=10
            elif dt_start is None and dt_end is not None:
                kwargs['until']=parse(dt_end)
            else:
                kwargs['count']=10  

            occurences = rrule(freq=frequency, **kwargs)
            return list(occurences)

            $$
            LANGUAGE 'plpython3u' VOLATILE;
            '''
        ),

    ]
