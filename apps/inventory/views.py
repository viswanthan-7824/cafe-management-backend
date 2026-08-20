from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from apps.accounts.permissions import IsCashierOrAdminRole
from .models import Supplier, SupplierProduct, InventoryTransaction
from .serializers import SupplierSerializer, SupplierProductSerializer, InventoryTransactionSerializer
from .services import record_inventory_transaction

class SupplierListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsCashierOrAdminRole]
    queryset = Supplier.objects.all().order_by('name')
    serializer_class = SupplierSerializer

class SupplierDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsCashierOrAdminRole]
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer

class InventoryTransactionListCreateView(APIView):
    permission_classes = [IsCashierOrAdminRole]

    def get(self, request):
        trx_list = InventoryTransaction.objects.all().order_by('-timestamp')[:100]
        serializer = InventoryTransactionSerializer(trx_list, many=True)
        return Response(serializer.data)

    def post(self, request):
        product_id = request.data.get('product')
        transaction_type = request.data.get('transaction_type')
        quantity = int(request.data.get('quantity', 0))
        reference_id = request.data.get('reference_id', '')
        notes = request.data.get('notes', '')

        try:
            trx = record_inventory_transaction(
                product_id=product_id,
                transaction_type=transaction_type,
                quantity=quantity,
                reference_id=reference_id,
                notes=notes,
                user=request.user
            )
            return Response(InventoryTransactionSerializer(trx).data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
