from django.test import TestCase
from planner.models import Material
from planner.serializers import MaterialSerializer

class MaterialModelSerializerTests(TestCase):
    def test_material_price_field_create_and_update(self):
        mat = Material.objects.create(name='Test Mat', category='test', unit='piece', price=12.34)
        self.assertEqual(mat.price, 12.34)
        mat.price = 56.78
        mat.save()
        self.assertEqual(Material.objects.get(id=mat.id).price, 56.78)

    def test_material_serializer_price_field(self):
        mat = Material.objects.create(name='Test Mat', category='test', unit='piece', price=9.99)
        data = MaterialSerializer(mat).data
        self.assertIn('price', data)
        self.assertEqual(float(data['price']), 9.99)
        # Test deserialization
        ser = MaterialSerializer(mat, data={'price': 15.55}, partial=True)
        self.assertTrue(ser.is_valid(), ser.errors)
        ser.save()
        mat.refresh_from_db()
        self.assertEqual(mat.price, 15.55)
