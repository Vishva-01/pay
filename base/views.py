from django.shortcuts import render

# Create your views here.
import json
from django.forms import ValidationError
from django.shortcuts import render
from django.views import View
from grpc import Status
import razorpay
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


def get_razorpay_client():
    """Returns the razorpay client."""
    return razorpay.Client(
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_SECRET_KEY)
    )

def is_razorpay_payment_order_successful(order_id):
    order_response = get_razorpay_client().order.fetch(order_id=order_id)
    return order_response.get("status") in ["paid"]

def create_razorpay_payment_order(amount, currency, receipt):
    return get_razorpay_client().order.create(
        data={
            "amount": int(int(amount) * 100),  # amount in paise
            "currency": currency,
            "receipt": receipt,
        }
    )

class CreateOrderView(View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            amount = data.get("amount")
            currency = data.get("currency", "INR")
            receipt = data.get("receipt")
            
            order = create_razorpay_payment_order(amount, currency, receipt)
            return JsonResponse(order)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=Status.HTTP_400_BAD_REQUEST)

class VerifyPaymentView(View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            order_id = data.get("order_id")
            
            if is_razorpay_payment_order_successful(order_id):
                return JsonResponse({"status": "success"})
            else:
                raise ValidationError("Payment verification failed")
        except ValidationError as e:
            return JsonResponse({"error": str(e)}, status=Status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=Status.HTTP_500_INTERNAL_SERVER_ERROR)

def payment_form(request):
    return render(request, 'index.html', {
        'RAZORPAY_KEY_ID': settings.RAZORPAY_KEY_ID
    })
