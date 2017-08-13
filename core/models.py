from django.db import models


class Baby(models.Model):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    birth_date = models.DateField(blank=False, null=False)

    objects = models.Manager()

    class Meta:
        default_permissions = ('view', 'add', 'change', 'delete')
        ordering = ['last_name', 'first_name']
        verbose_name_plural = 'Babies'

    def __str__(self):
        return '{} {}'.format(self.first_name, self.last_name)


class Sleep(models.Model):
    baby = models.ForeignKey('Baby', related_name='sleep')
    start = models.DateTimeField(blank=False, null=False)
    end = models.DateTimeField(blank=False, null=False)

    objects = models.Manager()

    class Meta:
        default_permissions = ('view', 'add', 'change', 'delete')
        ordering = ['-start']
        verbose_name_plural = 'Sleep'

    def __str__(self):
        return '{} slept from {} to {} on {}'.format(
            self.baby,
            self.start.time(),
            self.end.time(),
            self.end.date(),
        )
