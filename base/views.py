from django.shortcuts import render
from django.forms import ValidationError
from django.views import View
import json
import razorpay
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
import io


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
            return JsonResponse({"error": str(e)}, status=400)

class VerifyPaymentView(View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            order_id = data.get("order_id")

            if is_razorpay_payment_order_successful(order_id):
                return self.generate_pdf_receipt(order_id)
            else:
                raise ValidationError("Payment verification failed")
        except ValidationError as e:
            return JsonResponse({"error": str(e)}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    def generate_pdf_receipt(self, order_id):
        order_details = get_razorpay_client().order.fetch(order_id=order_id)

        template = get_template('receipt.html')
        html = template.render({'order': order_details})

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="receipt_{order_id}.pdf"'

        pisa_status = pisa.CreatePDF(
            io.BytesIO(html.encode("UTF-8")),
            dest=response
        )

        if pisa_status.err:
            return HttpResponse(f'We had some errors with code {pisa_status.err} <pre>{html}</pre>')
        return response

def payment_form(request):
    return render(request, 'index.html', {
        'RAZORPAY_KEY_ID': settings.RAZORPAY_KEY_ID
    })
