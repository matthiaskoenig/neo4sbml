from django.db import models

# Create your models here.
from neo4django.db import models

class Person(models.NodeModel):
    name = models.StringProperty()
    age = models.IntegerProperty()

    friends = models.Relationship('self', rel_type='friends_with')

class OnlinePerson(Person):
    email = models.EmailProperty()
    homepage = models.URLProperty()

# Relationships are simple. Instead of ForeignKey, ManyToManyField, or OneToOneField,
# just use Relationship. In addition to the relationship target, you can specify
# a relationship type and direction, cardinality, and the name of the relationship
# on the target model:

class Pet(models.NodeModel):
    owner = models.Relationship(Person,
                                rel_type='owns',
                                single=True,
                                related_name='pets'
                               )