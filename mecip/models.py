from django.db import models
from django.utils import timezone


class Campus(models.Model):
    campus_name = models.CharField(max_length=254)
    city = models.CharField(max_length=50)
    street = models.CharField(max_length=50)
    neighborhood = models.CharField(max_length=50)
    number = models.CharField(max_length=50)
    contact_number =models.CharField(max_length=50)
    email_campus = models.EmailField(max_length=254)
    created_date = models.DateTimeField(default=timezone.now)

    def __str__(self) -> str:
        return f'{self.campus_name} {self.city}'
    
class Categorie_Course(models.Model):
    categorie = models.CharField(max_length=250)

    def __str__(self) -> str:
        return f'{self.categorie}'


class Type_Course(models.Model):
    type_name_course = models.CharField(max_length=250)
    duration = models.CharField(max_length=2)
    type_categorie =  models.ForeignKey(Categorie_Course, on_delete=models.CASCADE)   

    def __str__(self) -> str:
        return f'{self.type_name_course}'
    

class Curso(models.Model):
    type_course = models.ForeignKey(Type_Course, on_delete=models.CASCADE, related_name='nome_curso')
    description = models.TextField()
    created_date = models.DateTimeField(default=timezone.now)
    campus = models.ForeignKey(Campus, related_name='cursos', on_delete=models.CASCADE, default=1)

    class Meta:
        unique_together = ('type_course', 'campus')

    def __str__(self) -> str:
        return f'{self.type_course.type_name_course}'   
   
    
class Relatorio(models.Model):
    course = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name='relatorios')
    campus = models.ForeignKey(Campus, on_delete=models.CASCADE)
    created_date = models.DateTimeField(default=timezone.now)
    assessment = models.TextField()

    class Meta:
        unique_together = ('course', 'campus')

    def __str__(self) -> str:
        return f'{self.course} {self.campus}'
    

 




    
