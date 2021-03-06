from datetime import datetime

from django.test import TestCase
from django_dynamic_fixture import G, N
from entity.models import EntityRelationship

from entity_history import EntityRelationshipActivationEvent


class EntityRelationshipActivationTriggerTests(TestCase):
    """
    Tests that entity activation events are properly created when entities
    are activated and deactivated. This is accomplished by a postgres database
    trigger that is installed in a data migration.
    """
    def test_bulk_create(self):
        ers = [N(EntityRelationship) for i in range(3)]
        t1 = datetime.utcnow()
        EntityRelationship.objects.bulk_create(ers)
        t2 = datetime.utcnow()

        events = list(EntityRelationshipActivationEvent.objects.all())
        self.assertTrue(len(events), 3)
        for i in range(3):
            self.assertTrue(events[i].was_activated)
            self.assertTrue(t1 <= events[i].time <= t2)

    def test_bulk_create_delete(self):
        ers = [N(EntityRelationship) for i in range(3)]
        t1 = datetime.utcnow()
        EntityRelationship.objects.bulk_create(ers)
        t2 = datetime.utcnow()
        EntityRelationship.objects.all().delete()
        t3 = datetime.utcnow()

        events = list(EntityRelationshipActivationEvent.objects.all())
        self.assertTrue(len(events), 3)
        for i in range(3):
            self.assertTrue(events[i].was_activated)
            self.assertTrue(t1 <= events[i].time <= t2)
        for i in range(3, 6):
            self.assertFalse(events[i].was_activated)
            self.assertTrue(t2 <= events[i].time <= t3)

    def test_entity_relationship_creation(self):
        t1 = datetime.utcnow()
        er = G(EntityRelationship)
        t2 = datetime.utcnow()

        event = EntityRelationshipActivationEvent.objects.get()
        self.assertTrue(event.was_activated)
        self.assertEquals(event.sub_entity, er.sub_entity)
        self.assertEquals(event.super_entity, er.super_entity)
        self.assertTrue(t1 <= event.time <= t2)

    def test_entity_relationship_creation_deletion(self):
        t1 = datetime.utcnow()
        er = G(EntityRelationship)
        sub_entity = er.sub_entity
        super_entity = er.super_entity
        t2 = datetime.utcnow()
        er.delete()
        t3 = datetime.utcnow()

        events = list(EntityRelationshipActivationEvent.objects.order_by('time', 'id'))

        self.assertTrue(events[0].was_activated)
        self.assertEquals(events[0].sub_entity, sub_entity)
        self.assertEquals(events[0].super_entity, super_entity)
        self.assertTrue(t1 <= events[0].time <= t2)

        self.assertFalse(events[1].was_activated)
        self.assertEquals(events[1].sub_entity, sub_entity)
        self.assertEquals(events[1].super_entity, super_entity)
        self.assertTrue(t2 <= events[1].time <= t3)

    def test_entity_relationship_creation_deletion_creation_save(self):
        t1 = datetime.utcnow()
        er = G(EntityRelationship)
        sub_entity1 = er.sub_entity
        super_entity1 = er.super_entity
        t2 = datetime.utcnow()
        er.delete()
        t3 = datetime.utcnow()
        er = G(EntityRelationship)
        sub_entity2 = er.sub_entity
        super_entity2 = er.super_entity
        er.save()
        t4 = datetime.utcnow()

        events = list(EntityRelationshipActivationEvent.objects.order_by('time', 'id'))

        self.assertTrue(events[0].was_activated)
        self.assertEquals(events[0].sub_entity, sub_entity1)
        self.assertEquals(events[0].super_entity, super_entity1)
        self.assertTrue(t1 <= events[0].time <= t2)

        self.assertFalse(events[1].was_activated)
        self.assertEquals(events[1].sub_entity, sub_entity1)
        self.assertEquals(events[1].super_entity, super_entity1)
        self.assertTrue(t2 <= events[1].time <= t3)

        self.assertTrue(events[2].was_activated)
        self.assertEquals(events[2].sub_entity, sub_entity2)
        self.assertEquals(events[2].super_entity, super_entity2)
        self.assertTrue(t3 <= events[2].time <= t4)
