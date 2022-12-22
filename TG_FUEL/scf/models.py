from django.db import models

# Create your models here.
from django.db import models

# Create your models here.

class mytable(models.Model):
    id = models.IntegerField(primary_key=True)
    flight = models.IntegerField()
    total_no = models.IntegerField()
    meandiff = models.DecimalField(max_digits=6, decimal_places=2)
    medianramp = models.DecimalField(max_digits=8, decimal_places=1)
    sddiff = models.DecimalField(max_digits=5, decimal_places=2)
    normality = models.CharField(max_length=6)
    scf90 = models.DecimalField(max_digits=5, decimal_places=2)
    scf95 = models.DecimalField(max_digits=5, decimal_places=2)
    scf99 = models.DecimalField(max_digits=5, decimal_places=2)
    
    

class FilesAdmin(models.Model):
    adminupload=models.FileField(upload_to='media')
    title=models.CharField(max_length=50)

    def __str__(self):
        return self.title
