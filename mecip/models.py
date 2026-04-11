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
    

class Course(models.Model):
    type_course = models.ForeignKey(Type_Course, on_delete=models.CASCADE, related_name='nome_curso')
    description = models.TextField()
    created_date = models.DateTimeField(default=timezone.now)
    campus = models.ForeignKey(Campus, related_name='cursos', on_delete=models.CASCADE, default=1)

    class Meta:
        unique_together = ('type_course', 'campus')

    def __str__(self) -> str:
        return f'{self.type_course.type_name_course}'   
   
    
class Questionnaire(models.Model):
    name = models.CharField(max_length=250)
    description = models.TextField(blank=True)
    campus = models.ForeignKey(Campus, on_delete=models.CASCADE, null=True, blank=True)
    created_date = models.DateTimeField(default=timezone.now)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self) -> str:
        return self.name


class Question(models.Model):
    QUESTION_TYPES = [
        ('text', 'Texto'),
        ('textarea', 'Texto longo'),
        ('boolean', 'Sim/Não'),
        ('choice', 'Múltipla escolha'),
    ]

    questionnaire = models.ForeignKey(Questionnaire, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    field_type = models.CharField(max_length=25, choices=QUESTION_TYPES, default='text')
    required = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    choices = models.TextField(blank=True, help_text='Separe opções com vírgula se for múltipla escolha (choice)')

    class Meta:
        ordering = ['questionnaire', 'order']

    def __str__(self) -> str:
        return f'{self.order} - {self.text[:50]}'


class ReportQuestionAnswer(models.Model):
    report = models.ForeignKey('Report', on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    answer = models.TextField(blank=True, null=True)
    created_date = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('report', 'question')

    def __str__(self) -> str:
        return f'{self.report} - {self.question.text[:40]}'


class Report(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='relatorios')
    campus = models.ForeignKey(Campus, on_delete=models.CASCADE)
    questionnaire = models.ForeignKey(Questionnaire, on_delete=models.SET_NULL, null=True, blank=True, related_name='reports')
    created_date = models.DateTimeField(default=timezone.now)
    assessment = models.TextField()
    assigned_team = models.ForeignKey('Team', on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_reports')
    assigned_user = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_reports')
    due_date = models.DateField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    
    STATUS_CHOICES = [
        ('Pendente', 'Pendente'),
        ('Em andamento', 'Em andamento'),
        ('Bloqueado', 'Bloqueado'),
        ('Pendente ajuste', 'Pendente ajuste'),
        ('Pendente avaliação', 'Pendente avaliação'),
        ('Aprovado', 'Aprovado'),
        ('Reprovado', 'Reprovado'),
    ]
    
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Pendente')

    class Meta:
        unique_together = ('course', 'campus')

    def __str__(self) -> str:
        return f'{self.course} {self.campus}'
    
class Team(models.Model):
    team_name = models.CharField(max_length=250)
    created_date = models.DateTimeField(default=timezone.now)
    campus = models.ForeignKey(Campus, on_delete=models.CASCADE)
    users = models.ManyToManyField('auth.User', related_name='teams')



    def __str__(self) -> str:
        return f'{self.team_name}'


class ReportTeamHistory(models.Model):
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name='team_history')
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='assignments')
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-start_date']

    def __str__(self) -> str:
        return f'{self.report} -> {self.team} ({self.start_date.isoformat()})'
    

 




    
